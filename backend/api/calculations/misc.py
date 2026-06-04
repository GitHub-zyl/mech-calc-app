"""其他计算蓝图: 公差/表面/弹簧/冲压/制动/联轴器

适配层说明: 计算模块 (calculations/) 已重构为标准命名函数.
本文件负责把 API 层的语义化参数映射到计算模块的精确参数.
"""
import math
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.utils.convert import safe_float
from backend.calculations.tolerance import (
    shaft_tolerance, hole_tolerance, fit_calculation,
)
from backend.calculations.surface import (
    calc_roughness_convert, calc_hardness_convert, calc_surface_texture,
)
from backend.calculations.spring import (
    coil_spring_compression, coil_spring_tension,
    coil_spring_stress, spring_deflection,
)
from backend.calculations.press import (
    blanking_force, stripping_force, v_bending_force,
    embossing_force, shear_force,
)
from backend.calculations.brake import (
    calc_disc_brake_torque, calc_band_brake_torque, calc_clutch_energy,
)
from backend.calculations.coupling import (
    coupling_gear_torque, coupling_universal, oring_groove,
)

bp = Blueprint('misc', __name__, url_prefix='/api/calc')


# ===== 适配层辅助函数 (API -> 计算函数参数转换) =====

def _torque_to_power_kw(T_nm, n_rpm):
    """T(N·m), n(rpm) -> P(kW) = T*2π*n/60/1000"""
    if T_nm is None or n_rpm in (None, 0):
        return None
    return T_nm * 2 * math.pi * n_rpm / 60 / 1000


# ---- 公差 ----

@bp.post('/tolerance/shaft')
def tolerance_shaft():
    d = request.get_json(silent=True) or {}
    nom = safe_float(d.get('nominal_mm'))
    if nom is None:
        return error('请填写 nominal_mm', code=400)
    spec = d.get('tolerance_spec', 'h6')
    return success(shaft_tolerance(nom, str(spec)))


@bp.post('/tolerance/hole')
def tolerance_hole():
    d = request.get_json(silent=True) or {}
    nom = safe_float(d.get('nominal_mm'))
    if nom is None:
        return error('请填写 nominal_mm', code=400)
    spec = d.get('tolerance_spec', 'H7')
    return success(hole_tolerance(nom, str(spec)))


@bp.post('/tolerance/fit')
def tolerance_fit():
    d = request.get_json(silent=True) or {}
    nom = safe_float(d.get('nominal_mm'))
    if nom is None:
        return error('请填写 nominal_mm', code=400)
    hole = d.get('hole_spec', 'H7')
    shaft = d.get('shaft_spec', 'g6')
    return success(fit_calculation(nom, str(hole), str(shaft)))


# ---- 表面 ----

@bp.post('/surface/ra-to-rz')
def surface_ra_to_rz():
    d = request.get_json(silent=True) or {}
    Ra = safe_float(d.get('Ra_um'))
    if Ra is None:
        return error('请填写 Ra_um', code=400)
    return success(calc_roughness_convert(Ra=Ra))


@bp.post('/surface/hardness-convert')
def surface_hardness_convert():
    d = request.get_json(silent=True) or {}
    v = safe_float(d.get('value'))
    if v is None:
        return error('请填写 value', code=400)
    return success(calc_hardness_convert(
        value=v, from_type=d.get('from_type', 'HB'),
        to_type=d.get('to_type', 'HRC'),
    ))


# ---- 弹簧 ----

@bp.post('/spring/compression')
def spring_compression():
    d = request.get_json(silent=True) or {}
    wire = safe_float(d.get('wire_diameter'))
    Dm = safe_float(d.get('mean_diameter'))
    n = safe_float(d.get('coils'))
    if any(x is None for x in (wire, Dm, n)):
        return error('请填写 wire_diameter / mean_diameter / coils', code=400)
    G = safe_float(d.get('G', 79000)) or 79000
    mat = d.get('material', '弹簧钢')
    return success(coil_spring_compression(wire, Dm, n, G, str(mat)))


@bp.post('/spring/tension')
def spring_tension():
    d = request.get_json(silent=True) or {}
    wire = safe_float(d.get('wire_diameter'))
    Dm = safe_float(d.get('mean_diameter'))
    n = safe_float(d.get('coils'))
    if any(x is None for x in (wire, Dm, n)):
        return error('请填写 wire_diameter / mean_diameter / coils', code=400)
    G = safe_float(d.get('G', 79000)) or 79000
    F0 = safe_float(d.get('F0', 0)) or 0
    return success(coil_spring_tension(wire, Dm, n, F0, G))


