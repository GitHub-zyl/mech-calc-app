"""轴系/轴承/梁/疲劳 蓝图

URL 前缀: /api/calc
"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.utils.convert import safe_float
from backend.calculations.shaft import (
    calc_shaft_torsion, calc_shaft_combined, calc_shaft_fatigue, calc_critical_speed,
)
from backend.calculations.bearing import (
    bearing_life, equivalent_load, bearing_static_check,
)
from backend.calculations.beam import beam_section_inertia, calc_beam
from backend.calculations.fatigue import (
    calc_sn_curve, calc_stress_concentration, calc_miner_damage,
)

bp = Blueprint('shaft_system', __name__, url_prefix='/api/calc')


# ============== 轴 ==============

@bp.post('/shaft/torsion')
def shaft_torsion_api():
    """轴扭转强度校核"""
    d, P, n, tau, P_kW = _p('d', 'P', 'n', 'tau_allow', 'P_kW')
    if d is None or (P is None and P_kW is None) or n is None:
        return error('请填写 d / (P 或 P_kW) / n', code=400)
    return success(calc_shaft_torsion(d=d, P=P, n=n, tau_allow=tau, P_kW=P_kW))


@bp.post('/shaft/combined')
def shaft_combined_api():
    """弯扭合成强度校核"""
    d, M, T, alpha, sigma = _p('d', 'M', 'T', 'alpha', 'sigma_allow', defaults={'alpha': 1.0})
    if d is None or M is None or T is None:
        return error('请填写 d / M / T', code=400)
    return success(calc_shaft_combined(d=d, M=M, T=T, alpha=alpha, sigma_allow=sigma))


@bp.post('/shaft/fatigue')
def shaft_fatigue_api():
    """轴疲劳强度校核"""
    d, M, T, sigma_b = _p('d', 'M', 'T', 'sigma_b')
    if d is None or M is None or T is None or sigma_b is None:
        return error('请填写 d / M / T / sigma_b', code=400)
    return success(calc_shaft_fatigue(d=d, M=M, T=T, sigma_b=sigma_b))


@bp.post('/shaft/critical-speed')
def shaft_critical_api():
    """轴临界转速"""
    d, L, m_shaft, m_disk = _p('d', 'L', 'm_shaft', 'm_disk')
    if d is None or L is None:
        return error('请填写 d / L', code=400)
    E = _p('E')[0] or 206000
    n_max = _p('n_max')[0]
    return success(calc_critical_speed(d=d, L=L, m_shaft=m_shaft, m_disk=m_disk, E=E, n_max=n_max))


# ============== 轴承 ==============

@bp.post('/bearing/life')
def bearing_life_api():
    """轴承基本寿命"""
    C, P, n = _p('C_kN', 'P_kN', 'n_rpm')
    if C is None or P is None or n is None:
        return error('请填写 C_kN / P_kN / n_rpm', code=400)
    bt = (request.get_json(silent=True) or {}).get('bearing_type', 'ball')
    return success(bearing_life(C_kN=C, P_kN=P, n_rpm=n, bearing_type=str(bt)))


@bp.post('/bearing/equivalent')
def bearing_equiv_api():
    """轴承当量动载荷"""
    Fr, Fa = _p('Fr_kN', 'Fa_kN')
    if Fr is None:
        return error('请填写 Fr_kN', code=400)
    X = _p('X')[0] or 0.56
    Y = _p('Y')[0] or 1.5
    return success(equivalent_load(Fr_kN=Fr, Fa_kN=Fa or 0, X=X, Y=Y))


@bp.post('/bearing/static-check')
def bearing_static_api():
    """轴承静强度校核"""
    C0, P0 = _p('C0_kN', 'P0_kN')
    if C0 is None or P0 is None:
        return error('请填写 C0_kN / P0_kN', code=400)
    safety = _p('safety')[0] or 1.0
    return success(bearing_static_check(C0_kN=C0, P0_kN=P0, safety=safety))


@bp.post('/bearing/life-modified')
def bearing_life_mod_api():
    """修正后轴承寿命 (ISO 281)"""
    C, P, n = _p('C', 'P', 'n')
    if C is None or P is None or n is None:
        return error('请填写 C / P / n', code=400)
    a1 = _p('a1')[0] or 1.0
    a23 = _p('a23')[0] or 1.0
    bt = (request.get_json(silent=True) or {}).get('bearing_type', 'ball')
    from backend.calculations.bearing_full import calc_bearing_life_modified
    return success(calc_bearing_life_modified(C=C, P=P, n=n, a1=a1, a23=a23, bearing_type=str(bt)))


@bp.post('/bearing/extended')
def bearing_extended_api():
    """轴承详细参数 (修正寿命/最小载荷/极限转速/粘度比)"""
    from backend.calculations.bearing_full import (
        calc_bearing_life_modified, calc_bearing_min_load, calc_bearing_speed_limit,
    )
    d = request.get_json(silent=True) or {}
    C = safe_float(d.get('C'))
    P = safe_float(d.get('P'))
    n = safe_float(d.get('n_rpm'))
    C0 = safe_float(d.get('C0'))
    dm = safe_float(d.get('dm'))
    bt = d.get('bearing_type', 'ball')

    result = {}
    if all(x is not None for x in (C, P, n)):
        result['life_modified'] = calc_bearing_life_modified(C=C, P=P, n=n, bearing_type=str(bt))
    if all(x is not None for x in (C0, n, dm)):
        result['min_load'] = calc_bearing_min_load(C0=C0, n=n, dm=dm, bearing_type=str(bt))
    if dm is not None and n is not None:
        result['speed_limit'] = calc_bearing_speed_limit(dm=dm, n=n, bearing_type=str(bt))
    return success(result)


# ============== 梁 ==============

@bp.post('/beam/section')
def beam_section_api():
    """截面惯性矩/模量"""
    d = request.get_json(silent=True) or {}
    shape = d.pop('shape', 'rect')
    return success(beam_section_inertia(shape, **d))


@bp.post('/beam/calc')
def beam_calc_api():
    """梁计算"""
    d = request.get_json(silent=True) or {}
    bt = d.get('beam_type')
    L = safe_float(d.get('L'))
    loads = d.get('loads', [])
    E = safe_float(d.get('E'))
    I = safe_float(d.get('I'))
    if not all([bt, L, loads, E, I]):
        return error('请填写 beam_type / L / loads / E / I', code=400)
    return success(calc_beam(beam_type=bt, L=L, loads=loads, E=E, I=I))


# ============== 疲劳 ==============

@bp.post('/fatigue/sn-curve')
def fatigue_sn_api():
    """S-N 曲线"""
    S_ut, N1, N2 = _p('S_ut', 'N1', 'N2')
    Se_prime = _p('Se_prime')[0]
    N_target = _p('N_target')[0]
    if S_ut is None or N1 is None or N2 is None:
        return error('请填写 S_ut / N1 / N2', code=400)
    return success(calc_sn_curve(S_ut=S_ut, N1=N1, N2=N2, Se_prime=Se_prime, N_target=N_target))


@bp.post('/fatigue/stress-conc')
def fatigue_stress_api():
    """应力集中系数"""
    K_t, q = _p('K_t', 'q')
    mt = (request.get_json(silent=True) or {}).get('material_type', 'steel')
    if K_t is None or q is None:
        return error('请填写 K_t / q', code=400)
    return success(calc_stress_concentration(K_t=K_t, q=q, material_type=str(mt)))


@bp.post('/fatigue/miner')
def fatigue_miner_api():
    """Miner 累积损伤"""
    d = request.get_json(silent=True) or {}
    stress_levels = d.get('stress_levels', [])
    cycles = d.get('cycles', [])
    S_ut = safe_float(d.get('S_ut'))
    Se = safe_float(d.get('Se'))
    if not (stress_levels and cycles and S_ut and Se):
        return error('请填写 stress_levels / cycles / S_ut / Se', code=400)
    return success(calc_miner_damage(stress_levels=stress_levels, cycles=cycles,
                                     S_ut=S_ut, Se=Se))


# ============== 工具 ==============

def _p(*keys, defaults=None):
    """从 JSON 提取多参数"""
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
