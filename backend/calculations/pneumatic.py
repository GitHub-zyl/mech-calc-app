"""
气动系统计算模块
参考：SMC气动技术基础, ISO 6358, 机械设计手册(成大先)第21篇
"""
import math


def calc_cylinder_force(D=None, d_rod=None, p=None, action_type='extend'):
    """
    气缸理论输出力
    
    伸出: F_extend = π·D²/4 × p
    缩回: F_retract = π·(D² - d²)/4 × p
    
    参数:
        D: 气缸内径 mm
        d_rod: 活塞杆直径 mm
        p: 工作压力 MPa
        action_type: 'extend'（伸出）| 'retract'（缩回）
    """
    if not D or not p:
        return {'error': '请提供气缸内径 D(mm) 和工作压力 p(MPa)'}

    A_bore = math.pi * D**2 / 4  # 无杆腔面积 mm²
    A_rod = math.pi * d_rod**2 / 4 if d_rod else 0  # 有杆腔面积 mm²

    if action_type == 'extend':
        A_eff = A_bore
        force_desc = '伸出力'
    else:
        A_eff = A_bore - A_rod
        force_desc = '缩回力'

    # 理论力 N, 实际力取 85% (负载率)
    F_theory = p * A_eff
    F_actual = F_theory * 0.85

    return {
        'bore_diameter_D_mm': D,
        'rod_diameter_mm': d_rod,
        'pressure_p_MPa': p,
        'action_type': action_type,
        'effective_area_mm2': round(A_eff, 2),
        'F_theory_N': round(F_theory, 2),
        'F_actual_N': round(F_actual, 2),
        'F_theory_kgf': round(F_theory / 9.81, 2),
        'F_actual_kgf': round(F_actual / 9.81, 2),
        'formula': f'{force_desc}: F = p·A_eff (负载率85%)',
        'reference': 'SMC气动技术基础 / ISO 6432',
    }


def calc_cylinder_air_consumption(D=None, stroke=None, p=None,
                                  n_cycle=None, action_type='double'):
    """
    气缸耗气量计算 (ANR 工况: 20°C, 101.3kPa)
    
    每行程耗气量: V = A_eff × stroke × (p + 0.1013) / 0.1013  (L)
    换算为 L/min: Q = V × n_cycle / 1000
    
    参数:
        D: 气缸内径 mm
        stroke: 行程 mm
        p: 工作压力 MPa（表压）
        n_cycle: 每分钟循环次数 (1/min)
        action_type: 'double'（双作用）| 'single'（单作用，仅伸出耗气）
    """
    if not D or not stroke or p is None or not n_cycle:
        return {'error': '请提供 D(mm)、stroke(mm)、p(MPa) 和 n_cycle(1/min)'}

    A_bore = math.pi * D**2 / 4  # mm²
    p_abs = p + 0.1013  # 绝对压力 MPa

    # 双作用气缸（伸出+缩回 = 2倍）
    n_eff = 2 if action_type == 'double' else 1

    # 每行程耗气量 mm³ → L
    V_stroke_mm3 = A_bore * stroke
    V_per_stroke_L = V_stroke_mm3 / 1e6 * (p_abs / 0.1013)
    Q_L_min = V_per_stroke_L * n_cycle * n_eff

    return {
        'bore_diameter_mm': D,
        'stroke_mm': stroke,
        'pressure_MPa_gauge': p,
        'pressure_MPa_abs': round(p_abs, 4),
        'cycles_per_min': n_cycle,
        'action_type': action_type,
        'V_per_stroke_L': round(V_per_stroke_L, 3),
        'Q_L_min_ANR': round(Q_L_min, 2),
        'Q_NL_min_ANR': round(Q_L_min * 0.001, 4),
        'formula': 'Q = A·s·(p+0.1013)/0.1013·n (L/min ANR)',
        'reference': 'SMC气动技术基础 §2.3, ISO 8778',
    }