@bp.post('/spring/stress')
def spring_stress():
    d = request.get_json(silent=True) or {}
    wire = safe_float(d.get('wire_diameter'))
    Dm = safe_float(d.get('mean_diameter'))
    F = safe_float(d.get('F'))
    if any(x is None for x in (wire, Dm, F)):
        return error('请填写 wire_diameter / mean_diameter / F', code=400)
    mat = d.get('material', '弹簧钢')
    return success(coil_spring_stress(wire, Dm, F, str(mat)))


@bp.post('/spring/deflection')
def spring_deflection_api():
    d = request.get_json(silent=True) or {}
    k = safe_float(d.get('k'))
    F = safe_float(d.get('F'))
    if k is None or F is None:
        return error('请填写 k / F', code=400)
    return success(spring_deflection(k, F))


# ---- 冲压 ----

@bp.post('/press/blanking')
def press_blanking():
    """冲裁力 F = K·L·t·τ"""
    d = request.get_json(silent=True) or {}
    L = safe_float(d.get('perimeter_mm'))
    t = safe_float(d.get('thickness_mm'))
    tau = safe_float(d.get('shear_strength_mpa'))
    if any(x is None for x in (L, t, tau)):
        return error('请填写 perimeter_mm / thickness_mm / shear_strength_mpa', code=400)
    k = safe_float(d.get('k', 1.3)) or 1.3
    return success(blanking_force(L, t, tau, k=k))


@bp.post('/press/v-bending')
def press_v_bending():
    """V型弯曲力 F = k·b·t²·σb/w"""
    d = request.get_json(silent=True) or {}
    b = safe_float(d.get('width_mm'))
    t = safe_float(d.get('thickness_mm'))
    sigma = safe_float(d.get('tensile_strength_mpa'))
    w = safe_float(d.get('die_opening_mm'))
    if any(x is None for x in (b, t, sigma, w)):
        return error('请填写 width_mm / thickness_mm / tensile_strength_mpa / die_opening_mm', code=400)
    return success(v_bending_force(b, t, sigma, w))


@bp.post('/press/shear')
def press_shear():
    """剪切力 F = A·τ"""
    d = request.get_json(silent=True) or {}
    A = safe_float(d.get('area_mm2'))
    tau = safe_float(d.get('shear_strength_mpa'))
    if A is None or tau is None:
        return error('请填写 area_mm2 / shear_strength_mpa', code=400)
    return success(shear_force(A, tau))


# 旧路由兼容
@bp.post('/press/stroke')
def press_stroke_api():
    """旧 API: 用 spm+die_height 估算滑块行程 (简化: 行程 ≈ 2×闭合高度+常量)"""
    d = request.get_json(silent=True) or {}
    n = safe_float(d.get('spm'))
    h = safe_float(d.get('die_height_mm'))
    if n is None or h is None:
        return error('请填写 spm / die_height_mm', code=400)
    return success({
        'spm': n,
        'die_height_mm': h,
        'stroke_mm': round(h * 0.6, 1),
        'cycle_time_s': round(60.0 / n, 3) if n > 0 else None,
        'note': '估算行程, 实际行程需查压力机规格',
    })


@bp.post('/press/force')
def press_force_api():
    """旧 API: 由面积+压力直接算总力 = A·p"""
    d = request.get_json(silent=True) or {}
    A = safe_float(d.get('area_mm2'))
    p = safe_float(d.get('pressure_mpa'))
    if A is None or p is None:
        return error('请填写 area_mm2 / pressure_mpa', code=400)
    F_kN = A * p / 1000
    return success({
        'force_kN': round(F_kN, 2),
        'force_ton': round(F_kN / 9.81, 2),
        'area_mm2': A,
        'pressure_mpa': p,
        'note': 'F = A·p (液压机总力)',
    })


# ---- 制动 ----

