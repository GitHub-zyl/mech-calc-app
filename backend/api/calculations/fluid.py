"""流体传动 (液压/气动) 蓝图"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.utils.convert import safe_float
from backend.calculations.hydraulic import (
    pipe_pressure_loss, thin_orifice_flow, accumulator_selection,
    hydraulic_shock, oil_tank_heat_balance, oil_viscosity_temp,
)
from backend.calculations.pneumatic import (
    calc_cylinder_force,
    calc_cylinder_air_consumption,
    calc_air_receiver_volume,
)

bp = Blueprint('fluid', __name__, url_prefix='/api/calc')


def _p(*keys, defaults=None):
    d = request.get_json(silent=True) or {}
    defaults = defaults or {}
    out = []
    for k in keys:
        v = d.get(k)
        if v is None or v == '':
            out.append(defaults.get(k))
        else:
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                out.append(v)
    return out


# ---- 液压 ----

@bp.post('/hydraulic/pipe-pressure-loss')
def hydraulic_pipe_loss():
    d = request.get_json(silent=True) or {}
    Q = safe_float(d.get('flow_lpm'))
    inner = safe_float(d.get('inner_diam_mm'))
    L = safe_float(d.get('length_m'))
    if any(x is None for x in (Q, inner, L)):
        return error('请填写 flow_lpm / inner_diam_mm / length_m', code=400)
    return success(pipe_pressure_loss(Q, inner, L))


@bp.post('/hydraulic/orifice')
def hydraulic_orifice():
    d = request.get_json(silent=True) or {}
    d_mm = safe_float(d.get('d_mm'))
    dp = safe_float(d.get('delta_p_bar'))
    if d_mm is None or dp is None:
        return error('请填写 d_mm / delta_p_bar', code=400)
    return success(thin_orifice_flow(d_mm, dp))


@bp.post('/hydraulic/accumulator')
def hydraulic_accumulator():
    d = request.get_json(silent=True) or {}
    V0 = safe_float(d.get('V0_L'))
    p0 = safe_float(d.get('p0_bar'))
    p1 = safe_float(d.get('p1_bar'))
    p2 = safe_float(d.get('p2_bar'))
    if any(x is None for x in (V0, p0, p1, p2)):
        return error('请填写 V0_L / p0_bar / p1_bar / p2_bar', code=400)
    return success(accumulator_selection(V0, p0, p1, p2))


@bp.post('/hydraulic/shock')
def hydraulic_shock_api():
    d = request.get_json(silent=True) or {}
    v1 = safe_float(d.get('v1_mps'))
    v2 = safe_float(d.get('v2_mps'))
    L = safe_float(d.get('pipe_length_m'))
    if any(x is None for x in (v1, v2, L)):
        return error('请填写 v1_mps / v2_mps / pipe_length_m', code=400)
    return success(hydraulic_shock(v1, v2, L))


@bp.post('/hydraulic/tank-heat')
def hydraulic_tank_heat():
    d = request.get_json(silent=True) or {}
    p = safe_float(d.get('power_kw'))
    if p is None:
        return error('请填写 power_kw', code=400)
    V = safe_float(d.get('tank_volume_L'))
    return success(oil_tank_heat_balance(power_kw=p, tank_volume_L=V,
                                         temp_rise_target_K=safe_float(d.get('temp_rise_target_K', 30)) or 30))


@bp.post('/hydraulic/oil-viscosity')
def hydraulic_oil_visc():
    d = request.get_json(silent=True) or {}
    nu = safe_float(d.get('nu_40'))
    t = safe_float(d.get('t_C'))
    if nu is None or t is None:
        return error('请填写 nu_40 / t_C', code=400)
    vi = safe_float(d.get('vi', 100)) or 100
    return success(oil_viscosity_temp(nu, t, vi))


@bp.post('/hydraulic/pipe-diameter')
def hydraulic_pipe_diameter():
    """由流量估算推荐管径 (按推荐流速 2~6 m/s)"""
    d = request.get_json(silent=True) or {}
    Q = safe_float(d.get('flow_lpm'))
    if Q is None:
        return error('请填写 flow_lpm', code=400)
    # 推荐流速档
    v_rec = safe_float(d.get('v_mps', 3.0)) or 3.0
    # Q (L/min) = 1e-3/60 m^3/s
    Q_m3_s = Q / 1000.0 / 60.0
    A = Q_m3_s / v_rec if v_rec > 0 else None
    import math as _m
    D = _m.sqrt(4 * A / _m.pi) * 1000 if A and A > 0 else None  # mm
    return success({
        'flow_lpm': Q,
        'recommended_velocity_mps': v_rec,
        'inner_diameter_mm': round(D, 2) if D else None,
        'formula': 'D = √(4Q/(π·v))',
        'note': '吸油管 v≈0.5~1.5 m/s, 压油管 v≈2~6 m/s, 回油管 v≤2 m/s',
    })


# ---- 气动 ----

@bp.post('/pneumatic/force')
def pneumatic_force():
    d = request.get_json(silent=True) or {}
    p = safe_float(d.get('pressure_mpa'))
    D = safe_float(d.get('bore_mm'))
    if p is None or D is None:
        return error('请填写 pressure_mpa / bore_mm', code=400)
    d_rod = safe_float(d.get('rod_mm', 0)) or 0
    return success(calc_cylinder_force(D=D, d_rod=d_rod, p=p))


@bp.post('/pneumatic/bore')
def pneumatic_bore():
    d = request.get_json(silent=True) or {}
    F = safe_float(d.get('force_kn'))
    p = safe_float(d.get('pressure_mpa'))
    if F is None or p is None:
        return error('请填写 force_kn / pressure_mpa', code=400)
    # 反推直径: F = π*D²/4 * p → D = sqrt(4F/π/p)
    import math
    D = math.sqrt(4 * F * 1000 / math.pi / (p * 1e6)) * 1000  # mm
    return success({'bore_mm': D})


@bp.post('/pneumatic/consumption')
def pneumatic_consumption():
    d = request.get_json(silent=True) or {}
    D = safe_float(d.get('bore_mm'))
    L = safe_float(d.get('stroke_mm'))
    n = safe_float(d.get('cycles_per_min'))
    p = safe_float(d.get('pressure_mpa', 0.6)) or 0.6
    if any(x is None for x in (D, L, n)):
        return error('请填写 bore_mm / stroke_mm / cycles_per_min', code=400)
    return success(calc_cylinder_air_consumption(D=D, stroke=L, p=p, n_cycle=n))


@bp.post('/pneumatic/receiver')
def pneumatic_receiver():
    d = request.get_json(silent=True) or {}
    Q = safe_float(d.get('compressor_flow_lpm'))
    p_min = safe_float(d.get('min_pressure_mpa'))
    p_max = safe_float(d.get('max_pressure_mpa'))
    if any(x is None for x in (Q, p_min, p_max)):
        return error('请填写 compressor_flow_lpm / min_pressure_mpa / max_pressure_mpa', code=400)
    # 单位换算: L/min -> m^3/min, 压力按绝对
    Q_m3_min = Q / 1000.0
    t_cycle = safe_float(d.get('t_cycle_min', 1.0)) or 1.0
    return success(calc_air_receiver_volume(Q=Q_m3_min, p_max=p_max, p_min=p_min, t_cycle=t_cycle))
