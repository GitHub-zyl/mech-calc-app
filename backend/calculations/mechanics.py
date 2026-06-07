"""
机械设计手册 — 运动学/动力学/转动惯量/振动/动量/能量 综合模块
"""
import math

# ============ 1. 运动学 (Kinematics) ============


def linear_motion(v0=0, a=0, t=0, s=None):
    """
    匀变速直线运动
    
    输入任意两个，计算其他参数
    v = v₀ + at
    s = v₀t + ½at²
    v² = v₀² + 2as
    """
    result = {'v0': v0, 'a': a, 't': t}
    
    if s is None and t > 0:
        s = v0 * t + 0.5 * a * t * t
        result['s'] = round(s, 4)
        result['v'] = round(v0 + a * t, 4)
    elif t > 0:
        result['s'] = s
        v = math.sqrt(v0*v0 + 2*a*s)
        result['v'] = round(v, 4) if not math.isnan(v) else 0
    else:
        result['s'] = 0
        result['v'] = v0
    
    result['formula_v'] = 'v = v₀ + at'
    result['formula_s'] = 's = v₀t + ½at²'
    return result


def rotational_motion(omega0=0, alpha=0, t=0):
    """
    匀角速转动
    ω = ω₀ + αt
    θ = ω₀t + ½αt²
    """
    omega = omega0 + alpha * t
    theta = omega0 * t + 0.5 * alpha * t * t
    n = omega * 60 / (2 * math.pi) if omega != 0 else 0  # rpm
    
    return {
        'omega0_rad_s': omega0, 'alpha_rad_s2': alpha, 't_s': t,
        'omega_rad_s': round(omega, 4),
        'theta_rad': round(theta, 4),
        'theta_rev': round(theta / (2*math.pi), 4),
        'speed_rpm': round(n, 2),
        'formula': 'ω = ω₀ + αt, θ = ω₀t + ½αt²',
    }


def centrifugal_force(mass_kg, radius_m, omega_rad_s=None, rpm=None, v_mps=None):
    """
    离心力 / 向心力  F = mω²r = mv²/r
    """
    if rpm is not None:
        omega_rad_s = rpm * 2 * math.pi / 60
    if v_mps is not None:
        omega_rad_s = v_mps / radius_m if radius_m > 0 else 0
    
    omega = omega_rad_s or 0
    F = mass_kg * omega * omega * radius_m if radius_m > 0 else 0
    a = omega * omega * radius_m  # 向心加速度
    
    v = omega * radius_m
    
    return {
        'mass_kg': mass_kg,
        'radius_m': radius_m,
        'omega_rad_s': round(omega, 4),
        'tangential_velocity_mps': round(v, 3),
        'centripetal_accel_m_s2': round(a, 3),
        'centrifugal_force_N': round(F, 2),
        'centrifugal_force_g': round(a / 9.81, 2) if a > 0 else 0,
        'formula': 'F = m·ω²·r',
    }


def momentum(mass_kg, velocity_mps):
    """动量 p = mv"""
    p = mass_kg * velocity_mps
    Ek = 0.5 * mass_kg * velocity_mps * velocity_mps
    return {
        'mass_kg': mass_kg,
        'velocity_mps': velocity_mps,
        'momentum_kgms': round(p, 3),
        'kinetic_energy_J': round(Ek, 3),
    }


def angular_momentum(I_kgm2, omega_rad_s):
    """角动量 L = Iω"""
    L = I_kgm2 * omega_rad_s
    Ek = 0.5 * I_kgm2 * omega_rad_s * omega_rad_s
    n = omega_rad_s * 60 / (2*math.pi)
    return {
        'inertia_kgm2': I_kgm2,
        'omega_rad_s': omega_rad_s,
        'speed_rpm': round(n, 2),
        'angular_momentum_kgm2s': round(L, 4),
        'rotational_energy_J': round(Ek, 4),
    }


def impulse(force_N, time_s, mass_kg=None):
    """冲量 Ft = mΔv"""
    I = force_N * time_s
    result = {'impulse_Ns': round(I, 3)}
    if mass_kg and mass_kg > 0:
        delta_v = I / mass_kg
        result['mass_kg'] = mass_kg
        result['velocity_change_mps'] = round(delta_v, 4)
        result['formula'] = 'Ft = m·Δv'
    return result


