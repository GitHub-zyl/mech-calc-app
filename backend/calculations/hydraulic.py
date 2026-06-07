"""
液压系统计算模块
参考：机械设计常用计算表 - 缝隙.管路 / 蓄能器 / 油箱.热平衡 / 液压冲击 / 液压油
"""
import math


def pipe_pressure_loss(flow_lpm, inner_diam_mm, length_m, viscosity_cst=46,
                       density_kgm3=870, pipe_type='metal'):
    """
    管路压力损失计算
    
    参数:
        flow_lpm: 流量 (L/min)
        inner_diam_mm: 管内径 (mm)
        length_m: 管长 (m)
        viscosity_cst: 油液运动粘度 (cSt, 默认46)
        density_kgm3: 油液密度 (kg/m³, 默认870)
        pipe_type: 管材类型 'metal'或'rubber'
    """
    d = inner_diam_mm / 1000  # m
    A = math.pi * d * d / 4   # m²
    Q = flow_lpm / 60000      # m³/s
    v = Q / A if A > 0 else 0  # m/s（流速）
    
    # 雷诺数 Re
    nu = viscosity_cst * 1e-6  # m²/s
    Re = v * d / nu if nu > 0 else 0
    
    # 判断流态
    if Re < 2320:
        flow_type = '层流'
        lam = 64 / Re if Re > 0 else 0
    else:
        flow_type = '紊流'
        # Blasius 公式 (光滑管)
        lam = 0.3164 / (Re ** 0.25) if Re > 0 else 0
    
    # 沿程压力损失 Δp = λ * (L/d) * (ρv²/2)
    delta_p = lam * (length_m / d) * (density_kgm3 * v * v / 2) if d > 0 else 0  # Pa
    delta_p_bar = delta_p / 100000  # bar
    
    # 推荐流速
    v_rec = '吸油管:0.5~1.5, 压力管:2~5, 回油管:1.5~2.5 m/s'
    v_ok = v <= 5.0
    
    return {
        'flow_lpm': flow_lpm,
        'inner_diameter_mm': inner_diam_mm,
        'flow_velocity_mps': round(v, 3),
        'reynolds_number': round(Re, 1),
        'flow_type': flow_type,
        'friction_factor': round(lam, 4),
        'pressure_loss_bar': round(delta_p_bar, 5),
        'pressure_loss_mpa': round(delta_p_bar / 10, 5),
        'velocity_recommendation': v_rec,
        'velocity_ok': v_ok,
    }


def thin_orifice_flow(d_mm, delta_p_bar, discharge_coeff=0.62, density_kgm3=870):
    """
    薄壁小孔流量 Q = Cd * A * sqrt(2*Δp/ρ)
    
    参数:
        d_mm: 小孔直径 (mm)
        delta_p_bar: 孔前后压差 (bar)
        discharge_coeff: 流量系数 (默认0.62)
        density_kgm3: 密度 (kg/m³)
    """
    A = math.pi * (d_mm / 1000) ** 2 / 4  # m²
    dp_pa = delta_p_bar * 100000  # Pa
    Q = discharge_coeff * A * math.sqrt(2 * dp_pa / density_kgm3)  # m³/s
    Q_lpm = Q * 60000  # L/min
    
    return {
        'orifice_diameter_mm': d_mm,
        'pressure_diff_bar': delta_p_bar,
        'discharge_coefficient': discharge_coeff,
        'flow_lpm': round(Q_lpm, 4),
        'flow_m3s': round(Q, 8),
    }


def accumulator_selection(V0_L, p0_bar, p1_bar, p2_bar):
    """
    蓄能器有效容积计算 (等温/绝热)
    
    参数:
        V0_L: 蓄能器公称容积 (L)
        p0_bar: 充气压力 (bar)
        p1_bar: 最低工作压力 (bar)
        p2_bar: 最高工作压力 (bar)
    """
    # 波义耳定律 p0*V0^n = p1*V1^n = p2*V2^n
    # 有效容积 ΔV = V1 - V2
    
    # 等温 (n=1)
    V1_iso = p0_bar * V0_L / p1_bar
    V2_iso = p0_bar * V0_L / p2_bar
    delta_V_iso = V1_iso - V2_iso
    
    # 绝热 (n=1.4 氮气)
    n = 1.4
    V1_adia = V0_L * (p0_bar / p1_bar) ** (1/n)
    V2_adia = V0_L * (p0_bar / p2_bar) ** (1/n)
    delta_V_adia = V1_adia - V2_adia
    
    return {
        'nominal_volume_L': V0_L,
        'gas_precharge_bar': p0_bar,
        'min_pressure_bar': p1_bar,
        'max_pressure_bar': p2_bar,
        'effective_volume_isothermal_L': round(delta_V_iso, 2),
        'effective_volume_adiabatic_L': round(delta_V_adia, 2),
        'volume_ratio_p2_p1': round(p2_bar / p1_bar, 2),
        'note': '等温(慢速)、绝热(快速)工况',
    }


