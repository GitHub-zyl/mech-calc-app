"""
链传动计算模块
参考：机械设计常用计算表 - 链轮参数计算 / 链条计算
"""
import math

def roller_chain_params(pitch, z):
    """
    滚子链链轮基本参数计算 (GB/T 1243)
    
    参数:
        pitch: 链条节距 (mm)
        z: 链轮齿数
    
    返回: dict
    """
    d = pitch / math.sin(math.pi / z)           # 分度圆直径
    dr = pitch * (0.5025 + 0.01 / z) if pitch <= 12.7 else pitch * 0.505  # 齿根圆直径近似
    
    da_max = d + 1.25 * pitch - dr
    da_min = d + (1 - 1.6 / z) * pitch - dr
    da = (da_max + da_min) / 2                   # 齿顶圆直径（平均）
    
    df = d - dr                                  # 齿根圆直径
    
    return {
        'pitch': pitch,
        'teeth': z,
        'pitch_diameter': round(d, 3),
        'tip_diameter': round(da, 3),
        'root_diameter': round(df, 3),
        'max_tip_diameter': round(da_max, 3),
    }


def chain_length(pitch, z1, z2, center_distance):
    """
    链条长度计算
    
    参数:
        pitch: 节距 (mm)
        z1, z2: 大小链轮齿数
        center_distance: 中心距 (mm)
    
    返回: dict
    """
    Lp = 2 * center_distance / pitch + (z1 + z2) / 2 + (z2 - z1)**2 / (4 * math.pi**2 * center_distance / pitch)
    Lp = round(Lp, 2)
    
    # 链条节数应取整数（偶数节）
    Lp_int = math.ceil(Lp / 2) * 2
    L_mm = Lp_int * pitch
    
    return {
        'pitch': pitch,
        'sprocket_teeth_1': z1,
        'sprocket_teeth_2': z2,
        'center_distance_mm': center_distance,
        'calculated_links': Lp,
        'recommended_links': Lp_int,
        'chain_length_mm': L_mm,
        'chain_length_m': round(L_mm / 1000, 3),
    }


def chain_power_capacity(pitch, z, rpm, chain_type='08A'):
    """
    滚子链传递功率估算
    
    参数:
        pitch: 节距 (mm)
        z: 小链轮齿数
        rpm: 小链轮转速
        chain_type: 链条型号 (08A, 10A, 12A, 16A, 20A)
    """
    # 链号对应的节距和极限拉伸载荷
    chain_data = {
        '06B': {'pitch': 9.525, 'load_kN': 8.9},
        '08A': {'pitch': 12.7, 'load_kN': 13.8},
        '08B': {'pitch': 12.7, 'load_kN': 18.0},
        '10A': {'pitch': 15.875, 'load_kN': 21.8},
        '10B': {'pitch': 15.875, 'load_kN': 22.2},
        '12A': {'pitch': 19.05, 'load_kN': 31.1},
        '12B': {'pitch': 19.05, 'load_kN': 29.0},
        '16A': {'pitch': 25.4, 'load_kN': 55.6},
        '16B': {'pitch': 25.4, 'load_kN': 60.0},
        '20A': {'pitch': 31.75, 'load_kN': 86.7},
        '20B': {'pitch': 31.75, 'load_kN': 95.0},
        '24A': {'pitch': 38.1, 'load_kN': 124.6},
        '24B': {'pitch': 38.1, 'load_kN': 160.0},
    }
    
    chain = chain_data.get(chain_type)
    if not chain:
        return {'error': f'未知链条型号: {chain_type}'}
    
    v = z * pitch * rpm / 60000  # m/s
    F_max = chain['load_kN'] * 1000 / 7  # 安全系数取7
    P = F_max * v / 1000  # kW
    
    return {
        'chain_type': chain_type,
        'pitch': chain['pitch'],
        'breaking_load_kN': chain['load_kN'],
        'speed_mps': round(v, 3),
        'power_capacity_kw': round(P, 2),
        'safety_factor': 7,
    }


def conveyor_chain_tension(mass_kg, speed_mps, length_m, mu=0.15):
    """
    倍速链/输送链张力计算
    
    参数:
        mass_kg: 输送物总质量 (kg)
        speed_mps: 输送速度 (m/s)
        length_m: 输送长度 (m)
        mu: 摩擦系数 (默认0.15)
    """
    g = 9.81
    F_friction = mass_kg * g * mu          # 摩擦力 N
    P = F_friction * speed_mps / 1000       # 所需功率 kW
    
    return {
        'total_mass_kg': mass_kg,
        'speed_mps': speed_mps,
        'friction_coefficient': mu,
        'friction_force_n': round(F_friction, 1),
        'required_power_kw': round(P, 3),
    }