def work_energy(force_N=None, distance_m=None, torque_Nm=None, angle_rad=None,
                mass_kg=None, velocity_mps=None):
    """
    功/能量计算
    直线: W = F·s
    旋转: W = T·θ
    动能: Ek = ½mv²
    """
    result = {}
    if force_N is not None and distance_m is not None:
        W = force_N * distance_m
        result['work_linear_J'] = round(W, 3)
        result['formula_linear'] = 'W = F·s'
    
    if torque_Nm is not None and angle_rad is not None:
        Wr = torque_Nm * angle_rad
        result['work_rotational_J'] = round(Wr, 3)
        result['formula_rotational'] = 'W = T·θ'
    
    if mass_kg is not None and velocity_mps is not None:
        Ek = 0.5 * mass_kg * velocity_mps * velocity_mps
        result['kinetic_energy_J'] = round(Ek, 3)
        result['formula_ke'] = 'Ek = ½mv²'
    
    return result


def power_calc(force_N=None, velocity_mps=None, torque_Nm=None, omega_rad_s=None,
               rpm=None, work_J=None, time_s=None):
    """
    功率计算
    直线: P = F·v
    旋转: P = T·ω = T·2πn/60
    """
    result = {}
    
    if force_N is not None and velocity_mps is not None:
        P = force_N * velocity_mps
        result['power_linear_W'] = round(P, 3)
        result['power_linear_kW'] = round(P / 1000, 4)
        result['formula_linear'] = 'P = F·v'
    
    if torque_Nm is not None:
        if omega_rad_s is not None:
            P = torque_Nm * omega_rad_s
        elif rpm is not None:
            P = torque_Nm * rpm * 2 * math.pi / 60
            result['speed_rpm'] = rpm
        else:
            P = 0
        result['power_rotational_W'] = round(P, 3)
        result['power_rotational_kW'] = round(P / 1000, 4)
        result['formula_rotational'] = 'P = T·ω'
    
    if work_J is not None and time_s is not None and time_s > 0:
        P2 = work_J / time_s
        result['power_work_W'] = round(P2, 3)
        result['formula_work'] = 'P = W/t'
    
    return result


def friction(force_normal_N, mu_static=0, mu_kinetic=0, mu_rolling=0):
    """
    摩擦力计算
    Fs = μs·N (静摩擦)
    Fk = μk·N (动摩擦)
    Fr = μr·N (滚动摩擦)
    """
    result = {'normal_force_N': force_normal_N}
    if mu_static:
        result['static_friction_N'] = round(mu_static * force_normal_N, 3)
        result['mu_static'] = mu_static
    if mu_kinetic:
        result['kinetic_friction_N'] = round(mu_kinetic * force_normal_N, 3)
        result['mu_kinetic'] = mu_kinetic
    if mu_rolling:
        result['rolling_friction_N'] = round(mu_rolling * force_normal_N, 3)
        result['mu_rolling'] = mu_rolling
    return result


# ============ 2. 转动惯量 (Mass Moment of Inertia) ============

