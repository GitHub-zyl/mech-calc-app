"""
冲裁 / 弯曲 / 冲压力计算模块
参考：机械设计常用计算表 - 总冲裁力 / V型U型弯曲力 / 剪切力
"""


def blanking_force(perimeter_mm, thickness_mm, shear_strength_mpa, k=1.3):
    """
    冲裁力计算    F = K · L · t · τ
    
    参数:
        perimeter_mm: 冲裁周边长度 (mm)
        thickness_mm: 材料厚度 (mm)
        shear_strength_mpa: 材料抗剪强度 (MPa)
        k: 修正系数，默认1.3
    """
    F = k * perimeter_mm * thickness_mm * shear_strength_mpa / 1000  # kN
    return {
        'blanking_force_kN': round(F, 2),
        'blanking_force_ton': round(F / 9.81, 2),
        'perimeter_mm': perimeter_mm,
        'thickness_mm': thickness_mm,
        'shear_strength_mpa': shear_strength_mpa,
        'factor_k': k,
        'formula': 'F = K · L · t · τ',
    }


def stripping_force(blanking_force_kN, material_type='steel'):
    """
    卸料力/推料力/顶件力计算
    
    参数:
        blanking_force_kN: 冲裁力 (kN)
        material_type: 材料类型 (steel/aluminum/copper)
    """
    # 系数表
    coeff = {
        'steel':   {'Kx': 0.04, 'Kt': 0.05, 'Kd': 0.06},  # noqa: E241
        'aluminum': {'Kx': 0.06, 'Kt': 0.055, 'Kd': 0.07},  # noqa: E241
        'copper':  {'Kx': 0.05, 'Kt': 0.04, 'Kd': 0.05},  # noqa: E241
    }
    c = coeff.get(material_type, coeff['steel'])
    
    Fx = c['Kx'] * blanking_force_kN  # 卸料力
    Ft = c['Kt'] * blanking_force_kN  # 推料力
    Fd = c['Kd'] * blanking_force_kN  # 顶件力
    
    return {
        'material': material_type,
        'stripping_force_kN': round(Fx, 2),
        'ejecting_force_kN': round(Ft, 2),
        'pushing_force_kN': round(Fd, 2),
        'total_force_kN': round(Fx + Ft + Fd + blanking_force_kN, 2),
        'total_force_ton': round((Fx + Ft + Fd + blanking_force_kN) / 9.81, 2),
    }


def v_bending_force(width_mm, thickness_mm, tensile_strength_mpa, die_opening_mm, k=1.33):
    """
    V型弯曲力计算    F = k · b · t² · σb / (w)
    
    参数:
        width_mm: 弯曲件宽度 (mm)
        thickness_mm: 材料厚度 (mm)
        tensile_strength_mpa: 抗拉强度 (MPa)
        die_opening_mm: 凹模开口宽度 (mm)
        k: 系数，V型一般取1.33
    """
    F = k * width_mm * thickness_mm**2 * tensile_strength_mpa / (die_opening_mm * 1000)  # kN
    
    return {
        'bending_type': 'V型弯曲',
        'bending_force_kN': round(F, 2),
        'bending_force_ton': round(F / 9.81, 2),
        'width_mm': width_mm,
        'thickness_mm': thickness_mm,
        'tensile_strength_mpa': tensile_strength_mpa,
        'die_opening_mm': die_opening_mm,
    }


def u_bending_force(width_mm, thickness_mm, tensile_strength_mpa, die_opening_mm):
    """
    U型弯曲力计算
    """
    # U型弯曲力约为V型的2倍
    v_result = v_bending_force(width_mm, thickness_mm, tensile_strength_mpa, die_opening_mm, k=1.33)
    F_u = v_result['bending_force_kN'] * 2
    
    return {
        'bending_type': 'U型弯曲',
        'bending_force_kN': round(F_u, 2),
        'bending_force_ton': round(F_u / 9.81, 2),
        'width_mm': width_mm,
        'thickness_mm': thickness_mm,
        'tensile_strength_mpa': tensile_strength_mpa,
        'die_opening_mm': die_opening_mm,
        'note': 'U型弯曲力约为V型的2倍',
    }


def embossing_force(area_mm2, tensile_strength_mpa):
    """
    压印成型力计算    F ≈ A · σb
    
    参数:
        area_mm2: 压印面积 (mm²)
        tensile_strength_mpa: 材料抗拉强度 (MPa)
    """
    F = area_mm2 * tensile_strength_mpa / 1000  # kN
    return {
        'embossing_force_kN': round(F, 2),
        'embossing_force_ton': round(F / 9.81, 2),
        'area_mm2': area_mm2,
        'tensile_strength_mpa': tensile_strength_mpa,
    }


def shear_force(area_mm2, shear_strength_mpa):
    """
    剪切力计算
    
    参数:
        area_mm2: 剪切面积 (mm²)
        shear_strength_mpa: 抗剪强度 (MPa)
    """
    F = area_mm2 * shear_strength_mpa / 1000  # kN
    return {
        'shear_force_kN': round(F, 2),
        'shear_force_ton': round(F / 9.81, 2),
        'shear_area_mm2': area_mm2,
        'shear_strength_mpa': shear_strength_mpa,
    }
