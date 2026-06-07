"""
梁的弯矩/挠度/转角计算模块
参考：材料力学(刘鸿文)，机械设计手册(成大先)第16篇
"""
import math


# 截面惯性矩预设
def beam_section_inertia(shape, **dims):
    """
    计算截面惯性矩 I (mm⁴) 和截面模量 W (mm³)
    
    参数:
        shape: 
            'circle' - 圆形 {d}
            'hollow_circle' - 空心圆 {D, d}
            'rect' - 矩形 {b, h}
            'hollow_rect' - 空心矩形 {B, H, b, h}
            'i_beam' - 工字钢简化 {B, H, t, tw} 翼缘宽B, 总高H, 翼缘厚t, 腹板厚tw
            'channel' - 槽钢简化 {B, H, t, tw} 腹板高H, 翼缘宽B, 翼缘厚t, 腹板厚tw
    """
    shape = shape.lower()

    if shape == 'circle':
        d = dims['d']
        I = math.pi * d**4 / 64
        W = math.pi * d**3 / 32
        return {'I_mm4': round(I, 2), 'W_mm3': round(W, 2)}

    elif shape == 'hollow_circle':
        D = dims['D']
        d = dims['d']
        I = math.pi * (D**4 - d**4) / 64
        W = 2 * I / D if D > 0 else 0
        return {'I_mm4': round(I, 2), 'W_mm3': round(W, 2)}

    elif shape == 'rect':
        b = dims['b']
        h = dims['h']
        I = b * h**3 / 12
        W = b * h**2 / 6
        return {'I_mm4': round(I, 2), 'W_mm3': round(W, 2)}

    elif shape == 'hollow_rect':
        B = dims['B']
        H = dims['H']
        b = dims['b']
        h = dims['h']
        I = (B * H**3 - b * h**3) / 12
        W = 2 * I / H if H > 0 else 0
        return {'I_mm4': round(I, 2), 'W_mm3': round(W, 2)}

    elif shape == 'i_beam':
        B, H = dims['B'], dims['H']
        t = dims.get('t', 0)
        tw = dims.get('tw', t)
        hw = H - 2 * t
        # 平行轴定理
        I_flange = 2 * (B * t**3 / 12 + B * t * (H/2 - t/2)**2)
        I_web = tw * hw**3 / 12
        I = I_flange + I_web
        W = 2 * I / H if H > 0 else 0
        return {'I_mm4': round(I, 2), 'W_mm3': round(W, 2)}

    elif shape == 'channel':
        # 槽钢简化：三矩形（腹板 + 两个翼缘）
        # 腹板高H, 翼缘宽B, 翼缘厚t, 腹板厚tw
        B, H = dims['B'], dims['H']
        t = dims.get('t', 0)
        tw = dims.get('tw', t)
        hw = H  # 腹板高度
        # 形心 (从腹板外侧到形心的距离)
        A_flange = B * t
        A_web = hw * tw
        A_total = 2 * A_flange + A_web
        x_c = (2 * A_flange * (B/2) + A_web * tw/2) / A_total if A_total > 0 else 0
        # 惯性矩（对形心轴）
        I_flange_self = 2 * (B * t**3 / 12)
        I_flange_shift = 2 * A_flange * (x_c - B/2)**2
        I_web_self = tw * hw**3 / 12
        I_web_shift = A_web * (x_c - tw/2)**2
        I = I_flange_self + I_flange_shift + I_web_self + I_web_shift
        W = I / (B - x_c) if (B - x_c) > 0 else 0
        return {'I_mm4': round(I, 2), 'W_mm3': round(W, 2), 'centroid_x_mm': round(x_c, 2)}

    else:
        return {'error': f'未知截面类型: {shape}'}


