"""
热力学/流体/传热计算模块
"""
import math

# ============ 热传导 ============


def conduction(Q=None, k=None, A=None, dT=None, L=None):
    """
    热传导  Q = k·A·ΔT/L
    
    输入任意4个求第5个
    """
    known = sum(1 for x in [Q, k, A, dT, L] if x is not None)
    if known != 4:
        return {'error': '请输入其中4个参数求第5个'}
    
    if Q is None:
        Q = k * A * dT / L
    elif k is None:
        k = Q * L / (A * dT) if A * dT != 0 else 0
    elif A is None:
        A = Q * L / (k * dT) if k * dT != 0 else 0
    elif dT is None:
        dT = Q * L / (k * A) if k * A != 0 else 0
    elif L is None:
        L = k * A * dT / Q if Q != 0 else 0
    
    return {
        'heat_flow_W': round(Q, 4) if Q else 0,
        'thermal_conductivity_W_mK': round(k, 4) if k else 0,
        'area_m2': round(A, 4) if A else 0,
        'temp_diff_K': round(dT, 2) if dT else 0,
        'thickness_m': round(L, 4) if L else 0,
        'formula': 'Q = k·A·ΔT/L',
    }


def convection(Q=None, h=None, A=None, dT=None):
    """
    热对流  Q = h·A·ΔT
    """
    known = sum(1 for x in [Q, h, A, dT] if x is not None)
    if known != 3:
        return {'error': '请输入其中3个参数'}
    
    if Q is None:
        Q = h * A * dT
    elif h is None:
        h = Q / (A * dT) if A * dT != 0 else 0
    elif A is None:
        A = Q / (h * dT) if h * dT != 0 else 0
    elif dT is None:
        dT = Q / (h * A) if h * A != 0 else 0
    
    return {
        'heat_flow_W': round(Q, 4) if Q else 0,
        'heat_transfer_coeff_W_m2K': round(h, 4) if h else 0,
        'area_m2': round(A, 4) if A else 0,
        'temp_diff_K': round(dT, 2) if dT else 0,
        'formula': 'Q = h·A·ΔT',
    }


def thermal_expansion(L0_m, dT_K, alpha=1.2e-5):
    """
    热膨胀  ΔL = α·L₀·ΔT
    
    参数:
        L0_m: 原始长度 (m)
        dT_K: 温度变化 (K)
        alpha: 线膨胀系数 (1/K), 钢≈1.2e-5
    """
    delta_L = alpha * L0_m * dT_K
    return {
        'original_length_m': L0_m,
        'temp_change_K': dT_K,
        'expansion_coeff': alpha,
        'expansion_mm': round(delta_L * 1000, 4),
        'final_length_m': round(L0_m + delta_L, 6),
        'formula': 'ΔL = α·L₀·ΔT',
    }


def thermal_stress(E_mpa, dT_K, alpha=1.2e-5):
    """
    热应力  σ = E·α·ΔT (完全约束)
    """
    sigma = E_mpa * alpha * dT_K
    return {
        'elastic_modulus_mpa': E_mpa,
        'temp_change_K': dT_K,
        'expansion_coeff': alpha,
        'thermal_stress_mpa': round(sigma, 2),
        'formula': 'σ = E·α·ΔT',
    }


# ============ 流体 ============

