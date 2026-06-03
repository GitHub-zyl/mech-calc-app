"""
三角皮带 / 同步带传动计算模块
参考：机械设计常用计算表 - 三角皮带参数表 / 同步带减速机设计计算
"""
import math

# ============ 三角皮带 ============

V_BELT_SECTIONS = {
    'A': {'pitch_width': 11.0, 'height': 8.0, 'angle_deg': 40, 'mass_kg_m': 0.10},
    'B': {'pitch_width': 14.0, 'height': 11.0, 'angle_deg': 40, 'mass_kg_m': 0.17},
    'C': {'pitch_width': 19.0, 'height': 14.0, 'angle_deg': 40, 'mass_kg_m': 0.30},
    'D': {'pitch_width': 27.0, 'height': 19.0, 'angle_deg': 40, 'mass_kg_m': 0.60},
    'E': {'pitch_width': 32.0, 'height': 23.0, 'angle_deg': 40, 'mass_kg_m': 0.87},
    'SPA': {'pitch_width': 11.0, 'height': 10.0, 'angle_deg': 40, 'mass_kg_m': 0.10},
    'SPB': {'pitch_width': 14.0, 'height': 13.0, 'angle_deg': 40, 'mass_kg_m': 0.17},
    'SPC': {'pitch_width': 19.0, 'height': 18.0, 'angle_deg': 40, 'mass_kg_m': 0.30},
    'Z': {'pitch_width': 8.5, 'height': 6.0, 'angle_deg': 40, 'mass_kg_m': 0.06},
}

def vbelt_calc(section, power_kw, n1_rpm, ratio, center_distance_mm):
    """
    三角皮带传动计算
    
    参数:
        section: 带型 (A/B/C/D/E/SPA/SPB/SPC/Z)
        power_kw: 传递功率 (kW)
        n1_rpm: 小带轮转速 (rpm)
        ratio: 传动比 (>=1)
        center_distance_mm: 中心距 (mm)
    """
    belt = V_BELT_SECTIONS.get(section.upper())
    if not belt:
        return {'error': f'未知带型: {section}'}
    
    # 小带轮基准直径推荐值
    d1_min = {'A': 75, 'B': 125, 'C': 200, 'D': 355, 'E': 500,
              'SPA': 90, 'SPB': 140, 'SPC': 224, 'Z': 50}
    d1 = d1_min.get(section.upper(), 100)
    d2 = round(d1 * ratio)
    
    # 带速
    v = math.pi * d1 * n1_rpm / 60000  # m/s
    if v > 30:
        return {'error': f'带速{v:.1f}m/s 超过30m/s，建议增大带轮直径'}
    
    # 基准长度（近似）
    L0 = 2 * center_distance_mm + math.pi * (d1 + d2) / 2 + (d2 - d1)**2 / (4 * center_distance_mm)
    
    # 小带轮包角
    alpha_deg = 180 - 60 * (d2 - d1) / center_distance_mm
    if alpha_deg < 120:
        return {'warning': f'包角{alpha_deg:.1f}° < 120°，建议增大中心距或加张紧轮'}
    
    K_alpha = 1 - (180 - alpha_deg) / 180 * 0.3  # 包角系数
    K_L = 1.0  # 长度系数（简化）
    
    # 单根皮带传递功率（简化）
    P0 = 0.1 * (d1 * n1_rpm / 1000)**1.5  # kW
    
    z = power_kw / (P0 * K_alpha * K_L)  # 根数
    
    return {
        'belt_section': section.upper(),
        'small_pulley_diameter': d1,
        'large_pulley_diameter': d2,
        'center_distance_mm': center_distance_mm,
        'belt_speed_mps': round(v, 2),
        'wrap_angle_deg': round(alpha_deg, 1),
        'approx_belt_length_mm': round(L0, 1),
        'wrap_angle_factor': round(K_alpha, 3),
        'single_belt_power_kw': round(P0, 3),
        'required_belts': math.ceil(z),
        'transmission_ratio': ratio,
    }


def vbelt_length_to_center(section, L, d1, d2):
    """
    已知皮带长度反算中心距
    """
    C = d1 + d2
    D = d2 - d1
    A = 2 * L - math.pi * C
    B = A**2 - 8 * D**2
    if B < 0:
        return {'error': '长度过短'}
    a = (A + math.sqrt(B)) / 4
    return {'center_distance_mm': round(a, 1)}


# ============ 同步带（周节制）============

SYNCHRONOUS_BELTS = {
    'MXL': {'pitch': 2.032, 'max_width': 6.4},
    'XL':  {'pitch': 5.080, 'max_width': 9.5},
    'L':   {'pitch': 9.525, 'max_width': 25.4},
    'H':   {'pitch': 12.700, 'max_width': 76.2},
    'XH':  {'pitch': 22.225, 'max_width': 101.6},
    'XXH': {'pitch': 31.750, 'max_width': 127.0},
}


def synchronous_belt_calc(belt_type, power_kw, n1_rpm, ratio, z1=None, center_distance_mm=None):
    """
    同步带传动计算（周节制）
    
    参数:
        belt_type: 带型 (MXL/XL/L/H/XH/XXH)
        power_kw: 功率 (kW)
        n1_rpm: 小带轮转速
        ratio: 传动比
        z1: 小带轮齿数（自动推荐）
        center_distance_mm: 中心距（自动计算）
    """
    belt = SYNCHRONOUS_BELTS.get(belt_type.upper())
    if not belt:
        return {'error': f'未知带型: {belt_type}'}
    
    pb = belt['pitch']
    
    # 推荐最少齿数
    z_min_table = {'MXL': 12, 'XL': 10, 'L': 10, 'H': 14, 'XH': 22, 'XXH': 22}
    z1_min = z_min_table.get(belt_type.upper(), 10)
    
    if z1 is None:
        z1 = max(z1_min, int(60 * power_kw**0.25 / pb**0.5))
    z2 = round(z1 * ratio)
    
    d1 = z1 * pb / math.pi
    d2 = z2 * pb / math.pi
    
    v = math.pi * d1 * n1_rpm / 60000  # m/s
    
    # 额定功率（简化模型）
    T_max = 0.5 * belt['max_width'] * pb * 0.5  # N·mm
    P_rated = T_max * n1_rpm / 9550000  # kW
    
    # 带宽
    width_needed = power_kw / P_rated * belt['max_width'] if P_rated > 0 else belt['max_width']
    
    result = {
        'belt_type': belt_type.upper(),
        'pitch_mm': pb,
        'small_pulley_teeth': z1,
        'large_pulley_teeth': z2,
        'small_pulley_diameter_mm': round(d1, 2),
        'large_pulley_diameter_mm': round(d2, 2),
        'belt_speed_mps': round(v, 2),
        'rated_power_kw': round(P_rated, 3),
        'recommended_width_mm': round(width_needed, 1),
        'transmission_ratio': round(ratio, 4),
    }
    
    if center_distance_mm:
        # 计算带的节线长度
        C = center_distance_mm
        Lp = 2 * C + math.pi * (d1 + d2) / 2 + (d2 - d1)**2 / (4 * C)
        result['center_distance_mm'] = C
        result['belt_pitch_length_mm'] = round(Lp, 1)
        result['belt_teeth_count'] = round(Lp / pb)
    
    return result