def calc_beam(beam_type=None, L=None, loads=None, E=None, I=None):
    """
    梁的弯矩/挠度/转角计算
    
    参数:
        beam_type: 'simply_supported' | 'cantilever' | 'fixed_both'
        L: 梁长度 mm
        loads: 载荷列表，每项为 dict，包含:
            - type: 'point' 集中力, 'uniform' 均布载荷, 'moment' 弯矩
            - 对于 point:  {'type': 'point', 'F': N, 'a': mm}
            - 对于 uniform: {'type': 'uniform', 'q': N/mm, 'a': mm, 'b': mm}
            - 对于 moment:  {'type': 'moment', 'M': N·mm, 'a': mm}
        E: 弹性模量 MPa
        I: 截面惯性矩 mm⁴
    
    返回: M_max, V_max, delta_max, theta_max
    """
    if not L or not loads or not E or not I:
        return {'error': '请提供 beam_type, L(mm), loads, E(MPa), I(mm⁴)'}

    beam_type = (beam_type or '').lower()
    EI = E * I

    M_max = 0  # 最大弯矩 N·mm
    V_max = 0  # 最大剪力 N
    delta_max = 0  # 最大挠度 mm
    theta_max = 0  # 最大转角 rad
    details = []

    def sign(x):
        return 1 if x >= 0 else -1

    if beam_type == 'simply_supported':
        # 简支梁
        for ld in loads:
            lt = ld.get('type', '')
            if lt == 'point':
                F = ld.get('F', 0)
                a = ld.get('a', 0)
                b = L - a
                # 支反力
                Rb = F * a / L if L > 0 else 0
                Ra = F - Rb
                # 弯矩
                if a <= b:
                    M_x = Ra * a
                else:
                    M_x = Rb * b
                M_max = max(M_max, M_x)
                V_max = max(V_max, abs(Ra), abs(Rb))
                # 挠度（载荷点）
                delta = F * a * b * (L**2 - a**2 - b**2) / (6 * EI * L) if EI > 0 else 0
                delta_max = max(delta_max, abs(delta))
                theta_a = F * b * (L**2 - b**2) / (6 * EI * L) if EI > 0 else 0
                theta_max = max(theta_max, abs(theta_a))
                details.append({
                    'type': '集中力', 'F_N': F, 'position_a_mm': a,
                    'M_at_pos_N_mm': round(M_x, 2), 'deflection_at_pos_mm': round(delta, 4),
                    'theta_a_rad': round(theta_a, 6),
                })

            elif lt == 'uniform':
                q = ld.get('q', 0)
                a = ld.get('a', 0)
                b = ld.get('b', L)
                c = b - a  # 载荷段长度
                # 等效集中力位置
                x_mid = (a + b) / 2
                Rq = q * c
                Rb = Rq * x_mid / L if L > 0 else 0
                Ra = Rq - Rb
                M_x = Ra * x_mid - q * c**2 / 8 if x_mid >= a else Ra * x_mid
                M_max = max(M_max, abs(M_x))
                V_max = max(V_max, abs(Ra), abs(Rb))
                delta = q * c / (24 * EI) * (L**3 - 2*L*c**2 + c**3) / L if EI > 0 and L > 0 else 0
                delta_max = max(delta_max, abs(delta))
                details.append({
                    'type': '均布载荷', 'q_N_per_mm': q,
                    'range': f'{a}~{b} mm', 'M_max_N_mm': round(M_x, 2),
                    'deflection_approx_mm': round(delta, 4),
                })

            elif lt == 'moment':
                M0 = ld.get('M', 0)
                a = ld.get('a', 0)
                b = L - a
                Ra = M0 / L if L > 0 else 0
                M_left = Ra * a
                M_right = Ra * a - M0 if a < L else 0
                M_max = max(M_max, abs(M_left), abs(M_right))
                details.append({
                    'type': '弯矩', 'M_N_mm': M0, 'position_a_mm': a,
                    'M_left_N_mm': round(M_left, 2), 'M_right_N_mm': round(M_right, 2),
                })

    elif beam_type == 'cantilever':
        # 悬臂梁（固定端x=0，自由端x=L）
        for ld in loads:
            lt = ld.get('type', '')
            if lt == 'point':
                F = ld.get('F', 0)
                a = ld.get('a', L)
                V = abs(F)
                M_fixed = F * a  # 固定端弯矩
                M_max = max(M_max, M_fixed)
                V_max = max(V_max, V)
                # 自由端挠度
                delta = F * a**2 * (3*L - a) / (6 * EI) if EI > 0 else 0
                delta_max = max(delta_max, abs(delta))
                details.append({
                    'type': '集中力', 'F_N': F, 'position_a_mm': a,
                    'M_fixed_N_mm': round(M_fixed, 2), 'tip_deflection_mm': round(delta, 4),
                })

            elif lt == 'uniform':
                q = ld.get('q', 0)
                a = ld.get('a', 0)
                b = ld.get('b', L)
                c = b - a
                V = q * c
                x_cg = a + c / 2
                M_fixed = q * c * x_cg if L > 0 else 0
                M_max = max(M_max, M_fixed)
                V_max = max(V_max, V)
                # 悬臂梁均布载荷自由端挠度 (从固定端 x=0 到位置 b 的均布载荷 q)
                # 标准公式: delta = q*b^2*(6*L^2 - 4*L*b + b^2) / (24*E*I)
                # 其中 b 为载荷段长度, L 为梁全长
                delta = q * c**2 * (6*L**2 - 4*L*c + c**2) / (24 * EI) if EI > 0 else 0
                delta_max = max(delta_max, abs(delta))
                details.append({
                    'type': '均布载荷', 'q_N_per_mm': q,
                    'range': f'{a}~{b} mm', 'M_fixed_N_mm': round(M_fixed, 2),
                })

            elif lt == 'moment':
                M0 = ld.get('M', 0)
                a = ld.get('a', 0)
                M_max = max(M_max, abs(M0))
                delta = M0 * L**2 / (2 * EI) if EI > 0 else 0
                delta_max = max(delta_max, abs(delta))
                details.append({
                    'type': '弯矩', 'M_N_mm': M0, 'position_a_mm': a,
                    'tip_deflection_mm': round(delta, 4),
                })

    elif beam_type == 'fixed_both':
        # 两端固定梁
        for ld in loads:
            lt = ld.get('type', '')
            if lt == 'point':
                F = ld.get('F', 0)
                a = ld.get('a', 0)
                b = L - a
                V = abs(F)
                # 固定端弯矩
                M_a = F * a * b**2 / L**2 if L > 0 else 0
                M_b = F * a**2 * b / L**2 if L > 0 else 0
                M_x = F * a * b**2 / L**2  # 简化计算
                M_max = max(M_max, abs(M_a), abs(M_b), abs(M_x))
                V_max = max(V_max, V)
                delta = F * a**3 * b**3 / (3 * EI * L**3) if EI > 0 and L > 0 else 0
                delta_max = max(delta_max, abs(delta))
                details.append({
                    'type': '集中力', 'F_N': F, 'position_a_mm': a,
                    'M_A_N_mm': round(M_a, 2), 'M_B_N_mm': round(M_b, 2),
                    'deflection_at_pos_mm': round(delta, 4),
                })

            elif lt == 'uniform':
                q = ld.get('q', 0)
                a = ld.get('a', 0)
                b = ld.get('b', L)
                c = b - a
                V = q * c
                M_end = q * L**2 / 12 if L > 0 else 0
                Mspan = q * L**2 / 24 if L > 0 else 0
                M_max = max(M_max, abs(M_end), abs(Mspan))
                V_max = max(V_max, V)
                delta = q * L**4 / (384 * EI) if EI > 0 else 0
                delta_max = max(delta_max, abs(delta))
                details.append({
                    'type': '均布载荷', 'q_N_per_mm': q,
                    'range': f'{a}~{b} mm', 'M_end_N_mm': round(M_end, 2),
                    'M_span_N_mm': round(Mspan, 2), 'max_deflection_mm': round(delta, 4),
                })

    else:
        return {'error': f'未知梁类型: {beam_type}。支持: simply_supported, cantilever, fixed_both'}

    return {
        'beam_type': beam_type,
        'length_mm': L,
        'E_MPa': E,
        'I_mm4': I,
        'EI_N_mm2': round(EI, 2),
        'M_max_N_mm': round(M_max, 2),
        'V_max_N': round(V_max, 2),
        'delta_max_mm': round(abs(delta_max), 6),
        'theta_max_rad': round(abs(theta_max), 6),
        'theta_max_deg': round(abs(theta_max) * 180 / math.pi, 4) if theta_max else 0,
        'load_details': details,
        'formula': 'M_max, V_max, δ_max, θ_max 按载荷叠加计算',
        'reference': '材料力学(刘鸿文) §5, §6',
    }
