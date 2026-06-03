"""
材料力学计算模块
参考：机械设计常用计算表 - 惯性距计算 / 立柱计算 / 稳定性系数 / 焊缝 / 键 / 销 / 过盈
"""
import math

# ============ 截面惯性矩 / 抗弯截面系数 ============

def section_properties(shape, params):
    """
    常用截面惯性矩 I 和抗弯截面系数 W
    
    参数:
        shape: 截面形状
            'rect': 矩形 {b, h}
            'circle': 实心圆 {d}
            'tube': 空心圆管 {D, d}
            'square_tube': 方管 {B, H, b, h} 外B×H, 内b×h
            'i_beam': 工字钢简化 {B, H, t, tw} 
            't_section': T型截面 {B, H, t, tw}
        params: dict of dimensions (mm)
    
    返回: 面积A, 惯性矩I, 截面系数W, 回转半径i
    """
    shape = shape.lower()
    
    if shape == 'rect':
        b = params['b']
        h = params['h']
        A = b * h
        I = b * h**3 / 12
        W = b * h**2 / 6
        i = math.sqrt(I / A) if A > 0 else 0
        desc = f'矩形 {b}×{h}'
        
    elif shape == 'circle':
        d = params['d']
        A = math.pi * d**2 / 4
        I = math.pi * d**4 / 64
        W = math.pi * d**3 / 32
        i = d / 4
        desc = f'实心圆 φ{d}'
    
    elif shape == 'tube':
        D = params['D']
        d = params['d']
        A = math.pi * (D**2 - d**2) / 4
        I = math.pi * (D**4 - d**4) / 64
        W = 2 * I / D if D > 0 else 0
        i = math.sqrt(I / A) if A > 0 else 0
        desc = f'空心圆 φ{D}/φ{d}'
        
    elif shape == 'square_tube':
        B, H = params['B'], params['H']
        b, h = params['b'], params['h']
        A = B * H - b * h
        I = (B * H**3 - b * h**3) / 12
        W = 2 * I / H if H > 0 else 0
        i = math.sqrt(I / A) if A > 0 else 0
        desc = f'方管 {B}×{H} (壁厚{min(H-h, B-b)/2:.1f})'
    
    elif shape == 'i_beam':
        # 简化工字钢：翼缘宽B，总高H，翼缘厚t，腹板厚tw
        B, H = params['B'], params['H']
        t = params.get('t', 0)
        tw = params.get('tw', t)
        hw = H - 2 * t  # 腹板高度
        A = 2 * B * t + hw * tw
        # 平行轴定理
        I_flange = 2 * (B * t**3 / 12 + B * t * (H/2 - t/2)**2)
        I_web = tw * hw**3 / 12
        I = I_flange + I_web
        W = 2 * I / H if H > 0 else 0
        i = math.sqrt(I / A) if A > 0 else 0
        desc = f'工字钢 H{H}×B{B}×t{t}×tw{tw}'
    
    elif shape == 't_section':
        B, H = params['B'], params['H']
        t = params.get('t', 0)
        tw = params.get('tw', t)
        # 计算形心
        A1 = B * t
        A2 = (H - t) * tw
        A = A1 + A2
        yc = (A1 * t/2 + A2 * (t + (H-t)/2)) / A if A > 0 else 0
        I1 = B * t**3 / 12 + A1 * (yc - t/2)**2
        I2 = tw * (H-t)**3 / 12 + A2 * (yc - t - (H-t)/2)**2
        I = I1 + I2
        W_top = I / yc if yc > 0 else 0
        W_bot = I / (H - yc) if H > yc else 0
        W = min(W_top, W_bot)
        i = math.sqrt(I / A) if A > 0 else 0
        desc = f'T型 {B}×{H}×t{t}×tw{tw}'
    else:
        return {'error': f'未知截面: {shape}'}
    
    return {
        'section': desc,
        'area_mm2': round(A, 2),
        'inertia_mm4': round(I, 2),
        'section_modulus_mm3': round(W, 4),
        'radius_gyration_mm': round(i, 4),
    }


# ============ 立柱 / 压杆稳定 ============

