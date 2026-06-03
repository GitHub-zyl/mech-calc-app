"""
轴设计计算模块
参考：GB/T 6403.3, 机械设计手册(成大先)第四卷第16篇
"""
import math


def calc_shaft_torsion(d=None, P=None, n=None, tau_allow=None, P_kW=None):
    """
    按扭转强度估算最小轴径
    d_min = (9550×P/(0.2×[τ]×n))^(1/3)
    或
    d_min = A × (P/n)^(1/3)
    其中 A = (9550/(0.2×[τ]))^(1/3) 为材料系数
    
    参数:
        d: 已有轴径mm（校核模式）
        P: 传递功率 kW
        P_kW: 功率别名
        n: 转速 rpm
        tau_allow: 许用扭转切应力 MPa
    """
    P_val = P or P_kW or 0
    if not P_val or not n:
        return {'error': '请提供功率 P(kW) 和转速 n(rpm)'}

    tau = tau_allow or 40  # 默认45钢调质
    
    # 计算最小轴径
    if tau > 0:
        d_min = (9550 * P_val / (0.2 * tau * n)) ** (1/3) if n > 0 else 0
        A_factor = (9550 / (0.2 * tau)) ** (1/3)
    else:
        d_min = 0
        A_factor = 0
    
    # 如果提供了已有轴径，进行校核
    result = {
        'power_kW': P_val,
        'speed_rpm': n,
        'allowable_tau_MPa': tau,
        'd_min_mm': round(d_min, 2),
        'A_factor': round(A_factor, 1),
        'formula': 'd_min = (9550P/(0.2[τ]n))^(1/3)',
        'reference': 'GB/T 6403.3 / 机械设计手册第16篇',
    }
    
    if d is not None and d_min > 0:
        safety = d / d_min
        result['given_d_mm'] = d
        result['safety_ratio'] = round(safety, 2)
        result['is_safe'] = safety >= 1.0
    
    return result


def calc_shaft_combined(d=None, M=None, T=None, alpha=1.0, sigma_allow=None):
    """
    弯扭合成强度校核（第三强度理论）
    sigma_ca = sqrt(M² + (αT)²) / W
    W = πd³/32 (实心轴)
    
    参数:
        d: 轴径 mm
        M: 弯矩 N·mm
        T: 扭矩 N·mm
        alpha: 折算系数（脉动循环=0.6, 对称循环=1.0, 静载荷=0.3）
        sigma_allow: 许用弯曲应力 MPa
    """
    if not d or M is None or T is None:
        return {'error': '请提供轴径 d(mm)、弯矩 M(N·mm) 和扭矩 T(N·mm)'}
    
    W = math.pi * d**3 / 32  # 抗弯截面系数 mm³
    M_ca = math.sqrt(M**2 + (alpha * T)**2)  # 当量弯矩
    sigma_ca = M_ca / W if W > 0 else 0
    
    result = {
        'shaft_diameter_mm': d,
        'bending_moment_N_mm': M,
        'torque_N_mm': T,
        'alpha': alpha,
        'section_modulus_mm3': round(W, 2),
        'equivalent_moment_N_mm': round(M_ca, 2),
        'sigma_ca_MPa': round(sigma_ca, 2),
        'formula': 'σ_ca = √(M²+(αT)²) / (πd³/32) [第三强度理论]',
        'reference': '机械设计手册(成大先)第16篇',
    }
    
    if sigma_allow is not None:
        n = sigma_allow / sigma_ca if sigma_ca > 0 else 0
        result['allowable_stress_MPa'] = sigma_allow
        result['safety_factor'] = round(n, 2)
        result['is_safe'] = n >= 1.0
    
    return result