def bernoulli(p1=None, p2=None, v1=None, v2=None, h1=0, h2=0, rho=1000, g=9.81):
    """
    伯努利方程  p₁ + ½ρv₁² + ρgh₁ = p₂ + ½ρv₂² + ρgh₂
    
    已知任意5个参数求第6个
    """
    # p1 + 0.5*rho*v1^2 + rho*g*h1 = p2 + 0.5*rho*v2^2 + rho*g*h2
    known = sum(1 for x in [p1, p2, v1, v2] if x is not None)
    if known < 3:
        return {'error': '至少需知道其中3个参数'}
    
    total_1 = (p1 or 0) + 0.5 * rho * (v1 or 0)**2 + rho * g * h1
    total_2 = (p2 or 0) + 0.5 * rho * (v2 or 0)**2 + rho * g * h2
    
    if v1 is None:
        # p1 + ρgh₁ = p₂ + ½ρv₂² + ρgh₂ - assume v2 known, p1 known
        v1 = math.sqrt(2 * (total_2 - (p1 or 0) - rho * g * h1) / rho) if rho > 0 else 0
    elif v2 is None:
        v2 = math.sqrt(2 * (total_1 - (p2 or 0) - rho * g * h2) / rho) if rho > 0 else 0
    elif p1 is None:
        p1 = total_2 - 0.5 * rho * v1**2 - rho * g * h1
    elif p2 is None:
        p2 = total_1 - 0.5 * rho * v2**2 - rho * g * h2
    
    return {
        'p1_Pa': round(p1, 2) if p1 else 0,
        'p2_Pa': round(p2, 2) if p2 else 0,
        'v1_mps': round(v1, 4) if v1 else 0,
        'v2_mps': round(v2, 4) if v2 else 0,
        'h1_m': h1, 'h2_m': h2,
        'rho_kgm3': rho,
        'total_head_m': round((total_1 or total_2) / (rho * g), 3) if rho > 0 else 0,
        'formula': 'p₁ + ½ρv₁² + ρgh₁ = const',
    }


def orifice_flow(d_mm, delta_p_Pa, Cd=0.62, rho=1000):
    """
    孔板流量  Q = Cd·A·√(2Δp/ρ)
    """
    A = math.pi * (d_mm / 1000)**2 / 4
    Q = Cd * A * math.sqrt(2 * delta_p_Pa / rho) if rho > 0 else 0
    Q_lpm = Q * 60000
    
    return {
        'orifice_diameter_mm': d_mm,
        'area_m2': round(A, 8),
        'pressure_drop_Pa': delta_p_Pa,
        'discharge_coeff': Cd,
        'flow_m3s': round(Q, 8),
        'flow_Lpm': round(Q_lpm, 3),
        'flow_m3h': round(Q * 3600, 4),
    }


def pipe_velocity(Q_m3s=None, Q_lpm=None, d_mm=None):
    """
    管流速度  v = Q/A
    """
    if Q_lpm is not None:
        Q_m3s = Q_lpm / 60000
    if not Q_m3s or not d_mm:
        return {'error': '请输入流量和管径'}
    
    A = math.pi * (d_mm / 1000)**2 / 4
    v = Q_m3s / A if A > 0 else 0
    
    return {
        'flow_m3s': Q_m3s,
        'diameter_mm': d_mm,
        'area_m2': round(A, 8),
        'velocity_mps': round(v, 4),
        'velocity_m_min': round(v * 60, 2),
    }


def weir_flow(b_m, h_m, Cd=0.62):
    """
    堰流  Q = Cd·b·√(2g)·h^(3/2)
    """
    Q = Cd * b_m * math.sqrt(2 * 9.81) * h_m**1.5
    return {
        'weir_width_m': b_m,
        'weir_head_m': h_m,
        'flow_m3s': round(Q, 4),
        'flow_Lpm': round(Q * 60000, 1),
    }


# ============ 气体 ============

def ideal_gas(p_Pa, V_m3, T_K, n_mol=None, m_kg=None, M_kgmol=0.029):
    """
    理想气体状态方程  pV = nRT
    R = 8.314 J/(mol·K)
    """
    R = 8.314
    if n_mol is None and m_kg is not None:
        n_mol = m_kg / M_kgmol
    if n_mol is None:
        return {'error': '请输入摩尔数或质量'}
    
    n = n_mol
    pV = n * R * T_K
    
    return {
        'pressure_Pa': p_Pa,
        'volume_m3': V_m3,
        'temperature_K': T_K,
        'moles': round(n, 4),
        'gas_constant': R,
        'pV_value': round(pV, 2),
        'formula': 'pV = nRT',
    }