def calc_pipe_flow_rate(d=None, p1=None, p2=None, L=None, T=293):
    """
    管路流量计算（简化等温稳态流动模型）
    
    用于估算压缩空气管道流量（不可压缩简化模型）
    或用于可压缩流亚音速情况下的近似流量
    
    不可压缩简化:
    Q = π·d²/4 × √(2·Δp/ρ)
    Δp = (8·μ·L·Q)/(π·r⁴) * 修正
    
    简化工程公式 (压缩空气管道, 经验公式):
    Q ≈ 112 × d^2.655 × √(Δp / (L × T))
    
    参数:
        d: 管道内径 mm
        p1: 上游绝对压力 MPa
        p2: 下游绝对压力 MPa
        L: 管长 m
        T: 温度 K（默认293K = 20°C）
    
    返回: 估算流量 m³/min (ANR)
    """
    if not d or not p1 or not p2 or not L:
        return {'error': '请提供 d(mm)、p1(MPa)、p2(MPa) 和 L(m)'}

    # 压降
    dp = (p1 - p2) * 1e6  # Pa

    if dp <= 0:
        return {'error': 'p1 必须大于 p2'}

    # Q (m³/min ANR) ≈ 112 × d^2.655 × √(Δp / L) (经验公式, 仅参考)
    # 以下使用达西-魏斯巴赫公式替代

    # 更合理的估算：基于达西-魏斯巴赫
    rho = 1.2  # 空气密度 kg/m³ (标准工况)
    f = 0.02   # 摩擦系数 (粗糙估算)
    A = math.pi * (d / 1000)**2 / 4  # 截面积 m²
    v = math.sqrt(2 * dp / (rho * (1 + f * L * 1000 / d))) if dp > 0 else 0
    Q_m3_s = A * v
    Q_m3_min = Q_m3_s * 60

    return {
        'pipe_diameter_mm': d,
        'p1_MPa_abs': p1,
        'p2_MPa_abs': p2,
        'pressure_drop_kPa': round(dp / 1000, 2),
        'pipe_length_m': L,
        'temperature_K': T,
        'flow_velocity_m_s': round(v, 2),
        'Q_est_m3_min_ANR': round(Q_m3_min, 4),
        'note': '简化等温流动模型, μ=0, f=0.02 (估算)',
        'formula': 'Q = A·√(2Δp/ρ(1+fL/d)) [达西-魏斯巴赫]',
        'reference': '机械设计手册(成大先)第21篇 §3',
    }


def calc_air_receiver_volume(Q=None, p_max=None, p_min=None, t_cycle=None):
    """
    储气罐容积估算
    
    V = Q × t_cycle × 60 × p_atm / (p_max - p_min)
    
    参数:
        Q: 平均用气量 m³/min (ANR)
        p_max: 储气罐最高压力 MPa（绝对）
        p_min: 储气罐最低压力 MPa（绝对）
        t_cycle: 加载/卸载循环周期 min
    
    返回: 储气罐推荐容积 m³ 和 L
    """
    if not Q or not p_max or not p_min or not t_cycle:
        return {'error': '请提供 Q(m³/min)、p_max(MPa)、p_min(MPa) 和 t_cycle(min)'}

    p_atm = 0.1013  # 大气压 MPa
    delta_p = p_max - p_min

    if delta_p <= 0:
        return {'error': 'p_max 必须大于 p_min'}

    # V = Q_ANR × t × p_atm / delta_p
    V_m3 = Q * t_cycle * p_atm / delta_p
    V_L = V_m3 * 1000

    # 经验：增加20%安全裕量
    V_recommended = V_m3 * 1.2

    return {
        'Q_avg_m3_min_ANR': Q,
        'p_max_MPa_abs': p_max,
        'p_min_MPa_abs': p_min,
        'delta_p_MPa': round(delta_p, 4),
        'cycle_time_min': t_cycle,
        'theoretical_volume_m3': round(V_m3, 4),
        'theoretical_volume_L': round(V_L, 1),
        'recommended_volume_m3': round(V_recommended, 4),
        'recommended_volume_L': round(V_recommended * 1000, 1),
        'formula': 'V = Q·t_cycle·p_atm / (p_max - p_min) × 1.2',
        'reference': 'SMC气动技术基础 §6 / 压缩空气系统设计',
    }