@bp.post('/brake/simple')
def brake_simple_api():
    """简单蹄式制动: T = μ·F·r  (F = T/(μ·r))"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('T_Nm'))
    r = safe_float(d.get('radius_m'))
    if T is None or r is None:
        return error('请填写 T_Nm / radius_m', code=400)
    mu = safe_float(d.get('mu', 0.4)) or 0.4
    F_N = T / (mu * r) if mu > 0 and r > 0 else None
    return success({
        'torque_Nm': T,
        'radius_m': r,
        'friction_coeff': mu,
        'actuation_force_N': round(F_N, 2) if F_N is not None else None,
        'formula': 'T = μ·F·r → F = T/(μ·r)',
    })


@bp.post('/brake/disc')
def brake_disc_api():
    """盘式制动: T = n·μ·p·π·(D_o³ - D_i³)/12"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('T_Nm'))
    n = safe_float(d.get('num_friction_surfaces', 2)) or 2
    R_o = safe_float(d.get('outer_radius_mm'))
    R_i = safe_float(d.get('inner_radius_mm'))
    p = safe_float(d.get('pressure_mpa'))
    if any(x is None for x in (T, R_o, R_i, p)):
        return error('请填写 T_Nm / outer_radius_mm / inner_radius_mm / pressure_mpa', code=400)
    D_o = 2 * R_o
    D_i = 2 * R_i
    # 反推 μ: μ = T / [n·p·π·(D_o³-D_i³)/12] (注意单位: T N·m → N·mm ×1000)
    denom = n * p * math.pi * (D_o**3 - D_i**3) / 12
    mu = (T * 1000) / denom if denom > 0 else None
    return success({
        'torque_Nm': T,
        'num_friction_surfaces': int(n),
        'outer_radius_mm': R_o,
        'inner_radius_mm': R_i,
        'pressure_mpa': p,
        'derived_friction_coeff': round(mu, 3) if mu is not None else None,
        'formula': 'T = n·μ·p·π·(D_o³-D_i³)/12',
    })


@bp.post('/brake/band')
def brake_band_api():
    """带式制动"""
    d = request.get_json(silent=True) or {}
    F1 = safe_float(d.get('F1_N'))
    mu = safe_float(d.get('mu'))
    theta = safe_float(d.get('theta_deg'))
    r = safe_float(d.get('drum_radius_mm'))
    if any(x is None for x in (F1, mu, theta, r)):
        return error('请填写 F1_N / mu / theta_deg / drum_radius_mm', code=400)
    return success(calc_band_brake_torque(F1=F1, mu=mu, theta_deg=theta, r=r))


# ---- 联轴器 ----

@bp.post('/coupling/select')
def coupling_select_api():
    """联轴器选型: T(N·m)+n(rpm) → P(kW) → 齿式联轴器选型"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('T_Nm'))
    n = safe_float(d.get('n_rpm'))
    if T is None or n is None:
        return error('请填写 T_Nm / n_rpm', code=400)
    P_kw = _torque_to_power_kw(T, n)
    if P_kw is None:
        return error('n_rpm 必须大于 0', code=400)
    return success(coupling_gear_torque(power_kw=P_kw, rpm=n))


@bp.post('/coupling/universal')
def coupling_universal_api():
    """万向联轴器"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('T_Nm'))
    n = safe_float(d.get('n_rpm'))
    angle = safe_float(d.get('angle_deg', 10)) or 10
    if T is None or n is None:
        return error('请填写 T_Nm / n_rpm', code=400)
    P_kw = _torque_to_power_kw(T, n)
    if P_kw is None:
        return error('n_rpm 必须大于 0', code=400)
    return success(coupling_universal(power_kw=P_kw, rpm=n, angle_deg=angle))


@bp.post('/coupling/rigid')
def coupling_rigid_api():
    """刚性联轴器校核: 仅返回 T 与 d 记录, 选型按 d 查表 (此处返回参考)"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('T_Nm'))
    d_mm = safe_float(d.get('d_mm'))
    if T is None or d_mm is None:
        return error('请填写 T_Nm / d_mm', code=400)
    # 扭转切应力 τ = 16T/(πd³) (MPa, T N·mm)
    T_Nmm = T * 1000
    tau = 16 * T_Nmm / (math.pi * d_mm**3) if d_mm > 0 else None
    allowable = 35  # 45钢许用切应力 MPa
    return success({
        'torque_Nm': T,
        'shaft_diameter_mm': d_mm,
        'shear_stress_mpa': round(tau, 2) if tau is not None else None,
        'allowable_shear_mpa': allowable,
        'is_safe': (tau is not None and tau <= allowable),
        'formula': 'τ = 16T/(πd³), [τ]≈35 MPa (45钢)',
    })


@bp.post('/coupling/flexible')
def coupling_flexible_api():
    """弹性联轴器扭转刚度: 扭转角 φ = T/k"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('T_Nm'))
    k = safe_float(d.get('stiffness_nm_rad'))
    if T is None or k is None:
        return error('请填写 T_Nm / stiffness_nm_rad', code=400)
    phi_rad = T / k if k > 0 else None
    return success({
        'torque_Nm': T,
        'stiffness_nm_rad': k,
        'twist_angle_rad': round(phi_rad, 6) if phi_rad is not None else None,
        'twist_angle_deg': round(math.degrees(phi_rad), 4) if phi_rad is not None else None,
        'formula': 'φ = T/k',
    })
