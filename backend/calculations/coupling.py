"""
联轴器 / O型圈 / 圆弧齿同步带 / 电机常识 计算模块
参考：机械设计常用计算表 - 齿式联轴器 / 万向联轴器 / O型圈 / 电机常识
"""
import math

# ============ 联轴器 ============

def coupling_gear_torque(power_kw, rpm, safety=1.5):
    """
    齿式联轴器扭矩校核
    
    参数:
        power_kw: 传递功率 (kW)
        rpm: 转速
        safety: 安全系数
    """
    T = 9550 * power_kw / rpm  # N·m
    T_calc = T * safety
    
    # 常见联轴器型号许用扭矩 (N·m)
    models = [
        {'model': 'CL1', 'T_nm': 710, 'max_rpm': 3780, 'd_mm': '12-32'},
        {'model': 'CL2', 'T_nm': 1400, 'max_rpm': 3000, 'd_mm': '20-40'},
        {'model': 'CL3', 'T_nm': 2500, 'max_rpm': 2400, 'd_mm': '30-50'},
        {'model': 'CL4', 'T_nm': 4000, 'max_rpm': 2000, 'd_mm': '40-65'},
        {'model': 'CL5', 'T_nm': 6300, 'max_rpm': 1700, 'd_mm': '50-75'},
        {'model': 'CL6', 'T_nm': 10000, 'max_rpm': 1500, 'd_mm': '60-85'},
        {'model': 'CL7', 'T_nm': 16000, 'max_rpm': 1300, 'd_mm': '70-100'},
        {'model': 'CL8', 'T_nm': 25000, 'max_rpm': 1100, 'd_mm': '80-120'},
        {'model': 'CL9', 'T_nm': 40000, 'max_rpm': 1000, 'd_mm': '90-140'},
        {'model': 'CL10', 'T_nm': 63000, 'max_rpm': 900, 'd_mm': '100-160'},
    ]
    
    rec = None
    for m in models:
        if m['T_nm'] >= T_calc:
            rec = m
            break
    
    result = {
        'power_kw': power_kw,
        'speed_rpm': rpm,
        'actual_torque_nm': round(T, 2),
        'calculated_torque_nm': round(T_calc, 2),
        'safety_factor': safety,
    }
    
    if rec:
        result['recommended_model'] = rec['model']
        result['rated_torque_nm'] = rec['T_nm']
        result['max_speed_rpm'] = rec['max_rpm']
        result['shaft_diameter_range_mm'] = rec['d_mm']
        result['is_safe'] = True
    else:
        result['recommended_model'] = '超出标准系列，需定制'
        result['is_safe'] = False
    
    return result


def coupling_universal(power_kw, rpm, angle_deg):
    """
    万向联轴器计算
    
    参数:
        power_kw: 传递功率 (kW)
        rpm: 转速
        angle_deg: 轴间夹角 (度)
    """
    T = 9550 * power_kw / rpm  # N·m
    beta = math.radians(angle_deg)
    
    # 速度波动率
    speed_fluctuation = 1 / math.cos(beta) - math.cos(beta)
    
    # 效率（粗略）
    eff = 1 - 0.02 * angle_deg / 10  # 每10°约2%损失
    eff = max(eff, 0.85)
    
    # 当量扭矩
    T_eq = T / math.cos(beta)
    
    return {
        'power_kw': power_kw,
        'speed_rpm': rpm,
        'angle_deg': angle_deg,
        'torque_nm': round(T, 2),
        'equivalent_torque_nm': round(T_eq, 2),
        'speed_fluctuation': round(speed_fluctuation * 100, 1),
        'efficiency': round(eff, 3),
        'note': '万向联轴器单节有速度波动，双节可抵消',
    }


# ============ O型圈 ============

ORING_GROOVE = {
    '1.8': {'groove_depth': 1.3, 'groove_width': 2.4, 'compression': 0.28},
    '1.9': {'groove_depth': 1.4, 'groove_width': 2.6, 'compression': 0.26},
    '2.0': {'groove_depth': 1.5, 'groove_width': 2.8, 'compression': 0.25},
    '2.4': {'groove_depth': 1.8, 'groove_width': 3.2, 'compression': 0.25},
    '2.5': {'groove_depth': 1.9, 'groove_width': 3.4, 'compression': 0.24},
    '2.6': {'groove_depth': 2.0, 'groove_width': 3.6, 'compression': 0.23},
    '3.0': {'groove_depth': 2.3, 'groove_width': 4.0, 'compression': 0.23},
    '3.1': {'groove_depth': 2.4, 'groove_width': 4.2, 'compression': 0.23},
    '3.5': {'groove_depth': 2.7, 'groove_width': 4.8, 'compression': 0.23},
    '4.0': {'groove_depth': 3.1, 'groove_width': 5.4, 'compression': 0.23},
    '4.5': {'groove_depth': 3.5, 'groove_width': 6.0, 'compression': 0.22},
    '5.0': {'groove_depth': 3.9, 'groove_width': 6.8, 'compression': 0.22},
    '5.5': {'groove_depth': 4.3, 'groove_width': 7.4, 'compression': 0.22},
    '6.0': {'groove_depth': 4.7, 'groove_width': 8.0, 'compression': 0.22},
    '7.0': {'groove_depth': 5.5, 'groove_width': 9.2, 'compression': 0.21},
}