def calc_shaft_fatigue(d=None, M=None, T=None, sigma_b=None,
                       K_sigma=1.0, K_tau=1.0, beta=1.0,
                       epsilon_sigma=1.0, epsilon_tau=1.0,
                       psi_sigma=0.2, psi_tau=0.1):
    """
    疲劳强度安全系数校核（弯扭联合）
    
    弯曲安全系数: S_σ = σ_{-1} / (K_σ·σ_a/(β·ε_σ) + ψ_σ·σ_m)
    扭转安全系数: S_τ = τ_{-1} / (K_τ·τ_a/(β·ε_τ) + ψ_τ·τ_m)
    综合安全系数: S = S_σ·S_τ / √(S_σ²+S_τ²)
    
    参数:
        d: 轴径 mm
        M: 弯矩 N·mm（对称循环 σ_m=0, σ_a=M/W）
        T: 扭矩 N·mm（脉动循环 τ_a=τ_m=T/(2Wt)）
        sigma_b: 材料抗拉强度 MPa
        K_sigma: 弯曲有效应力集中系数
        K_tau: 扭转有效应力集中系数
        beta: 表面质量系数
        epsilon_sigma: 弯曲尺寸系数
        epsilon_tau: 扭转尺寸系数
        psi_sigma: 弯曲平均应力折算系数
        psi_tau: 扭转平均应力折算系数
    """
    if not d or M is None or T is None or not sigma_b:
        return {'error': '请提供轴径 d(mm)、弯矩 M(N·mm)、扭矩 T(N·mm) 和抗拉强度 σ_b(MPa)'}

    # 疲劳极限估算（碳钢和合金钢）
    sigma_minus1 = 0.44 * sigma_b  # 弯曲疲劳极限
    tau_minus1 = 0.25 * sigma_b     # 扭转疲劳极限

    W = math.pi * d**3 / 32
    Wt = math.pi * d**3 / 16

    # 弯曲应力（对称循环）
    sigma_a = M / W if W > 0 else 0
    sigma_m = 0  # 对称循环

    # 扭转应力（脉动循环）
    tau_a = T / (2 * Wt) if Wt > 0 else 0
    tau_m = tau_a

    # 安全系数
    denom_sigma = (K_sigma * sigma_a) / (beta * epsilon_sigma) + psi_sigma * sigma_m
    S_sigma = sigma_minus1 / denom_sigma if denom_sigma > 0 else float('inf')

    denom_tau = (K_tau * tau_a) / (beta * epsilon_tau) + psi_tau * tau_m
    S_tau = tau_minus1 / denom_tau if denom_tau > 0 else float('inf')

    S = S_sigma * S_tau / math.sqrt(S_sigma**2 + S_tau**2) if S_sigma > 0 and S_tau > 0 else 0

    return {
        'shaft_diameter_mm': d,
        'bending_moment_N_mm': M,
        'torque_N_mm': T,
        'tensile_strength_sigma_b_MPa': sigma_b,
        'sigma_minus1_MPa': round(sigma_minus1, 2),
        'tau_minus1_MPa': round(tau_minus1, 2),
        'sigma_a_MPa': round(sigma_a, 2),
        'tau_a_MPa': round(tau_a, 2),
        'S_sigma': round(S_sigma, 2),
        'S_tau': round(S_tau, 2),
        'S_combined': round(S, 2),
        'is_safe': S >= 1.5,
        'formula': 'S = S_σ·S_τ / √(S_σ²+S_τ²)',
        'reference': '机械设计手册(成大先)第16篇 §3.5',
    }


def calc_critical_speed(d=None, L=None, m_shaft=None, m_disk=None,
                        E=206000, n_max=None):
    """
    临界转速计算（Rayleigh法）
    简支轴，单盘居中
    ω_cr = √(g/δ)
    δ = (F·L³)/(48EI) + 5qL⁴/(384EI)
    
    参数:
        d: 轴径 mm
        L: 轴长 mm
        m_shaft: 轴质量 kg
        m_disk: 圆盘质量 kg
        E: 弹性模量 MPa（默认206000，钢）
        n_max: 最高工作转速 rpm（校核用）
    """
    if not d or not L:
        return {'error': '请提供轴径 d(mm) 和轴长 L(mm)'}

    I = math.pi * d**4 / 64  # 截面惯性矩 mm⁴
    g = 9810  # mm/s² (9.81 m/s²)
    E_N_mm2 = E  # MPa = N/mm²

    # 挠度
    if m_disk:
        F = m_disk * 9.81  # N
        delta_disk = F * L**3 / (48 * E_N_mm2 * I) if I > 0 and E_N_mm2 > 0 else 0
    else:
        delta_disk = 0

    if m_shaft:
        q = m_shaft * 9.81 / L  # N/mm
        delta_shaft = 5 * q * L**4 / (384 * E_N_mm2 * I) if I > 0 and E_N_mm2 > 0 else 0
    else:
        delta_shaft = 0

    delta_total = delta_disk + delta_shaft
    omega_cr = math.sqrt(g / delta_total) if delta_total > 0 else 0
    n_cr = omega_cr * 60 / (2 * math.pi)

    result = {
        'shaft_diameter_mm': d,
        'shaft_length_mm': L,
        'elastic_modulus_MPa': E,
        'inertia_mm4': round(I, 2),
        'deflection_disk_mm': round(delta_disk, 4),
        'deflection_shaft_mm': round(delta_shaft, 4),
        'deflection_total_mm': round(delta_total, 4),
        'critical_omega_rad_s': round(omega_cr, 2),
        'critical_speed_cr_rpm': round(n_cr, 2),
        'formula': 'ω_cr = √(g/δ) [Rayleigh法]',
        'reference': '机械设计手册(成大先)第16篇 §8',
    }

    if n_max is not None and n_cr > 0:
        margin = n_cr / n_max
        result['max_working_speed_rpm'] = n_max
        result['safety_margin'] = round(margin, 2)
        result['is_safe'] = margin >= 1.3
        result['note'] = '安全裕度≥1.3 推荐（刚性轴）, 或 n_cr/n_max ≤ 0.75（柔性轴）'

    return result