def column_buckling(E_mpa, L_mm, I_mm4, A_mm2, mu=1.0, sigma_s_mpa=235):
    """
    立柱/压杆稳定性计算 (欧拉公式)
    
    参数:
        E_mpa: 弹性模量 (MPa)
        L_mm: 杆长 (mm)
        I_mm4: 截面惯性矩 (mm⁴)
        A_mm2: 截面积 (mm²)
        mu: 长度系数 (1=两端铰支, 0.5=两端固定, 0.7=一端固定一端铰支, 2=一端固定一端自由)
        sigma_s_mpa: 屈服强度 (MPa)
    """
    i = math.sqrt(I_mm4 / A_mm2) if A_mm2 > 0 else 0  # 回转半径
    lam = L_mm / i if i > 0 else 0  # 长细比
    
    # 欧拉临界力
    Pcr = math.pi**2 * E_mpa * I_mm4 / (mu * L_mm)**2 if L_mm > 0 else 0
    sigma_cr = Pcr / A_mm2 if A_mm2 > 0 else 0  # 临界应力
    
    # 判断破坏模式
    lam_p = math.pi * math.sqrt(E_mpa / sigma_s_mpa)  # 比例极限长细比
    if lam > lam_p:
        failure_mode = '弹性屈曲 (欧拉)'
        sigma_cr_actual = sigma_cr
    else:
        failure_mode = '弹塑性屈曲'
        # 简化 Johnson 公式
        sigma_cr_actual = sigma_s_mpa * (1 - sigma_s_mpa * lam**2 / (4 * math.pi**2 * E_mpa))
    
    return {
        'slenderness_ratio': round(lam, 2),
        'limit_slenderness': round(lam_p, 2),
        'euler_critical_force_N': round(Pcr, 1),
        'euler_critical_stress_mpa': round(sigma_cr, 2),
        'actual_critical_stress_mpa': round(sigma_cr_actual, 2) if sigma_cr_actual else 0,
        'failure_mode': failure_mode,
    }


def column_stability_check(F_N, A_mm2, E_mpa, L_mm, I_mm4, mu=1.0, sigma_s_mpa=235, safety=2.0):
    """
    立柱稳定性校核 (完整流程)
    
    返回: 应力校核 + 稳定性校核
    """
    i = math.sqrt(I_mm4 / A_mm2) if A_mm2 > 0 else 0
    lam = L_mm / i if i > 0 else 0
    
    sigma = F_N / A_mm2 if A_mm2 > 0 else 0  # 工作应力
    Pcr = math.pi**2 * E_mpa * I_mm4 / (mu * L_mm)**2 if L_mm > 0 else 0
    n_stable = Pcr / F_N if F_N > 0 else 0  # 稳定安全系数
    
    # 许用稳定应力
    sigma_permissible = Pcr / (A_mm2 * safety) if A_mm2 > 0 else 0
    
    return {
        'working_stress_mpa': round(sigma, 2),
        'euler_critical_force_kN': round(Pcr / 1000, 2),
        'stability_safety_factor': round(n_stable, 3),
        'required_safety_factor': safety,
        'is_safe': n_stable >= safety,
        'slenderness_ratio': round(lam, 2),
        'failure_mode': '屈曲' if lam > 80 else '强度破坏',
    }


# ============ 焊缝强度 ============

def weld_fillet_stress(F_N, weld_leg_mm, weld_length_mm, num_welds=2):
    """
    角焊缝强度校核  τ = F / (0.707·K·l·n)
    
    参数:
        F_N: 载荷 (N)
        weld_leg_mm: 焊脚尺寸 (mm)
        weld_length_mm: 焊缝长度 (mm)
        num_welds: 焊缝数量
    """
    throat = 0.707 * weld_leg_mm  # 喉部厚度
    A_weld = throat * weld_length_mm * num_welds
    tau = F_N / A_weld if A_weld > 0 else 0
    
    return {
        'throat_thickness_mm': round(throat, 2),
        'effective_area_mm2': round(A_weld, 2),
        'shear_stress_mpa': round(tau, 2),
        'weld_leg_mm': weld_leg_mm,
        'weld_length_mm': weld_length_mm,
        'num_welds': num_welds,
    }


def weld_butt_stress(F_N, plate_thickness_mm, weld_width_mm):
    """
    对接焊缝强度  σ = F / (t·w)
    """
    A = plate_thickness_mm * weld_width_mm
    sigma = F_N / A if A > 0 else 0
    return {
        'effective_area_mm2': round(A, 2),
        'tensile_stress_mpa': round(sigma, 2),
        'plate_thickness_mm': plate_thickness_mm,
        'weld_width_mm': weld_width_mm,
    }


# ============ 键强度 ============

def key_strength(T_Nmm, shaft_diameter_mm, key_width_mm, key_height_mm, key_length_mm):
    """
    平键强度校核
    
    参数:
        T_Nmm: 传递扭矩 (N·mm)
        shaft_diameter_mm: 轴径 (mm)
        key_width_mm: 键宽 b (mm)
        key_height_mm: 键高 h (mm)
        key_length_mm: 键长 L (mm)
    """
    d = shaft_diameter_mm
    h = key_height_mm
    l = key_length_mm
    b = key_width_mm
    t = h / 2  # 键的接触高度 (近似)
    
    # 剪切应力 τ = 2T / (d·b·l)
    tau = 2 * T_Nmm / (d * b * l) if all([d, b, l]) else 0
    # 挤压应力 σp = 4T / (d·h·l)
    sigma_p = 4 * T_Nmm / (d * h * l) if all([d, h, l]) else 0
    
    return {
        'torque_Nm': round(T_Nmm / 1000, 2),
        'shaft_diameter_mm': shaft_diameter_mm,
        'key_size': f'{key_width_mm}×{key_height_mm}×{key_length_mm}',
        'shear_stress_mpa': round(tau, 2),
        'bearing_stress_mpa': round(sigma_p, 2),
        'formula_shear': 'τ = 2T/(d·b·l)',
        'formula_bearing': 'σp = 4T/(d·h·l)',
    }


