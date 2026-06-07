"""紧固件/连接/焊接 蓝图

URL 前缀: /api/calc
"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.utils.convert import safe_float
from backend.calculations.thread import (
    metric_thread_basic, tap_drill_diameter, bolt_preload_torque,
)
from backend.calculations.weld import (  # noqa: F401
    calc_fillet_weld_stress, calc_butt_weld_stress,
)
from backend.calculations.strength import (  # noqa: F401
    section_properties, column_buckling, column_stability_check,
    weld_fillet_stress, weld_butt_stress,
    key_strength, pin_strength, interference_fit,
)

bp = Blueprint('fasteners', __name__, url_prefix='/api/calc')


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


# ---- 螺纹 ----

@bp.post('/thread/metric')
def thread_metric():
    """公制螺纹基本尺寸"""
    d, p = _p('nominal_d', 'pitch')
    if d is None or p is None:
        return error('请填写 nominal_d / pitch', code=400)
    return success(metric_thread_basic(d, p))


@bp.post('/thread/tap-drill')
def thread_tap():
    """攻丝底孔"""
    spec = (request.get_json(silent=True) or {}).get('spec', 'M10x1.5')
    return success(tap_drill_diameter(str(spec)))


@bp.post('/thread/preload')
def thread_preload():
    """螺栓预紧扭矩"""
    d = safe_float((request.get_json(silent=True) or {}).get('d_mm'))
    if d is None:
        return error('请填写 d_mm', code=400)
    body = request.get_json(silent=True) or {}
    return success(bolt_preload_torque(d, str(body.get('grade', '8.8')),
                                       safe_float(body.get('mu', 0.15)) or 0.15))


# ---- 焊接 ----

@bp.post('/weld/fillet')
def weld_fillet():
    """角焊缝强度校核"""
    d = request.get_json(silent=True) or {}
    F = safe_float(d.get('F_N'))
    h = safe_float(d.get('weld_leg_mm'))
    Lw = safe_float(d.get('weld_length_mm'))
    if F is None or h is None or Lw is None:
        return error('请填写 F_N / weld_leg_mm / weld_length_mm', code=400)
    num = int(safe_float(d.get('num_welds', 2)) or 2)
    return success(weld_fillet_stress(F_N=F, weld_leg_mm=h,
                                      weld_length_mm=Lw, num_welds=num))


@bp.post('/weld/butt')
def weld_butt():
    """对接焊缝强度校核"""
    d = request.get_json(silent=True) or {}
    F = safe_float(d.get('F_N'))
    t = safe_float(d.get('plate_thickness_mm'))
    w = safe_float(d.get('weld_width_mm'))
    if F is None or t is None or w is None:
        return error('请填写 F_N / plate_thickness_mm / weld_width_mm', code=400)
    return success(weld_butt_stress(F_N=F, plate_thickness_mm=t, weld_width_mm=w))


# ---- 强度 ----

@bp.post('/strength/column-buckling')
def strength_column_buckling():
    """压杆稳定性 (欧拉)"""
    d = request.get_json(silent=True) or {}
    E = safe_float(d.get('E_mpa'))
    L = safe_float(d.get('L_mm'))
    I = safe_float(d.get('I_mm4'))
    A = safe_float(d.get('A_mm2'))
    if any(x is None for x in (E, L, I, A)):
        return error('请填写 E_mpa / L_mm / I_mm4 / A_mm2', code=400)
    mu = safe_float(d.get('mu', 1.0)) or 1.0
    sigma_s = safe_float(d.get('sigma_s_mpa', 235)) or 235
    return success(column_buckling(E_mpa=E, L_mm=L, I_mm4=I, A_mm2=A, mu=mu, sigma_s_mpa=sigma_s))


@bp.post('/strength/column-stability')
def strength_column_stability():
    """立柱稳定性校核 (完整流程)"""
    d = request.get_json(silent=True) or {}
    F = safe_float(d.get('F_N'))
    A = safe_float(d.get('A_mm2'))
    E = safe_float(d.get('E_mpa'))
    L = safe_float(d.get('L_mm'))
    I = safe_float(d.get('I_mm4'))
    if any(x is None for x in (F, A, E, L, I)):
        return error('请填写 F_N / A_mm2 / E_mpa / L_mm / I_mm4', code=400)
    return success(column_stability_check(F_N=F, A_mm2=A, E_mpa=E, L_mm=L, I_mm4=I))


@bp.post('/strength/key')
def strength_key():
    """平键强度校核"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('T_Nmm'))
    if T is None:
        return error('请填写 T_Nmm', code=400)
    return success(key_strength(T_Nmm=T,
                                shaft_diameter_mm=safe_float(d.get('shaft_diameter_mm')) or 50,
                                key_width_mm=safe_float(d.get('key_width_mm')) or 10,
                                key_height_mm=safe_float(d.get('key_height_mm')) or 8,
                                key_length_mm=safe_float(d.get('key_length_mm')) or 40))


@bp.post('/strength/pin')
def strength_pin():
    """销强度校核"""
    d = request.get_json(silent=True) or {}
    F = safe_float(d.get('F_N'))
    pin_d = safe_float(d.get('pin_diameter_mm'))
    if F is None or pin_d is None:
        return error('请填写 F_N / pin_diameter_mm', code=400)
    num_pins = int(safe_float(d.get('num_pins', 1)) or 1)
    return success(pin_strength(F_N=F, pin_diameter_mm=pin_d, num_pins=num_pins))


@bp.post('/strength/interference-fit')
def strength_interference():
    """过盈配合"""
    d = request.get_json(silent=True) or {}
    shaft_d = safe_float(d.get('shaft_diameter_mm'))
    inter = safe_float(d.get('interference_um'))
    hub_od = safe_float(d.get('hub_od_mm'))
    if any(x is None for x in (shaft_d, inter, hub_od)):
        return error('请填写 shaft_diameter_mm / interference_um / hub_od_mm', code=400)
    return success(interference_fit(shaft_diameter_mm=shaft_d,
                                    interference_um=inter, hub_od_mm=hub_od))
