"""
焊接计算扩展模块
参考：GB 50017-2017 钢结构设计标准, AWS D1.1, 机械设计手册(成大先)第16篇 §5
"""
import math


def calc_fillet_weld_stress(F=None, M=None, h=None, Lw=None, load_type='tension'):
    """
    角焊缝应力校核
    
    受拉/受剪: τ = F / (0.707·h·ΣLw)
    弯扭组合: σ_w = √((σ_F + σ_M)² + τ_T²)
    
    参数:
        F: 载荷 N
        M: 弯矩 N·mm（弯扭组合时）
        h: 焊脚尺寸 mm (角焊缝的直角边)
        Lw: 焊缝总有效长度 mm
        load_type: 'tension'|'shear'|'combined'（弯扭组合）
    """
    if not h or not Lw:
        return {'error': '请提供焊脚尺寸 h(mm) 和焊缝有效长度 Lw(mm)'}

    throat = 0.707 * h
    A_weld = throat * Lw  # 有效面积 mm²

    result = {
        'fillet_leg_h_mm': h,
        'throat_thickness_mm': round(throat, 2),
        'weld_length_Lw_mm': Lw,
        'effective_area_mm2': round(A_weld, 2),
    }

    if load_type == 'tension' or load_type == 'shear':
        if F is None:
            return {'error': f'{load_type} 模式需要提供载荷 F(N)'}
        tau = F / A_weld if A_weld > 0 else 0
        result['force_N'] = F
        result['load_type'] = load_type
        result['shear_stress_tau_MPa'] = round(tau, 2)
        result['formula'] = 'τ = F / (0.707·h·ΣLw)'

    elif load_type == 'combined':
        if F is None or M is None:
            return {'error': '弯扭组合模式需要提供 F(N) 和 M(N·mm)'}
        # 正应力（假设力垂直于焊缝方向）
        sigma_F = F / A_weld if A_weld > 0 else 0
        # 弯曲应力
        W_weld = throat * Lw**2 / 6  # 焊缝抗弯截面系数
        sigma_M = M / W_weld if W_weld > 0 else 0
        # 合成应力
        sigma_combined = math.sqrt(sigma_F**2 + sigma_M**2)

        result['force_N'] = F
        result['moment_N_mm'] = M
        result['sigma_F_MPa'] = round(sigma_F, 2)
        result['sigma_M_MPa'] = round(sigma_M, 2)
        result['sigma_combined_MPa'] = round(sigma_combined, 2)
        result['formula'] = 'σ = √(σ_F² + σ_M²) [弯扭组合]'
        result['load_type'] = 'combined'

    return result


def calc_butt_weld_stress(F=None, M=None, t=None, Lw=None, load_type='tension'):
    """
    对接焊缝应力校核
    
    受拉: σ = F / (t·Lw)
    受弯: σ = 6M / (t·Lw²)
    弯拉组合: σ = F/(t·Lw) + 6M/(t·Lw²)
    
    参数:
        F: 轴向力 N
        M: 弯矩 N·mm
        t: 板厚 mm
        Lw: 焊缝宽度/长度 mm
        load_type: 'tension'|'bending'|'combined'
    """
    if not t or not Lw:
        return {'error': '请提供板厚 t(mm) 和焊缝宽度 Lw(mm)'}

    A_weld = t * Lw
    W_weld = t * Lw**2 / 6

    result = {
        'plate_thickness_t_mm': t,
        'weld_width_Lw_mm': Lw,
        'effective_area_mm2': round(A_weld, 2),
        'section_modulus_mm3': round(W_weld, 2),
    }

    if load_type == 'tension':
        if F is None:
            return {'error': '受拉模式需要提供轴向力 F(N)'}
        sigma = F / A_weld if A_weld > 0 else 0
        result['force_N'] = F
        result['sigma_MPa'] = round(sigma, 2)
        result['formula'] = 'σ = F / (t·Lw)'

    elif load_type == 'bending':
        if M is None:
            return {'error': '受弯模式需要提供弯矩 M(N·mm)'}
        sigma = M / W_weld if W_weld > 0 else 0
        result['moment_N_mm'] = M
        result['sigma_MPa'] = round(sigma, 2)
        result['formula'] = 'σ = 6M / (t·Lw²)'

    elif load_type == 'combined':
        if F is None or M is None:
            return {'error': '弯拉组合模式需要提供 F(N) 和 M(N·mm)'}
        sigma_F = F / A_weld if A_weld > 0 else 0
        sigma_M = M / W_weld if W_weld > 0 else 0
        sigma = sigma_F + sigma_M
        result['force_N'] = F
        result['moment_N_mm'] = M
        result['sigma_F_MPa'] = round(sigma_F, 2)
        result['sigma_M_MPa'] = round(sigma_M, 2)
        result['sigma_total_MPa'] = round(sigma, 2)
        result['formula'] = 'σ = F/(t·Lw) + 6M/(t·Lw²)'

    result['load_type'] = load_type
    result['reference'] = 'GB 50017-2017 / AWS D1.1'

    return result