def mass_inertia(shape, mass_kg=None, density_kgm3=None, **dims):
    """
    常见形状的转动惯量计算 (20种)
    
    形状: solid_cylinder, hollow_cylinder, solid_sphere, thin_sphere,
          thin_rod_center, thin_rod_end, rectangular_plate, annulus,
          cone, rectangular_block, thick_wall_tube
    """
    def calc_mass(vol):
        if mass_kg:
            return mass_kg
        if density_kgm3:
            return density_kgm3 * vol
        return 1.0  # 默认单位质量
    
    shape = shape.lower()
    result = {'shape': shape}
    
    if shape == 'solid_cylinder' or shape == 'disc':
        # 实心圆柱/圆盘  I = ½mr² (绕轴线)
        r = dims.get('r', dims.get('d', 0) / 2)
        h = dims.get('h', 0)
        V = math.pi * r * r * h if h > 0 else math.pi * r * r
        m = calc_mass(V)
        I = 0.5 * m * r * r
        result['I_axial_kgm2'] = round(I, 6)
        # 绕直径 (端面) I = m(3r²+h²)/12
        if h > 0:
            I_diam = m * (3*r*r + h*h) / 12
            result['I_diametral_kgm2'] = round(I_diam, 6)
        result['formula'] = 'I = ½mr² (轴线), I = m(3r²+h²)/12 (直径)'
    
    elif shape == 'hollow_cylinder':
        # 空心圆柱  I = ½m(r₁²+r₂²)
        r1 = dims.get('r1', dims.get('d1', 0) / 2)  # 内径
        r2 = dims.get('r2', dims.get('d2', 0) / 2)  # 外径
        h = dims.get('h', 0)
        V = math.pi * (r2*r2 - r1*r1) * h if h > 0 else math.pi * (r2*r2 - r1*r1)
        m = calc_mass(V)
        I = 0.5 * m * (r1*r1 + r2*r2)
        result['I_axial_kgm2'] = round(I, 6)
        result['formula'] = 'I = ½m(r₁²+r₂²)'
    
    elif shape == 'solid_sphere':
        # 实心球  I = ⅖mr²
        r = dims.get('r', dims.get('d', 0) / 2)
        V = 4/3 * math.pi * r**3
        m = calc_mass(V)
        I = 0.4 * m * r * r
        result['I_kgm2'] = round(I, 6)
        result['formula'] = 'I = ⅖mr²'
    
    elif shape == 'thin_sphere':
        # 薄球壳  I = ⅔mr²
        r = dims.get('r', dims.get('d', 0) / 2)
        t = dims.get('t', 0.001)
        V = 4 * math.pi * r * r * t
        m = calc_mass(V)
        I = 2/3 * m * r * r
        result['I_kgm2'] = round(I, 6)
        result['formula'] = 'I = ⅔mr²'
    
    elif shape == 'thin_rod_center':
        # 细杆(过中心)  I = 1/12 mL²
        L = dims.get('L', dims.get('l', 0))
        A = dims.get('A', dims.get('d', 0.01))  # 截面积
        V = A * L
        m = calc_mass(V)
        I = m * L * L / 12
        result['I_kgm2'] = round(I, 6)
        result['formula'] = 'I = 1/12·mL²'
    
    elif shape == 'thin_rod_end':
        # 细杆(过端部)  I = ⅓mL²
        L = dims.get('L', dims.get('l', 0))
        A = dims.get('A', dims.get('d', 0.01))
        V = A * L
        m = calc_mass(V)
        I = m * L * L / 3
        result['I_kgm2'] = round(I, 6)
        result['formula'] = 'I = ⅓mL²'
    
    elif shape == 'rectangular_plate':
        # 矩形薄板(过中心,垂直板面) I = 1/12·m(a²+b²)
        a = dims.get('a', dims.get('w', dims.get('width', 0)))
        b = dims.get('b', dims.get('h', dims.get('height', 0)))
        t = dims.get('t', dims.get('thickness', 0.001))
        V = a * b * t
        m = calc_mass(V)
        I = m * (a*a + b*b) / 12
        result['I_kgm2'] = round(I, 6)
        # 绕x轴 I = mb²/12
        result['I_x_kgm2'] = round(m * b * b / 12, 6)
        # 绕y轴 I = ma²/12
        result['I_y_kgm2'] = round(m * a * a / 12, 6)
        result['formula'] = 'I = 1/12·m(a²+b²)'
    
    elif shape == 'annulus':
        # 圆环 (纤细) I = mr²
        r = dims.get('r', dims.get('d', 0) / 2)
        A = dims.get('A', 0.001)  # 环截面积
        V = 2 * math.pi * r * A
        m = calc_mass(V)
        I = m * r * r
        result['I_kgm2'] = round(I, 6)
        result['formula'] = 'I = mr²'
    
    elif shape == 'cone':
        # 圆锥(绕轴线) I = 3/10·mr²
        r = dims.get('r', dims.get('d', 0) / 2)
        h = dims.get('h', 0)
        V = math.pi * r * r * h / 3
        m = calc_mass(V)
        I = 0.3 * m * r * r
        result['I_axial_kgm2'] = round(I, 6)
        result['formula'] = 'I = 3/10·mr²'
    
    elif shape == 'rectangular_block':
        # 长方体(过质心) I = 1/12·m(a²+b²)
        a = dims.get('a', dims.get('w', 0))
        b = dims.get('b', dims.get('h', 0))
        c = dims.get('c', dims.get('d', 0))
        V = a * b * c
        m = calc_mass(V)
        result['I_x_kgm2'] = round(m * (b*b + c*c) / 12, 6)
        result['I_y_kgm2'] = round(m * (a*a + c*c) / 12, 6)
        result['I_z_kgm2'] = round(m * (a*a + b*b) / 12, 6)
        result['formula'] = 'Ix=m(b²+c²)/12, Iy=m(a²+c²)/12, Iz=m(a²+b²)/12'
    
    elif shape == 'parallel_axis':
        # 平行轴定理  I = I_cm + md²
        I_cm = dims.get('I_cm', 0)
        d = dims.get('d', 0)
        m = mass_kg or 1.0
        I = I_cm + m * d * d
        result['I_cm_kgm2'] = I_cm
        result['offset_m'] = d
        result['mass_kg'] = m
        result['I_parallel_kgm2'] = round(I, 6)
        result['formula'] = 'I = I_cm + md²'
    
    else:
        return {'error': f'未知形状: {shape}'}
    
    if mass_kg:
        result['mass_kg'] = mass_kg
    return result