def hydraulic_shock(v1_mps, v2_mps, pipe_length_m, bulk_modulus_mpa=1400,
                    density_kgm3=870, pipe_diam_mm=20, wall_thickness_mm=2,
                    pipe_emodule_mpa=206000, close_time_s=None):
    """
    液压冲击计算
    
    参数:
        v1_mps: 管路原流速 (m/s)
        v2_mps: 关闭后流速 (m/s)
        pipe_length_m: 管长 (m)
        bulk_modulus_mpa: 油液体积弹性模量 (MPa)
        density_kgm3: 油液密度 (kg/m³)
        pipe_diam_mm: 管内径 (mm)
        wall_thickness_mm: 管壁厚 (mm)
        pipe_emodule_mpa: 管材弹性模量 (MPa)
        close_time_s: 关闭时间 (s)，None表示瞬时关闭
    """
    # 冲击波传播速度
    K = bulk_modulus_mpa * 1e6
    E = pipe_emodule_mpa * 1e6
    d = pipe_diam_mm / 1000
    delta = wall_thickness_mm / 1000
    
    # 等效弹性模量
    if d > 0 and delta > 0:
        K_eq = 1 / (1/K + d/(E * delta))
    else:
        K_eq = K
    
    a = math.sqrt(K_eq / density_kgm3)  # 冲击波速度 m/s
    
    # 往复时间
    T = 2 * pipe_length_m / a if a > 0 else 0
    
    # 压力增量
    delta_v = abs(v1_mps - v2_mps)
    delta_p_direct = density_kgm3 * a * delta_v  # Pa 直接冲击
    
    if close_time_s is not None and close_time_s > T and T > 0:
        # 间接冲击
        delta_p = delta_p_direct * T / close_time_s
        shock_type = '间接冲击'
    else:
        delta_p = delta_p_direct
        shock_type = '直接冲击'
    
    return {
        'shock_wave_speed_mps': round(a, 1),
        'round_trip_time_s': round(T, 4),
        'pressure_increase_bar': round(delta_p / 100000, 2),
        'pressure_increase_mpa': round(delta_p / 1000000, 3),
        'shock_type': shock_type,
        'close_time_s': close_time_s or 0,
    }


def oil_tank_heat_balance(power_kw, tank_volume_L=None, temp_rise_target_K=30,
                          heat_transfer_coeff=15, ambient_temp_C=25):
    """
    油箱热平衡计算
    
    参数:
        power_kw: 系统发热功率 (kW)
        tank_volume_L: 油箱有效容积 (L)
        temp_rise_target_K: 目标温升 (K)
        heat_transfer_coeff: 散热系数 W/(m²·K)
        ambient_temp_C: 环境温度 (°C)
    """
    # 推荐油箱容积 (系统流量的3~5倍)
    if tank_volume_L:
        # 油箱散热面积估算（近似：A = 0.065 * V^(2/3)）
        V_m3 = tank_volume_L / 1000
        A = 6 * V_m3 ** (2/3)  # m² 近似
        # 自然散热功率
        P_cool = heat_transfer_coeff * A * temp_rise_target_K / 1000  # kW
        actual_temp_rise = power_kw / (heat_transfer_coeff * A / 1000) if A > 0 else 999
        need_cooler = power_kw > P_cool
        
        return {
            'power_loss_kw': power_kw,
            'tank_volume_L': tank_volume_L,
            'cooling_area_m2': round(A, 2),
            'natural_cooling_power_kw': round(P_cool, 2),
            'estimated_temp_rise_K': round(actual_temp_rise, 1),
            'target_temp_rise_K': temp_rise_target_K,
            'needs_cooler': need_cooler,
        }
    else:
        # 根据发热功率推荐油箱容积
        rec_vol = power_kw * 60  # 粗略 60L/kW
        return {
            'power_loss_kw': power_kw,
            'recommended_tank_volume_L': round(rec_vol, 0),
            'note': '推荐容积 = 系统流量×(3~5倍)',
        }


def oil_viscosity_temp(nu_40, t_C, vi=100):
    """
    油液粘度-温度关系 (近似)
    
    参数:
        nu_40: 40°C时粘度 (cSt)
        t_C: 实际温度 (°C)
        vi: 粘度指数 (默认100)
    """
    # 近似公式 (Walther-MacCaull)
    # log(log(ν+0.7)) = A - B·log(T)
    import math
    
    T = t_C + 273.15
    T_40 = 40 + 273.15
    
    loglog_nu40 = math.log10(math.log10(nu_40 + 0.7))
    
    # 简化估算
    if vi >= 100:
        B = 3.0
    elif vi >= 70:
        B = 3.5
    else:
        B = 4.0
    
    A = loglog_nu40 + B * math.log10(T_40)
    loglog_nu = A - B * math.log10(T)
    nu = 10 ** (10 ** loglog_nu) - 0.7
    
    return {
        'viscosity_at_40C_cst': nu_40,
        'temperature_C': t_C,
        'viscosity_at_t_cst': round(nu, 1),
        'viscosity_index': vi,
    }