def oring_groove(section_diam_mm):
    """
    O型圈沟槽尺寸推荐
    
    参数:
        section_diam_mm: O型圈截面直径 (mm)
    """
    key = str(section_diam_mm)
    if key in ORING_GROOVE:
        g = ORING_GROOVE[key]
        return {
            'oring_section_diameter_mm': section_diam_mm,
            'groove_depth_mm': g['groove_depth'],
            'groove_width_mm': g['groove_width'],
            'compression_ratio': g['compression'],
            'compression_mm': round(section_diam_mm * g['compression'], 2),
            'note': '用于静密封（端面密封）',
        }
    else:
        # 近似计算
        depth = section_diam_mm * 0.75
        width = section_diam_mm * 1.4
        return {
            'oring_section_diameter_mm': section_diam_mm,
            'groove_depth_mm': round(depth, 1),
            'groove_width_mm': round(width, 1),
            'compression_ratio': 0.25,
            'compression_mm': round(section_diam_mm * 0.25, 2),
            'note': '近似值，建议查标准',
        }


# ============ 圆弧齿同步带 HTD ============

HTD_BELTS = {
    '3M':  {'pitch': 3, 'height': 2.4, 'min_teeth': 10},
    '5M':  {'pitch': 5, 'height': 3.8, 'min_teeth': 14},
    '8M':  {'pitch': 8, 'height': 6.0, 'min_teeth': 22},
    '14M': {'pitch': 14, 'height': 10.0, 'min_teeth': 28},
    '20M': {'pitch': 20, 'height': 13.0, 'min_teeth': 34},
}


def htd_synchronous_belt(belt_type, power_kw, n1_rpm, ratio, z1=None, width_mm=None):
    """
    HTD圆弧齿同步带计算
    
    参数:
        belt_type: 带型 (3M/5M/8M/14M/20M)
        power_kw: 功率 (kW)
        n1_rpm: 小带轮转速
        ratio: 传动比
        z1: 小带轮齿数
        width_mm: 带宽
    """
    belt = HTD_BELTS.get(belt_type.upper())
    if not belt:
        return {'error': f'未知带型: {belt_type}，可选: 3M,5M,8M,14M,20M'}
    
    pb = belt['pitch']
    
    if z1 is None:
        z1 = max(belt['min_teeth'], int(30 * power_kw**0.3 / pb**0.4))
    z2 = round(z1 * ratio)
    
    d1 = z1 * pb / math.pi
    d2 = z2 * pb / math.pi
    v = math.pi * d1 * n1_rpm / 60000
    
    # 额定功率近似
    T_rated = 0.4 * pb * 10  # 参考扭矩
    P_rated = T_rated * n1_rpm / 9550 * (z1 / belt['min_teeth'])
    
    return {
        'belt_type': belt_type.upper(),
        'pitch_mm': pb,
        'belt_height_mm': belt['height'],
        'small_pulley_teeth': z1,
        'large_pulley_teeth': z2,
        'small_pulley_diameter_mm': round(d1, 2),
        'large_pulley_diameter_mm': round(d2, 2),
        'belt_speed_mps': round(v, 2),
        'rated_power_kw': round(P_rated, 3),
        'transmission_ratio': round(ratio, 3),
        'note': f'HTD圆弧齿，推荐带宽: {width_mm or "按功率查表"} mm',
    }


# ============ 电机常识 ============

MOTOR_KNOWLEDGE = {
    '同步转速': {
        'formula': 'n = 60f/p',
        'desc': 'n=同步转速(rpm), f=电源频率(Hz), p=极对数',
        'table': {
            '2极(50Hz)': 3000, '4极(50Hz)': 1500, '6极(50Hz)': 1000, '8极(50Hz)': 750,
            '2极(60Hz)': 3600, '4极(60Hz)': 1800, '6极(60Hz)': 1200, '8极(60Hz)': 900,
        }
    },
    '功率-扭矩关系': {
        'formula': 'T = 9550 × P / n',
        'desc': 'T=扭矩(N·m), P=功率(kW), n=转速(rpm)',
        'example': '5.5kW 4极电机 → T = 9550×5.5/1500 = 35.0 N·m',
    },
    '额定电流估算': {
        'formula': 'I ≈ P × 2 (380V三相异步电机)',
        'desc': '粗略估算：每kW约2A (380V), 每kW约4.5A (220V)',
        'example': '11kW/380V → I ≈ 22A',
    },
    '变频器选型': {
        'desc': '变频器额定电流 ≥ 电机额定电流 × 1.1',
        'example': '11kW/22A电机 → 变频器 ≥ 24.2A，选25A等级',
    },
}


def motor_sync_speed(poles=4, freq=50):
    """同步转速计算 n = 60f/p"""
    p = poles / 2
    n = 60 * freq / p
    return {
        'poles': poles,
        'frequency_hz': freq,
        'sync_speed_rpm': round(n),
        'slip_speed_rpm': round(n * 0.97),  # 异步电机额定转速≈同步转速×0.97
        'formula': f'n = 60 × {freq} / {poles//2} = {round(n)} rpm',
    }


def motor_torque(power_kw, rpm=None, poles=4, freq=50):
    """电机扭矩计算"""
    if rpm is None:
        n_sync = 60 * freq / (poles / 2)
        rpm = n_sync * 0.97
    T = 9550 * power_kw / rpm
    return {
        'power_kw': power_kw,
        'speed_rpm': round(rpm),
        'torque_nm': round(T, 2),
        'formula': f'T = 9550 × {power_kw} / {round(rpm)} = {round(T, 2)} N·m',
    }


def motor_current_estimate(power_kw, voltage=380):
    """电机额定电流估算"""
    if voltage >= 380:
        I = power_kw * 2
    else:
        I = power_kw * 4.5
    return {
        'power_kw': power_kw,
        'voltage_v': voltage,
        'estimated_current_a': round(I, 1),
        'formula': f'I ≈ {power_kw} × {"2" if voltage >= 380 else "4.5"} = {round(I, 1)} A',
        'note': '粗略估算，实际以铭牌为准',
    }