# ============ 销强度 ============

def pin_strength(F_N, pin_diameter_mm, num_pins=1):
    """
    圆柱销剪切强度  τ = 4F / (n·π·d²)
    
    参数:
        F_N: 横向载荷 (N)
        pin_diameter_mm: 销直径 (mm)
        num_pins: 销数量
    """
    A = num_pins * math.pi * pin_diameter_mm**2 / 4
    tau = F_N / A if A > 0 else 0
    
    return {
        'force_N': F_N,
        'pin_diameter_mm': pin_diameter_mm,
        'num_pins': num_pins,
        'total_area_mm2': round(A, 2),
        'shear_stress_mpa': round(tau, 2),
        'formula': 'τ = 4F/(n·π·d²)',
    }


# ============ 过盈配合 ============

def interference_fit(shaft_diameter_mm, interference_um, hub_od_mm,
                     E_shaft_mpa=206000, E_hub_mpa=206000,
                     nu_shaft=0.3, nu_hub=0.3,
                     friction_coeff=0.15, length_mm=None):
    """
    过盈配合传递扭矩计算
    
    参数:
        shaft_diameter_mm: 配合直径 (mm)
        interference_um: 过盈量 (μm)
        hub_od_mm: 轮毂外径 (mm)
        E_shaft_mpa, E_hub_mpa: 弹性模量
        nu_shaft, nu_hub: 泊松比
        friction_coeff: 摩擦系数
        length_mm: 配合长度 (mm)
    """
    d = shaft_diameter_mm
    delta = interference_um / 1000  # mm
    d_hub = hub_od_mm
    
    # 过盈产生的接触压力 (厚壁圆筒公式)
    q = delta / (d * (1/E_shaft_mpa * (1 - nu_shaft) + 1/E_hub_mpa * ((d_hub**2 + d**2)/(d_hub**2 - d**2) + nu_hub)))
    
    # 可以传递的扭矩
    if length_mm and q > 0:
        T = math.pi * d**2 * length_mm * q * friction_coeff / 2  # N·mm
    else:
        T = 0
    
    # 温差法装配所需温度
    alpha = 1.2e-5  # 钢的热膨胀系数
    delta_need = interference_um * 1.5  # 装配时需要的间隙
    delta_T = (interference_um + delta_need) / (alpha * d * 1000) if d > 0 else 0
    
    return {
        'contact_pressure_mpa': round(q, 2),
        'transmittable_torque_Nm': round(T / 1000, 2) if T > 0 else 0,
        'interference_mm': round(delta, 4),
        'temp_rise_for_assembly_C': round(delta_T, 1),
        'formula_pressure': 'p = δ / (d·(C₁/E₁ + C₂/E₂))',
        'note': '温差法装配: 加热轮毂或冷却轴',
    }


# ============ 压入力 ============

def press_fit_force(shaft_diameter_mm, interference_um, hub_od_mm, length_mm,
                    friction_coeff=0.15, E_mpa=206000, nu=0.3):
    """
    压入力计算  F = f·π·d·L·p
    
    参数:
        shaft_diameter_mm: 轴径 (mm)
        interference_um: 过盈量 (μm)
        hub_od_mm: 轮毂外径 (mm)
        length_mm: 配合长度 (mm)
        friction_coeff: 摩擦系数
    """
    d = shaft_diameter_mm
    delta = interference_um / 1000
    d_hub = hub_od_mm
    
    q = delta / (d * (2/E_mpa * ((d_hub**2 + d**2)/(d_hub**2 - d**2))))
    
    F = friction_coeff * math.pi * d * length_mm * q if q > 0 else 0
    
    return {
        'press_force_N': round(F, 1),
        'press_force_ton': round(F / 9806.65, 2),
        'contact_pressure_mpa': round(q, 2),
        'shaft_diameter_mm': d,
        'interference_mm': round(delta, 4),
        'length_mm': length_mm,
    }

def rivet_strength(F_N, d_mm, t_min_mm, n=1, shear_planes=1):
    import math
    As = n * math.pi * d_mm**2 / 4
    tau = F_N * shear_planes / As if As > 0 else 0
    sigma_p = F_N / (n * d_mm * t_min_mm) if n * d_mm * t_min_mm > 0 else 0
    return {'shear_stress_mpa': round(tau, 2), 'bearing_stress_mpa': round(sigma_p, 2)}

def adhesive_strength(F_N, width_mm, length_mm):
    A = width_mm * length_mm
    stress = F_N / A if A > 0 else 0
    return {'area_mm2': round(A, 2), 'stress_mpa': round(stress, 2)}
