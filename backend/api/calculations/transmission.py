"""传动类计算 API: 齿轮/蜗杆/带/链/凸轮

URL 前缀: /api/calc
端点命名: <module>/<function>
"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.utils.convert import safe_float, safe_int

# 计算函数导入
from backend.calculations.gear import (
    spur_gear_params, spur_gear_mesh, gear_motor_selection, rack_and_pinion,
    gear_bending_strength, gear_contact_strength, gear_force,
)
from backend.calculations.mechanics import planetary_gear, compound_gear_train
from backend.calculations.worm import worm_geometry, worm_efficiency
from backend.calculations.belt import vbelt_calc, synchronous_belt_calc
from backend.calculations.chain import (
    roller_chain_params, chain_length, chain_power_capacity, conveyor_chain_tension,
)
from backend.calculations.cam import (
    cam_motion_uniform, cam_motion_sine, cam_motion_cosine,
    cam_motion_modified_trapezoid, cam_profile_points, cam_analysis,
    indexer_selection, divider_general,
)

bp = Blueprint('transmission', __name__, url_prefix='/api/calc')


def _params(*keys, defaults=None):
    """从请求 JSON 中按顺序提取参数, 找不到的填默认"""
    d = request.get_json(silent=True) or {}
    defaults = defaults or {}
    out = []
    for i, k in enumerate(keys):
        v = d.get(k)
        if v is None or v == '':
            if k in defaults:
                out.append(defaults[k])
            else:
                out.append(None)
        else:
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                out.append(v)  # 字符串 (如 cam motion_type)
    return out


# ============== 齿轮 ==============

@bp.post('/gear/spur')
def gear_spur():
    """直齿轮几何参数"""
    m, z, alpha, ha, c, x = _params('module', 'teeth', 'pressure_angle', 'addendum_coef', 'clearance_coef', 'modification_coefficient',
                                    defaults={'pressure_angle': 20, 'addendum_coef': 1.0, 'clearance_coef': 0.25, 'modification_coefficient': 0})
    if m is None or z is None:
        return error('请填写模数 (module) 和齿数 (teeth)', code=400)
    return success(spur_gear_params(m, int(z), alpha, ha, c, x))


@bp.post('/gear/mesh')
def gear_mesh():
    """齿轮副啮合参数"""
    m, z1, z2, alpha, ha, c, x1, x2 = _params(
        'module', 'teeth1', 'teeth2', 'pressure_angle', 'addendum_coef', 'clearance_coef', 'x1', 'x2',
        defaults={'pressure_angle': 20, 'addendum_coef': 1.0, 'clearance_coef': 0.25, 'x1': 0, 'x2': 0})
    if m is None or z1 is None or z2 is None:
        return error('请填写模数和两个齿数', code=400)
    return success(spur_gear_mesh(m, int(z1), int(z2), alpha, ha, c, x1, x2))


@bp.post('/gear/motor')
def gear_motor():
    """齿轮减速机选型"""
    p, n1, ratio, eff = _params('power_kw', 'n1_rpm', 'ratio', 'efficiency',
                                defaults={'efficiency': 0.95})
    if p is None or n1 is None or ratio is None:
        return error('请填写功率/输入转速/传动比', code=400)
    return success(gear_motor_selection(p, n1, ratio, eff))


@bp.post('/gear/rack')
def gear_rack():
    """齿条-小齿轮"""
    m, z, F, v, alpha = _params('module', 'z_pinion', 'force_n', 'speed_mps', 'pressure_angle',
                                defaults={'pressure_angle': 20})
    if m is None or z is None:
        return error('请填写模数和齿数', code=400)
    return success(rack_and_pinion(m, int(z), F, v, alpha))


@bp.post('/gear/bending')
def gear_bending():
    """齿轮弯曲强度"""
    Ft, b, m, YF, YS, Yb, K = _params('Ft_N', 'b_mm', 'm_mm', 'YF', 'YS', 'Yb', 'K',
                                      defaults={'YF': 2.5, 'YS': 1.6, 'Yb': 1.0, 'K': 1.3})
    if Ft is None or b is None or m is None:
        return error('请填写 Ft_N / b_mm / m_mm', code=400)
    return success(gear_bending_strength(Ft, b, m, YF, YS, Yb, K))


@bp.post('/gear/contact')
def gear_contact():
    """齿轮接触强度"""
    Ft, b, d1, u, K, ZE, ZH, Ze = _params('Ft_N', 'b_mm', 'd1_mm', 'u', 'K', 'ZE', 'ZH', 'Ze',
                                          defaults={'K': 1.3, 'ZE': 189.8, 'ZH': 2.5, 'Ze': 0.87})
    if Ft is None or b is None or d1 is None or u is None:
        return error('请填写 Ft_N / b_mm / d1_mm / u', code=400)
    return success(gear_contact_strength(Ft, b, d1, u, K, ZE, ZH, Ze))


@bp.post('/gear/force')
def gear_force_api():
    """齿轮受力分析"""
    T, d, alpha, beta = _params('torque_Nm', 'd_mm', 'pressure_angle', 'helix_angle',
                                defaults={'pressure_angle': 20, 'helix_angle': 0})
    if T is None or d is None:
        return error('请填写扭矩 (Nm) 和分度圆直径 (mm)', code=400)
    return success(gear_force(T, d, alpha, beta))


@bp.post('/gear/planetary')
def gear_planetary():
    """行星齿轮"""
    z_sun, z_ring, z_planet = _params('z_sun', 'z_ring', 'z_planet')
    n_sun = safe_float((request.get_json(silent=True) or {}).get('n_sun'))
    if any(x is None for x in (z_sun, z_ring, z_planet)):
        return error('请填写太阳轮/齿圈/行星轮齿数', code=400)
    # 行星齿轮 carrier_input=True 默认太阳轮固定, 行星架为输出
    result = planetary_gear(int(z_sun), int(z_ring), int(z_planet))
    if n_sun is not None:
        result['input_speed_rpm'] = n_sun
    return success(result)


@bp.post('/gear/compound')
def gear_compound():
    """复合齿轮系 (多级) — teeth_list: [[z1,z2],[z3,z4],...]"""
    d = request.get_json(silent=True) or {}
    teeth_list = d.get('teeth_list', [])
    if not isinstance(teeth_list, list) or not teeth_list:
        return error('teeth_list 必须是非空数组, 形如 [[z1,z2],[z3,z4]]', code=400)
    try:
        # 转换为 (z1, z2) 元组列表
        teeth_tuples = [(float(t[0]), float(t[1])) for t in teeth_list]
    except (TypeError, ValueError, IndexError):
        return error('teeth_list 元素必须是 [z_driver, z_driven]', code=400)
    return success(compound_gear_train(teeth_tuples))


# ============== 蜗杆 ==============

@bp.post('/worm/geometry')
def worm_geometry_api():
    """蜗杆副几何"""
    m, z1, z2, q = _params('m', 'z1', 'z2', 'q', defaults={'q': 10})
    if m is None or z1 is None or z2 is None:
        return error('请填写 m / z1 / z2', code=400)
    return success(worm_geometry(m, int(z1), int(z2), q))


@bp.post('/worm/efficiency')
def worm_efficiency_api():
    """蜗杆效率"""
    gamma, fv = _params('gamma_deg', 'fv', defaults={'fv': 0.06})
    if gamma is None:
        return error('请填写导程角 gamma_deg', code=400)
    return success(worm_efficiency(gamma, fv))


# ============== 带 ==============

@bp.post('/belt/vbelt')
def belt_vbelt():
    """V 带传动"""
    section, P, n1, ratio, a = _params('section', 'power_kw', 'n1_rpm', 'ratio', 'center_distance_mm')
    if any(x is None for x in (P, n1, ratio, a)) or not section:
        return error('请填写 section / power_kw / n1_rpm / ratio / center_distance_mm', code=400)
    return success(vbelt_calc(str(section), P, n1, ratio, a))


@bp.post('/belt/synchronous')
def belt_synchronous():
    """同步带传动"""
    btype, P, n1, ratio, z1, a = _params('belt_type', 'power_kw', 'n1_rpm', 'ratio', 'z1', 'center_distance_mm')
    if any(x is None for x in (P, n1, ratio)) or not btype:
        return error('请填写 belt_type / power_kw / n1_rpm / ratio', code=400)
    return success(synchronous_belt_calc(str(btype), P, n1, ratio, z1, a))


# ============== 链 ==============

@bp.post('/chain/sprocket')
def chain_sprocket():
    """滚子链链轮参数"""
    pitch, z = _params('pitch', 'teeth')
    if pitch is None or z is None:
        return error('请填写 pitch / teeth', code=400)
    return success(roller_chain_params(pitch, int(z)))


@bp.post('/chain/length')
def chain_length_api():
    """链条长度计算"""
    pitch, z1, z2, a = _params('pitch', 'teeth1', 'teeth2', 'center_distance')
    if any(x is None for x in (pitch, z1, z2, a)):
        return error('请填写 pitch / teeth1 / teeth2 / center_distance', code=400)
    return success(chain_length(pitch, int(z1), int(z2), a))


@bp.post('/chain/conveyor')
def chain_conveyor():
    """输送链张力"""
    m, v, L, mu = _params('mass_kg', 'speed_mps', 'length_m', 'mu',
                          defaults={'mu': 0.15})
    if any(x is None for x in (m, v, L)):
        return error('请填写 mass_kg / speed_mps / length_m', code=400)
    return success(conveyor_chain_tension(m, v, L, mu))


# ============== 凸轮 ==============

@bp.post('/cam/profile')
def cam_profile():
    """凸轮轮廓点"""
    d = request.get_json(silent=True) or {}
    rb = safe_float(d.get('rb'))
    h = safe_float(d.get('h'))
    beta = safe_float(d.get('beta_deg'))
    motion_type = d.get('motion_type', 'sine') or 'sine'
    if any(x is None for x in (rb, h, beta)):
        return error('请填写 rb / h / beta_deg', code=400)
    return success(cam_profile_points(rb, h, beta, str(motion_type),
                                      int(d.get('num_points', 36) or 36)))


@bp.post('/cam/analysis')
def cam_analysis_api():
    """凸轮运动学分析"""
    beta, h, motion_type = _params('beta_deg', 'h', 'motion_type',
                                   defaults={'motion_type': 'sine'})
    if beta is None or h is None:
        return error('请填写 beta_deg / h', code=400)
    return success(cam_analysis(beta, h, str(motion_type or 'sine')))


@bp.post('/cam/indexer')
def cam_indexer():
    """凸轮分度器选型"""
    d = request.get_json(silent=True) or {}
    T = safe_float(d.get('load_torque_nm'))
    index_angle = safe_float(d.get('index_angle_deg'))
    dwell_angle = safe_float(d.get('dwell_angle_deg'))
    rpm_input = safe_float(d.get('rpm_input')) or 30
    num_stations = safe_float(d.get('num_stations')) or 8
    if any(x is None for x in (T, index_angle, dwell_angle)):
        return error('请填写 load_torque_nm / index_angle_deg / dwell_angle_deg', code=400)
    return success(indexer_selection(T, index_angle, dwell_angle, rpm_input, num_stations))


@bp.post('/cam/divider')
def cam_divider():
    """通用分度器"""
    d = request.get_json(silent=True) or {}
    pitch_angle = safe_float(d.get('pitch_angle_deg'))
    table_d = safe_float(d.get('table_diameter_mm'))
    mass = safe_float(d.get('load_mass_kg'))
    rpm_input = safe_float(d.get('rpm_input')) or 30
    if any(x is None for x in (pitch_angle, table_d, mass)):
        return error('请填写 pitch_angle_deg / table_diameter_mm / load_mass_kg', code=400)
    return success(divider_general(pitch_angle, table_d, mass, rpm_input))