def parallel_axis_theorem(I_cm, mass, d):
    """平行轴定理 I = I_cm + md²"""
    I = I_cm + mass * d * d
    return {
        'I_cm': I_cm, 'mass': mass, 'offset_d': d,
        'I_parallel': round(I, 6),
        'formula': 'I = I_cm + m·d²'
    }


def radius_of_gyration(I, mass):
    """回转半径 i = √(I/m)"""
    if mass <= 0:
        return {'error': '质量必须大于0'}
    i = math.sqrt(I / mass)
    return {
        'inertia_kgm2': I, 'mass_kg': mass,
        'radius_of_gyration_m': round(i, 4),
        'radius_of_gyration_mm': round(i * 1000, 2),
    }


# ============ 3. 振动 (Vibration) ============

def spring_mass_vibration(k_Nm, mass_kg, zeta=0):
    """
    弹簧质量系统振动
    ωn = √(k/m)  (无阻尼固有频率)
    fn = ωn/(2π) (Hz)
    """
    omega_n = math.sqrt(k_Nm / mass_kg) if mass_kg > 0 else 0
    fn = omega_n / (2 * math.pi)
    
    # 阻尼固有频率
    omega_d = omega_n * math.sqrt(1 - zeta*zeta) if zeta < 1 else 0
    
    return {
        'stiffness_Nm': k_Nm, 'mass_kg': mass_kg,
        'natural_freq_rad_s': round(omega_n, 4),
        'natural_freq_Hz': round(fn, 4),
        'natural_freq_rpm': round(fn * 60, 2),
        'period_s': round(1/fn, 4) if fn > 0 else 0,
        'damping_ratio': zeta,
        'damped_freq_rad_s': round(omega_d, 4) if omega_d > 0 else 0,
    }


def torsional_vibration(G_mpa, J_mm4, L_mm, I_disc_kgm2):
    """
    扭转振动 (圆轴+圆盘)
    kt = G·J/L (扭转刚度)
    fn = √(kt/I)/(2π)
    """
    G_pa = G_mpa * 1e6
    J_m4 = J_mm4 * 1e-12
    L_m = L_mm / 1000
    
    kt = G_pa * J_m4 / L_m if L_m > 0 else 0
    omega_n = math.sqrt(kt / I_disc_kgm2) if I_disc_kgm2 > 0 else 0
    fn = omega_n / (2 * math.pi)
    
    return {
        'shear_modulus_GPa': G_mpa / 1000,
        'torsional_constant_m4': round(J_m4, 12),
        'length_m': round(L_m, 3),
        'torsional_stiffness_Nm_rad': round(kt, 2),
        'disc_inertia_kgm2': I_disc_kgm2,
        'natural_freq_rad_s': round(omega_n, 4),
        'natural_freq_Hz': round(fn, 4),
        'formula': 'ωn = √(kt/I), kt = G·J/L',
    }


def critical_shaft_speed(E_mpa, I_mm4, mass_kg, L_mm, g=9.81):
    """
    轴的临界转速 (单盘转子)
    ωcr = √(g/δ)  δ = mgL³/(48EI)
    """
    E_pa = E_mpa * 1e6
    I_m4 = I_mm4 * 1e-12
    L_m = L_mm / 1000
    W = mass_kg * g
    
    delta = W * L_m**3 / (48 * E_pa * I_m4) if E_pa * I_m4 > 0 else 0
    omega_cr = math.sqrt(g / delta) if delta > 0 else 0
    n_cr = omega_cr * 60 / (2 * math.pi)
    
    return {
        'deflection_mm': round(delta * 1000, 4),
        'critical_omega_rad_s': round(omega_cr, 2),
        'critical_speed_rpm': round(n_cr, 2),
        'formula': 'ωcr = √(g/δ), δ=mgL³/(48EI)',
    }


def simple_pendulum(L_m, g=9.81):
    """单摆 T = 2π√(L/g)"""
    T = 2 * math.pi * math.sqrt(L_m / g) if L_m > 0 else 0
    f = 1 / T if T > 0 else 0
    return {
        'length_m': L_m,
        'period_s': round(T, 4),
        'frequency_Hz': round(f, 4),
    }


# ============ 4. 飞轮/制动器 ============

