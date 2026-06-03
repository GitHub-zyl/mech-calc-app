"""
疲劳强度计算模块
参考：机械设计手册(成大先)第16篇, ISO 12107, ASTM E739
"""
import math


def calc_sn_curve(S_ut=None, N1=None, N2=None, Se_prime=None, N_target=None):
    """
    S-N 曲线（应力-寿命曲线）双对数拟合
    
    S_f(N) = S_ut × (N)^b
    其中 b = log(S_f(N1)/S_f(N2)) / log(N1/N2) [或通过两点反推]
    
    标准方法：
    S_1000 = 0.9·S_ut（锻造材料的 10³ 次疲劳强度）
    Se（疲劳极限, 10⁶ 次）= Se_prime
    
    参数:
        S_ut: 抗拉强度 MPa
        N1: 第一个参考循环数 (默认1000)
        N2: 第二个参考循环数 (默认10⁶)
        Se_prime: 疲劳极限（无限寿命）MPa
        N_target: 指定循环数（如不提供则返回 b 系数和任意 N 的估算函数描述）
    
    返回: 拟合得到的 S_f 值
    """
    if not S_ut or not Se_prime:
        return {'error': '请提供抗拉强度 S_ut(MPa) 和疲劳极限 Se_prime(MPa)'}

    N1_val = N1 or 1000
    N2_val = N2 or 10**6

    # S-N 曲线双对数拟合: S = a·N^b
    S1 = 0.9 * S_ut  # 10³ 次强度
    S2 = Se_prime     # 疲劳极限

    b = math.log10(S1 / S2) / math.log10(N1_val / N2_val) if S2 > 0 and S1 > 0 else 0
    a = S1 / (N1_val)**b if N1_val > 0 else 0

    result = {
        'S_ut_MPa': S_ut,
        'Se_prime_MPa': Se_prime,
        'N1_cycles': N1_val,
        'S1000_MPa': round(S1, 2),
        'N2_cycles': N2_val,
        'Se_MPa': round(S2, 2),
        'b_exponent': round(b, 6),
        'a_coefficient': round(a, 4),
        'formula': 'S_f = a·N^b (双对数 S-N 曲线)',
        'reference': '机械设计手册(成大先)第16篇 §3, ISO 12107',
    }

    if N_target is not None:
        if N_target <= 10**3:
            S_f_val = S1
        elif N_target >= 10**6:
            S_f_val = S2
        else:
            S_f_val = a * N_target**b
        result['N_target'] = N_target
        result['S_f_MPa'] = round(S_f_val, 2)

    return result


def calc_stress_concentration(K_t=None, q=None, material_type='steel'):
    """
    有效应力集中系数
    K_f = 1 + q·(K_t - 1)
    
    参数:
        K_t: 理论应力集中系数
        q: 缺口敏感系数 (0~1, 0=不敏感, 1=完全敏感)
        material_type: 'steel'|'aluminum'|'cast_iron'|'titanium' (用于自动估算 q)
    
    q 的自动估算（基于材料类型和近似 S_ut 范围）:
        - 结构钢: q ≈ 0.7-0.95
        - 铝合金: q ≈ 0.8-0.95
        - 铸铁: q ≈ 0-0.1 (对缺口敏感度极低)
        - 钛合金: q ≈ 0.5-0.75
    """
    if K_t is None:
        return {'error': '请提供理论应力集中系数 K_t'}

    # 自动估算 q（如果未提供）
    if q is None:
        q_defaults = {
            'steel': 0.85,
            'aluminum': 0.90,
            'cast_iron': 0.05,
            'titanium': 0.65,
        }
        q = q_defaults.get(material_type.lower(), 0.85)

    K_f = 1 + q * (K_t - 1)

    return {
        'K_t_theoretical': K_t,
        'q_notch_sensitivity': round(q, 4),
        'material_type': material_type,
        'K_f_effective': round(K_f, 4),
        'formula': 'K_f = 1 + q·(K_t - 1)',
        'reference': 'Peterson应力集中系数 / 机械设计手册第16篇',
    }


def calc_miner_damage(stress_levels=None, cycles=None, S_ut=None, Se=None):
    """
    Miner 线性累积损伤法则
    
    D = Σ(n_i / N_i)
    
    参数:
        stress_levels: 各级应力幅值列表 [σ_a1, σ_a2, ...] (MPa)
        cycles: 各级循环次数列表 [n1, n2, ...]
        S_ut: 抗拉强度 MPa
        Se: 疲劳极限 MPa
    
    返回: 总损伤 D 和剩余寿命比例
    """
    if not stress_levels or not cycles or not S_ut or not Se:
        return {'error': '请提供 stress_levels([]), cycles([]), S_ut(MPa), Se(MPa)'}

    if len(stress_levels) != len(cycles):
        return {'error': 'stress_levels 和 cycles 长度必须一致'}

    # S-N 拟合参数
    N_ref1 = 10**3
    N_ref2 = 10**6
    S1 = 0.9 * S_ut
    b = math.log10(S1 / Se) / math.log10(N_ref1 / N_ref2) if Se > 0 else 0
    a = S1 / N_ref1**b

    D = 0
    level_details = []
    for i, (sigma, n_i) in enumerate(zip(stress_levels, cycles)):
        if sigma <= 0 or n_i <= 0:
            N_i = float('inf')
        elif sigma >= S1:
            N_i = N_ref1
        elif sigma <= Se:
            N_i = float('inf')
        else:
            N_i = (sigma / a) ** (1/b) if b != 0 else float('inf')

        d_i = n_i / N_i if N_i != float('inf') else 0
        D += d_i
        level_details.append({
            'level': i + 1,
            'stress_MPa': sigma,
            'n_cycles': n_i,
            'N_cycles_to_failure': round(N_i, 1) if N_i != float('inf') else '∞ (无限)',
            'damage_d_i': round(d_i, 6),
        })

    remaining_life = (1 - D) / D if D > 0 else float('inf')

    return {
        'S_ut_MPa': S_ut,
        'Se_MPa': Se,
        'total_damage_D': round(D, 6),
        'is_safe': D < 1.0,
        'remaining_life_factor': round(remaining_life, 2) if remaining_life != float('inf') else '∞',
        'level_details': level_details,
        'formula': 'D = Σ(n_i/N_i) [Miner线性累积损伤法则]',
        'reference': '机械设计手册(成大先)第16篇 §3.6, ASTM E1049',
    }
