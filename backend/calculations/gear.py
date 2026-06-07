"""
齿轮传动计算模块
参考：机械设计常用计算表 - 齿轮参数计算 / 齿轮齿条传动设计
"""
import math


def spur_gear_params(m, z, alpha_deg=20, ha_star=1.0, c_star=0.25, x=0):
    """
    标准/变位直齿圆柱齿轮基本参数计算
    
    参数:
        m: 模数 (mm)
        z: 齿数
        alpha_deg: 压力角 (度)
        ha_star: 齿顶高系数
        c_star: 顶隙系数
        x: 变位系数
    
    返回: dict
    """
    alpha = math.radians(alpha_deg)
    
    d = m * z                          # 分度圆直径
    db = d * math.cos(alpha)           # 基圆直径
    ha = m * (ha_star + x)             # 齿顶高
    hf = m * (ha_star + c_star - x)    # 齿根高
    h = ha + hf                         # 全齿高
    da = d + 2 * ha                     # 齿顶圆直径
    df = d - 2 * hf                     # 齿根圆直径
    p = math.pi * m                     # 齿距
    s = math.pi * m / 2 + 2 * x * m * math.tan(alpha)  # 齿厚
    e = math.pi * m / 2 - 2 * x * m * math.tan(alpha)  # 齿槽宽
    
    return {
        'module': m,
        'teeth': z,
        'pressure_angle_deg': alpha_deg,
        'pitch_diameter': round(d, 4),
        'base_circle_diameter': round(db, 4),
        'addendum': round(ha, 4),
        'dedendum': round(hf, 4),
        'whole_depth': round(h, 4),
        'tip_diameter': round(da, 4),
        'root_diameter': round(df, 4),
        'circular_pitch': round(p, 4),
        'tooth_thickness': round(s, 4),
        'space_width': round(e, 4),
        'modification_coefficient': x,
    }


def spur_gear_mesh(m, z1, z2, alpha_deg=20, ha_star=1.0, c_star=0.25, x1=0, x2=0):
    """
    直齿圆柱齿轮啮合计算
    
    返回: dict 包含两个齿轮参数和中心距
    """
    g1 = spur_gear_params(m, z1, alpha_deg, ha_star, c_star, x1)
    g2 = spur_gear_params(m, z2, alpha_deg, ha_star, c_star, x2)
    
    a = m * (z1 + z2) / 2                      # 标准中心距
    inv_alpha = math.tan(math.radians(alpha_deg)) - math.radians(alpha_deg)
    inv_alpha_w = 2 * (x1 + x2) * math.tan(math.radians(alpha_deg)) / (z1 + z2) + inv_alpha
    
    # 啮合角 (迭代求解)
    alpha_w = alpha_deg  # 初始值
    for _ in range(20):
        inv_alpha_w_calc = math.tan(math.radians(alpha_w)) - math.radians(alpha_w)
        if abs(inv_alpha_w_calc - inv_alpha_w) < 1e-10:
            break
        alpha_w = alpha_w - (inv_alpha_w_calc - inv_alpha_w) / (1 / math.cos(math.radians(alpha_w))**2 - 1)
    
    a_w = a * math.cos(math.radians(alpha_deg)) / math.cos(math.radians(alpha_w))  # 实际中心距
    
    return {
        'gear1': g1,
        'gear2': g2,
        'center_distance': round(a, 4),
        'actual_center_distance': round(a_w, 4),
        'working_pressure_angle_deg': round(alpha_w, 4),
        'transmission_ratio': round(z2 / z1, 4),
    }


def gear_motor_selection(power_kw, n1_rpm, ratio, efficiency=0.95):
    """
    齿轮传动电机选型计算
    
    参数:
        power_kw: 所需功率 (kW)
        n1_rpm: 输入转速 (rpm)
        ratio: 传动比
        efficiency: 传动效率
    """
    n2_rpm = n1_rpm / ratio
    T1 = 9550 * power_kw / n1_rpm          # 输入扭矩 N·m
    T2 = T1 * ratio * efficiency            # 输出扭矩 N·m
    
    return {
        'input_speed': n1_rpm,
        'output_speed': round(n2_rpm, 2),
        'input_torque': round(T1, 2),
        'output_torque': round(T2, 2),
        'ratio': ratio,
        'power_kw': power_kw,
        'efficiency': efficiency,
    }


def rack_and_pinion(m, z_pinion, force_n=None, speed_mps=None, alpha_deg=20):
    """
    齿轮齿条传动计算
    
    参数:
        m: 模数 (mm)
        z_pinion: 齿轮齿数
        force_n: 驱动力 (N)
        speed_mps: 移动速度 (m/s)
    """
    d = m * z_pinion
    # 每转移动距离
    travel_per_rev = math.pi * d  # mm
    
    result = {
        'module': m,
        'pinion_teeth': z_pinion,
        'pinion_pitch_diameter': round(d, 2),
        'travel_per_revolution_mm': round(travel_per_rev, 2),
    }
    
    if force_n:
        # 所需扭矩
        torque_nm = force_n * d / 2000  # N·m (d in mm)
        result['required_torque_nm'] = round(torque_nm, 2)
    
    if speed_mps:
        # 所需转速
        rpm = speed_mps * 1000 * 60 / (math.pi * d)
        result['required_speed_rpm'] = round(rpm, 2)
    
    if force_n and speed_mps:
        power_kw = force_n * speed_mps / 1000
        result['required_power_kw'] = round(power_kw, 3)
    
    return result


def gear_bending_strength(Ft_N, b_mm, m_mm, YF=2.5, YS=1.6, Yb=1.0, K=1.3):
    sigma_F = K * Ft_N * YF * YS * Yb / (b_mm * m_mm) if b_mm * m_mm > 0 else 0
    return {'bending_stress_mpa': round(sigma_F, 2)}


def gear_contact_strength(Ft_N, b_mm, d1_mm, u, K=1.3, ZE=189.8, ZH=2.5, Ze=0.87):
    import math
    sigma_H = ZE * ZH * Ze * math.sqrt(2 * K * Ft_N / (b_mm * d1_mm) * (u + 1) / u) if b_mm * d1_mm * u > 0 else 0
    return {'contact_stress_mpa': round(sigma_H, 2)}


def gear_force(torque_Nm, d_mm, alpha_deg=20, beta_deg=0):
    import math
    Ft = 2 * torque_Nm * 1000 / d_mm if d_mm > 0 else 0
    Fr = Ft * math.tan(math.radians(alpha_deg)) / math.cos(math.radians(beta_deg))
    Fa = Ft * math.tan(math.radians(beta_deg))
    return {'tangential_N': round(Ft, 1), 'radial_N': round(Fr, 1), 'axial_N': round(Fa, 1)}
