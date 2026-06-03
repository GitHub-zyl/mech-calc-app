"""
制动器与离合器计算模块
参考：机械设计手册(成大先)第16篇 §14, 第18篇 §10
"""
import math


def calc_disc_brake_torque(p=None, mu=None, D_o=None, D_i=None, n_faces=2):
    """
    盘式制动器制动力矩（均匀磨损假设）
    
    T = n × μ × p × π × (D_o³ - D_i³) / 12
    
    参数:
        p: 衬面比压 MPa
        mu: 摩擦系数
        D_o: 制动盘外径 mm
        D_i: 制动盘内径 mm
        n_faces: 摩擦面数（单盘=2, 多盘=n_faces）
    
    返回: 制动力矩 N·m
    """
    if not p or not mu or not D_o or not D_i:
        return {'error': '请提供 p(MPa)、μ、D_o(mm)、D_i(mm)'}

    if D_i >= D_o:
        return {'error': '外径必须大于内径'}

    # 均匀磨损假设: T = n·μ·p·π·(D_o³ - D_i³) / 12
    T_N_mm = n_faces * mu * p * math.pi * (D_o**3 - D_i**3) / 12
    T_N_m = T_N_mm / 1000

    # 有效摩擦半径
    R_eff = (D_o**3 - D_i**3) / (3 * (D_o**2 - D_i**2)) if D_o != D_i else D_o / 2

    return {
        'pressure_MPa': p,
        'friction_coeff_mu': mu,
        'disc_OD_mm': D_o,
        'disc_ID_mm': D_i,
        'num_faces': n_faces,
        'effective_radius_mm': round(R_eff, 2),
        'torque_N_mm': round(T_N_mm, 2),
        'torque_N_m': round(T_N_m, 3),
        'formula': 'T = n·μ·p·π·(D_o³-D_i³)/12 [均匀磨损]',
        'reference': '机械设计手册(成大先)第16篇 §14.2',
    }


def calc_band_brake_torque(F1=None, mu=None, theta_deg=None, r=None):
    """
    带式制动器制动力矩
    
    欧拉公式: F1/F2 = e^(μθ)
    制动力矩: T = (F1 - F2) × r = F1·r·(1 - e^(-μθ))
    
    参数:
        F1: 张紧端力 N
        mu: 摩擦系数
        theta_deg: 包角 deg
        r: 制动鼓半径 mm
    """
    if not F1 or not mu or not theta_deg or not r:
        return {'error': '请提供 F1(N)、μ、θ(deg) 和 r(mm)'}

    theta_rad = theta_deg * math.pi / 180
    ratio = math.exp(mu * theta_rad)
    F2 = F1 / ratio if ratio > 0 else 0
    T_N_mm = (F1 - F2) * r
    T_N_m = T_N_mm / 1000

    return {
        'tight_force_F1_N': F1,
        'friction_coeff_mu': mu,
        'wrap_angle_theta_deg': theta_deg,
        'wrap_angle_theta_rad': round(theta_rad, 4),
        'drum_radius_r_mm': r,
        'slack_force_F2_N': round(F2, 2),
        'F1_F2_ratio': round(ratio, 2),
        'torque_N_mm': round(T_N_mm, 2),
        'torque_N_m': round(T_N_m, 3),
        'is_self_locking': theta_rad * mu >= 3.0,
        'formula': 'T = F1·r·(1 - e^(-μθ)) [欧拉公式]',
        'reference': '机械设计手册(成大先)第16篇 §14.3',
    }


def calc_clutch_energy(W=None, J=None, omega1=None, omega2=None,
                        m_drum=None, c_specific=500):
    """
    离合器接合滑磨功与温升计算
    
    滑磨功: W_slip = ½·J·(ω1² - ω2²)  (主动件释放的能量)
    温升: ΔT = W_slip / (m·c)             (制动鼓/离合器的温升)
    
    参数:
        W: 滑磨功 J（如已知直接输入）
        J: 从动部分转动惯量 kg·m²
        omega1: 主动件初始角速度 rad/s
        omega2: 从动件初始角速度 rad/s
        m_drum: 制动鼓/离合器质量 kg
        c_specific: 材料比热 J/(kg·K)，钢≈500, 铸铁≈460
    
    返回: 滑磨功、温升
    """
    result = {}

    if W is not None:
        slip_energy = W
    elif J is not None and omega1 is not None:
        w2 = omega2 if omega2 is not None else 0
        slip_energy = 0.5 * J * (omega1**2 - w2**2)
        result['inertia_J_kgm2'] = J
        result['omega1_rad_s'] = omega1
        result['omega2_rad_s'] = w2
    else:
        return {'error': '请提供滑磨功 W(J) 或 (J, omega1[, omega2])'}

    result['slip_work_J'] = round(slip_energy, 2)
    result['slip_work_kJ'] = round(slip_energy / 1000, 3)

    if m_drum is not None and m_drum > 0:
        delta_T = slip_energy / (m_drum * c_specific)
        result['drum_mass_kg'] = m_drum
        result['specific_heat_J_kgK'] = c_specific
        result['temperature_rise_K'] = round(delta_T, 2)
        result['temperature_rise_acceptable'] = delta_T <= 150
        result['note'] = '一般允许温升 ≤150K (干式), ≤80K (湿式)'

    result['formula'] = 'W_slip = ½J(ω1²-ω2²), ΔT = W/(m·c)'
    result['reference'] = '机械设计手册(成大先)第16篇 §14.4'

    return result
