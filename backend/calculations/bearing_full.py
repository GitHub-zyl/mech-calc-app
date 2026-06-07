"""
滚动轴承详细选型计算模块
参考：GB/T 6391-2010(ISO 281:2007), SKF综合型录
"""


def calc_bearing_life_modified(C=None, P=None, n=None, a1=1.0, a23=1.0, bearing_type='ball'):
    """
    修正额定寿命计算
    L_nmh = a1·a23·(10^6/(60n))·(C/P)^p
    
    参数:
        C: 基本额定动载荷 kN
        P: 当量动载荷 kN
        n: 转速 rpm
        a1: 可靠度寿命修正系数 (默认1.0=90%可靠度, 0.62=95%, 0.53=96%, 0.33=99%)
        a23: 润滑/材料修正系数 (默认1.0, 良好润滑1.5-2.5)
        bearing_type: 'ball' (球轴承, p=3) | 'roller' (滚子轴承, p=10/3)
    """
    if not C or not P or not n:
        return {'error': '请提供 C(kN)、P(kN) 和 n(rpm)'}

    p = 3.0 if bearing_type == 'ball' else 10/3
    L10 = (10**6 / (60 * n)) * (C / P)**p if n > 0 and P > 0 else 0  # 基本额定寿命 (h)
    L_nmh = a1 * a23 * L10

    return {
        'dynamic_load_C_kN': C,
        'equivalent_load_P_kN': P,
        'speed_n_rpm': n,
        'bearing_type': bearing_type,
        'exponent_p': p,
        'reliability_factor_a1': a1,
        'lubrication_factor_a23': a23,
        'basic_L10h': round(L10, 1),
        'modified_Lnmh': round(L_nmh, 1),
        'formula': 'L_nmh = a1·a23·(10⁶/60n)·(C/P)^p',
        'reference': 'GB/T 6391-2010 (ISO 281:2007)',
    }


def calc_bearing_min_load(C0=None, n=None, dm=None, bearing_type='ball'):
    """
    最小载荷要求计算
    
    球轴承: Fm = 0.01·C0（当 dm<100 且 n<1000）或 Fm = k_r·C0
    滚子轴承: Fm = 0.02·C0
    
    参数:
        C0: 基本额定静载荷 kN
        n: 转速 rpm
        dm: 轴承节圆直径 mm, dm=(D+d)/2
        bearing_type: 'ball' | 'roller'
    """
    if not C0:
        return {'error': '请提供基本额定静载荷 C0(kN)'}

    if bearing_type == 'ball':
        Fm = 0.01 * C0
        if dm and dm >= 100:
            Fm *= (dm / 100)**0.5
        if n and n >= 1000:
            Fm *= (n / 1000)**0.5
    else:
        Fm = 0.02 * C0
        if dm and dm >= 100:
            Fm *= (dm / 100)**0.33

    return {
        'static_load_C0_kN': C0,
        'bearing_type': bearing_type,
        'pitch_diameter_dm_mm': dm,
        'speed_n_rpm': n,
        'min_radial_load_Fm_kN': round(Fm, 3),
        'formula': '球: Fm=0.01·C0, 滚子: Fm=0.02·C0',
        'reference': 'SKF综合型录 - 最小载荷要求',
    }


def calc_bearing_speed_limit(dm=None, n=None, bearing_type='ball', lubrication='grease'):
    """
    极限转速校核
    
    参考转速 / 极限转速取决于 ndm 值
    ndm = n × (D+d)/2 = n × dm
    
    极限 ndm 值 (粗略):
        - 深沟球轴承 (脂润滑): 500000
        - 圆柱滚子轴承 (脂润滑): 350000
        - 圆锥滚子轴承 (脂润滑): 250000
        - 推力球轴承 (脂润滑): 200000
    
    参数:
        dm: 节圆直径 mm
        n: 实际转速 rpm
        bearing_type: 'deep_groove_ball'|'cylindrical_roller'|'tapered_roller'|'thrust_ball'|'angular_contact'
        lubrication: 'grease'|'oil_bath'|'oil_mist'|'oil_jet'
    """
    if not dm or not n:
        return {'error': '请提供节圆直径 dm(mm) 和转速 n(rpm)'}

    # 脂润滑基准 ndm
    ndm_limits = {
        'deep_groove_ball': 500000,
        'angular_contact': 450000,
        'cylindrical_roller': 350000,
        'tapered_roller': 250000,
        'thrust_ball': 200000,
        'spherical_roller': 200000,
    }

    # 润滑系数
    lube_factors = {
        'grease': 1.0,
        'oil_bath': 1.5,
        'oil_mist': 2.0,
        'oil_jet': 2.5,
    }

    base_ndm = ndm_limits.get(bearing_type, 300000)
    lube_factor = lube_factors.get(lubrication, 1.0)
    ndm_limit = base_ndm * lube_factor
    actual_ndm = n * dm

    safety = ndm_limit / actual_ndm if actual_ndm > 0 else float('inf')

    return {
        'bearing_type': bearing_type,
        'lubrication': lubrication,
        'pitch_diameter_dm_mm': dm,
        'actual_speed_n_rpm': n,
        'actual_ndm': round(actual_ndm, 1),
        'limit_ndm': round(ndm_limit, 1),
        'safety_ratio': round(safety, 2),
        'is_safe': safety >= 1.0,
        'formula': 'ndm = n·(D+d)/2 ≤ ndm_limit',
        'reference': 'SKF综合型录 / 机械设计手册第16篇',
    }
