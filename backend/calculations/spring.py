"""
弹簧刚度计算模块
参考：机械设计常用计算表 - 弹簧刚度计算大全
"""
import math

def coil_spring_compression(d, Dm, n, G=79000, material='弹簧钢'):
    """
    圆柱螺旋压缩弹簧计算
    
    参数:
        d: 弹簧线径 (mm)
        Dm: 弹簧中径 (mm)
        n: 有效圈数
        G: 切变模量 (MPa, 默认弹簧钢 79000)
        material: 材料名称
    
    返回: dict
    """
    if material == '弹簧钢':
        G = 79000
    elif material == '不锈钢':
        G = 73000
    elif material == '铜合金':
        G = 45000
    
    C = Dm / d                     # 旋绕比
    k = G * d**4 / (8 * Dm**3 * n) # 刚度 N/mm
    
    return {
        'wire_diameter': d,
        'mean_diameter': Dm,
        'active_coils': n,
        'spring_index': round(C, 2),
        'shear_modulus': G,
        'stiffness_n_per_mm': round(k, 4),
        'material': material,
    }


def coil_spring_tension(d, Dm, n, F0=0, G=79000):
    """
    圆柱螺旋拉伸弹簧计算
    """
    C = Dm / d
    k = G * d**4 / (8 * Dm**3 * n)
    
    return {
        'wire_diameter': d,
        'mean_diameter': Dm,
        'active_coils': n,
        'spring_index': round(C, 2),
        'stiffness_n_per_mm': round(k, 4),
        'initial_tension_n': F0,
    }


def coil_spring_stress(d, Dm, F, material='弹簧钢'):
    """
    弹簧应力校核
    
    参数:
        d: 线径 (mm)
        Dm: 中径 (mm)
        F: 工作载荷 (N)
    """
    C = Dm / d
    # 曲度系数
    K = (4*C - 1) / (4*C - 4) + 0.615 / C
    
    tau = 8 * K * F * Dm / (math.pi * d**3)  # 最大切应力 MPa
    
    materials = {
        '弹簧钢': {'allowable': 640, 'desc': '60Si2Mn 许用应力 640 MPa'},
        '不锈钢': {'allowable': 480, 'desc': '1Cr18Ni9 许用应力 480 MPa'},
        '铜合金': {'allowable': 300, 'desc': 'QSi3-1 许用应力 300 MPa'},
    }
    
    mat = materials.get(material, materials['弹簧钢'])
    safe = tau < mat['allowable']
    
    return {
        'max_shear_stress_mpa': round(tau, 2),
        'allowable_stress_mpa': mat['allowable'],
        'curvature_factor': round(K, 4),
        'is_safe': safe,
        'material_desc': mat['desc'],
        'safety_factor': round(mat['allowable'] / tau, 2) if tau > 0 else float('inf'),
    }


def spring_deflection(k, F):
    """
    弹簧变形量计算
    """
    if k <= 0:
        return {'error': '刚度必须大于0'}
    f = F / k
    return {
        'stiffness': k,
        'force': F,
        'deflection_mm': round(f, 2),
    }
