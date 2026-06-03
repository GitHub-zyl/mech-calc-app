"""
螺纹/紧固件计算模块
参考：机械设计常用计算表 - 螺纹中小径计算 / 公制螺纹
"""
import math

def metric_thread_basic(nominal_d, pitch):
    """
    公制螺纹基本尺寸计算 (ISO 68)
    
    参数:
        nominal_d: 公称直径 (mm)
        pitch: 螺距 (mm)
    
    返回: dict
    """
    H = 0.8660254 * pitch  # 原始三角形高度
    
    d2 = nominal_d - 0.649519 * pitch   # 中径
    d1 = nominal_d - 1.082532 * pitch   # 小径（外螺纹）
    D1 = nominal_d - 1.082532 * pitch   # 小径（内螺纹）
    D2 = nominal_d - 0.649519 * pitch   # 中径（内螺纹）
    D = nominal_d                       # 内螺纹大径
    
    return {
        'nominal_diameter': nominal_d,
        'pitch': pitch,
        'pitch_diameter': round(d2, 4),
        'minor_diameter_external': round(d1, 4),  # 外螺纹小径
        'minor_diameter_internal': round(D1, 4),  # 内螺纹小径
        'thread_height': round(H, 4),
        'tap_drill_diameter': round(D1 + 0.1, 3),  # 推荐的攻丝底孔直径
    }


def tap_drill_diameter(thread_spec):
    """
    攻丝底孔直径计算
    
    参数:
        thread_spec: 螺纹规格字符串，如 'M6', 'M8x1'
    
    返回: dict
    """
    import re
    m = re.match(r'M(\d+(?:\.\d+)?)(?:[xX](\d+(?:\.\d+)?))?$', thread_spec.strip().upper())
    if not m:
        return {'error': f'无法解析螺纹规格: {thread_spec}。格式示例: M6, M8x1'}
    
    d = float(m.group(1))
    p = float(m.group(2)) if m.group(2) else (0.8 if d <= 3 else (1.0 if d <= 6 else (1.25 if d <= 10 else (1.5 if d <= 16 else 2.0))))
    
    result = metric_thread_basic(d, p)
    drill = result['minor_diameter_internal']
    
    # 推荐底孔直径（按材料分类）
    return {
        'thread': thread_spec,
        'pitch': p,
        'theoretical_drill_mm': round(drill, 2),
        'drill_steel_castiron_mm': round(d - p, 2),         # 钢/铸铁：d-p
        'drill_stainless_mm': round(d - p * 1.05, 2),       # 不锈钢
        'drill_aluminum_mm': round(d - p * 0.95, 2),        # 铝
        'note': '实际加工请根据材料硬度适当调整'
    }


def bolt_preload_torque(d_mm, grade='8.8', mu=0.15):
    """
    螺栓预紧力与扭矩计算
    
    参数:
        d_mm: 螺纹公称直径 (mm)
        grade: 性能等级 (4.6, 4.8, 5.6, 5.8, 6.8, 8.8, 9.8, 10.9, 12.9)
        mu: 摩擦系数 (默认0.15)
    """
    grades = {
        '4.6': 240, '4.8': 320, '5.6': 300, '5.8': 400,
        '6.8': 480, '8.8': 640, '9.8': 720, '10.9': 940, '12.9': 1100
    }
    
    sigma_s = grades.get(grade, 640)
    As = 0.7854 * (d_mm - 0.9382 * 0.75)**2  # 应力面积近似
    Fp = (0.6 if grade in ('8.8', '9.8') else 0.7) * sigma_s * As / 1000  # kN
    T = 0.2 * Fp * d_mm  # 拧紧扭矩 N·m
    
    return {
        'diameter_mm': d_mm,
        'grade': grade,
        'yield_strength_mpa': sigma_s,
        'stress_area_mm2': round(As, 2),
        'preload_kN': round(Fp, 2),
        'tightening_torque_nm': round(T, 2),
        'friction_coefficient': mu,
    }