def flywheel_energy(I_kgm2, omega_rad_s=None, rpm=None):
    """飞轮储能 E = ½Iω²"""
    if rpm is not None:
        omega_rad_s = rpm * 2 * math.pi / 60
    omega = omega_rad_s or 0
    E = 0.5 * I_kgm2 * omega * omega
    
    return {
        'inertia_kgm2': I_kgm2,
        'omega_rad_s': round(omega, 2),
        'speed_rpm': round(omega * 60 / (2*math.pi), 2) if omega > 0 else 0,
        'energy_kJ': round(E / 1000, 3),
        'energy_J': round(E, 1),
    }


def brake_torque(force_N, radius_m, num_shoes=2, mu=0.35):
    """制动器扭矩 (简单蹄式) T = n·μ·F·r"""
    T = num_shoes * mu * force_N * radius_m
    return {
        'actuating_force_N': force_N,
        'brake_radius_m': radius_m,
        'num_shoes': num_shoes,
        'friction_coeff': mu,
        'brake_torque_Nm': round(T, 2),
        'braking_power_kW': 0,  # 需要转速
    }


def lead_screw_efficiency(d_mm, pitch_mm, mu=0.15):
    """
    螺旋传动效率
    η = tan(λ) / tan(λ+ρ)
    λ = atan(P/(πd)) 导程角
    ρ = atan(μ) 摩擦角
    """
    d = d_mm / 1000
    P = pitch_mm / 1000
    lam = math.atan(P / (math.pi * d)) if d > 0 else 0
    rho = math.atan(mu)
    eta = math.tan(lam) / math.tan(lam + rho) if (lam + rho) > 0 else 0
    
    # 自锁条件: λ < ρ
    self_locking = lam < rho
    
    return {
        'diameter_mm': d_mm, 'pitch_mm': pitch_mm,
        'lead_angle_deg': round(math.degrees(lam), 2),
        'friction_angle_deg': round(math.degrees(rho), 2),
        'efficiency': round(eta, 4),
        'self_locking': self_locking,
        'formula': 'η = tan(λ)/tan(λ+ρ)',
    }


def screw_jack_torque(load_N, d_mm, pitch_mm, mu=0.15):
    """
    螺旋千斤顶驱动力矩
    T = F·d/2·tan(λ+ρ)
    """
    d = d_mm / 1000
    P = pitch_mm / 1000
    lam = math.atan(P / (math.pi * d))
    rho = math.atan(mu)
    
    T = load_N * d / 2 * math.tan(lam + rho)
    
    return {
        'load_N': load_N,
        'lifting_torque_Nm': round(T, 3),
        'lead_angle_deg': round(math.degrees(lam), 2),
        'formula': 'T = F·d/2·tan(λ+ρ)',
    }


# ============ 5. 轮系 (Gear Trains) ============

def planetary_gear(z_sun, z_ring, z_planet, carrier_input=True):
    """
    行星轮系传动比
    
    基本公式: n_sun + α·n_ring - (1+α)·n_carrier = 0
    α = z_ring / z_sun
    """
    alpha = z_ring / z_sun
    
    # 固定齿圈 (n_ring=0): n_carrier / n_sun = 1 / (1+α)
    ratio_fixed_ring = 1 / (1 + alpha)
    # 固定太阳轮 (n_sun=0): n_carrier / n_ring = α / (1+α)
    ratio_fixed_sun = alpha / (1 + alpha)
    # 固定行星架 (n_carrier=0): n_sun / n_ring = -α
    ratio_fixed_carrier = -alpha
    
    return {
        'sun_teeth': z_sun, 'ring_teeth': z_ring, 'planet_teeth': z_planet,
        'alpha': round(alpha, 4),
        'ratio_fixed_ring': round(ratio_fixed_ring, 4),
        'ratio_fixed_sun': round(ratio_fixed_sun, 4),
        'ratio_fixed_carrier': round(ratio_fixed_carrier, 4),
        'note': '正=同向, 负=反向',
    }


def compound_gear_train(teeth_list):
    """
    复合轮系总传动比
    i_total = (∏z_driven) / (∏z_driving)
    
    teeth_list: [(z1, z2), (z3, z4), ...] 每对啮合齿轮
    """
    ratio = 1.0
    stages = []
    for i, (z1, z2) in enumerate(teeth_list):
        stage_ratio = z2 / z1
        ratio *= stage_ratio
        stages.append({
            'stage': i + 1,
            'driving_teeth': z1, 'driven_teeth': z2,
            'stage_ratio': round(stage_ratio, 4),
        })
    
    return {
        'stages': stages,
        'total_ratio': round(ratio, 4),
        'direction': '同向' if ratio > 0 else '反向',
    }
