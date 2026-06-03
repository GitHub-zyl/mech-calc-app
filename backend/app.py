"""
机械设计常用计算表 - Flask Web App
"""
import os
import sys
import json
from flask import Flask, render_template, request, jsonify

# 确保能找到calculations模块
sys.path.insert(0, os.path.dirname(__file__))

from calculations.gear import spur_gear_params, spur_gear_mesh, gear_motor_selection, rack_and_pinion
from calculations.spring import coil_spring_compression, coil_spring_stress, spring_deflection
from calculations.thread import metric_thread_basic, tap_drill_diameter, bolt_preload_torque
from calculations.chain import roller_chain_params, chain_length, chain_power_capacity, conveyor_chain_tension
from calculations.belt import vbelt_calc, synchronous_belt_calc
from calculations.cam import cam_profile_points, cam_analysis, indexer_selection, divider_general
from calculations.press import blanking_force, stripping_force, v_bending_force, u_bending_force, embossing_force, shear_force
from calculations.tolerance import shaft_tolerance, hole_tolerance, fit_calculation, FIT_RECOMMENDATIONS
from calculations.hydraulic import pipe_pressure_loss, thin_orifice_flow, accumulator_selection, hydraulic_shock, oil_tank_heat_balance, oil_viscosity_temp
from calculations.coupling import coupling_gear_torque, coupling_universal, oring_groove, htd_synchronous_belt, motor_sync_speed, motor_torque, motor_current_estimate, MOTOR_KNOWLEDGE
from calculations.strength import section_properties, column_buckling, column_stability_check, weld_fillet_stress, weld_butt_stress, key_strength, pin_strength, interference_fit, press_fit_force, rivet_strength, adhesive_strength
from calculations.mechanics import linear_motion, rotational_motion, centrifugal_force, momentum, angular_momentum, impulse, work_energy, power_calc, friction, mass_inertia, parallel_axis_theorem, radius_of_gyration, spring_mass_vibration, torsional_vibration, critical_shaft_speed, simple_pendulum, flywheel_energy, brake_torque, lead_screw_efficiency, screw_jack_torque, planetary_gear, compound_gear_train
from calculations.bearing import bearing_life, equivalent_load, bearing_static_check
from calculations.worm import worm_geometry, worm_efficiency
from calculations.gear import gear_bending_strength, gear_contact_strength, gear_force
from calculations.thermo import conduction, convection, thermal_expansion, thermal_stress, bernoulli, orifice_flow, pipe_velocity, weir_flow, ideal_gas
from calculations.shaft import calc_shaft_torsion, calc_shaft_combined, calc_shaft_fatigue, calc_critical_speed
from calculations.beam import beam_section_inertia, calc_beam
from calculations.bearing_full import calc_bearing_life_modified, calc_bearing_min_load, calc_bearing_speed_limit
from calculations.fatigue import calc_sn_curve, calc_stress_concentration, calc_miner_damage
from calculations.pneumatic import calc_cylinder_force, calc_cylinder_air_consumption, calc_pipe_flow_rate, calc_air_receiver_volume
from calculations.surface import calc_roughness_convert, calc_hardness_convert, calc_surface_texture
from calculations.brake import calc_disc_brake_torque, calc_band_brake_torque, calc_clutch_energy
from calculations.weld import calc_fillet_weld_stress, calc_butt_weld_stress
from utils.units import convert_all, list_categories, PHYSICAL_CONSTANTS

# 模板/静态文件路径（支持多种运行场景）
_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_template_dir = os.path.join(_base_dir, 'templates')
_static_dir = os.path.join(_base_dir, 'static')
if not os.path.isdir(_template_dir):
    # 从exe运行时尝试同级目录
    import sys
    _exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    _template_dir = os.path.join(_exe_dir, 'templates')
    _static_dir = os.path.join(_exe_dir, 'static')

import sys
# Debug info removed for production
app = Flask(__name__,
    template_folder=_template_dir,
    static_folder=_static_dir)

# 提供data目录的静态文件
@app.route('/data/<path:filename>')
def serve_data(filename):
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    filepath = os.path.join(data_dir, filename)
    if os.path.exists(filepath) and filename.endswith('.json'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return app.response_class(f.read(), mimetype='application/json')
    return jsonify({'error': 'File not found'}), 404

# 加载数据
data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted_data.json')
DB = {}
if os.path.exists(data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        DB = json.load(f)

def safe_float(v, default=None):
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default

# ============ API路由 ============

@app.route('/')
def index():
    # 直接读取HTML文件，避免Jinja2模板路径问题
    idx_path = os.path.join(_template_dir, 'index.html')
    if os.path.exists(idx_path):
        with open(idx_path, 'r', encoding='utf-8') as f:
            return app.response_class(f.read(), mimetype='text/html')
    return f'<h1>Template not found at {idx_path}</h1><p>base={_base_dir}</p>', 404

@app.route('/api/data/<category>')
def get_data(category):
    """查询数据库：材料、钢材、铝材等"""
    if category == 'materials':
        q = request.args.get('q', '').lower()
        if q:
            results = [m for m in DB.get('materials', []) if q in m.get('name', '').lower()]
        else:
            results = DB.get('materials', [])
        return jsonify(results[:100])
    elif category == 'steels':
        return jsonify(DB.get('steel_grades', []))
    elif category == 'aluminum':
        return jsonify(DB.get('aluminum_grades', []))
    elif category == 'plastics':
        return jsonify(DB.get('plastics', []))
    elif category == 'bearings':
        return jsonify(DB.get('bearings_deep_groove', []))
    return jsonify({'error': '未知类别'})

# ============ 计算API ============

@app.route('/api/calculate/gear/spur', methods=['POST'])
def calc_spur_gear():
    """直齿圆柱齿轮基本参数"""
    data = request.json
    m = safe_float(data.get('module'))
    z = safe_float(data.get('teeth'))
    alpha = safe_float(data.get('pressure_angle', 20))
    x = safe_float(data.get('modification_coefficient', 0))
    
    if not m or not z:
        return jsonify({'error': '请填写模数(m)和齿数(z)'})
    
    result = spur_gear_params(m, int(z), alpha, x=x)
    return jsonify(result)

@app.route('/api/calculate/gear/mesh', methods=['POST'])
def calc_gear_mesh():
    """齿轮啮合计算"""
    data = request.json
    m = safe_float(data.get('module'))
    z1 = safe_float(data.get('teeth1'))
    z2 = safe_float(data.get('teeth2'))
    alpha = safe_float(data.get('pressure_angle', 20))
    x1 = safe_float(data.get('x1', 0))
    x2 = safe_float(data.get('x2', 0))
    
    if not all([m, z1, z2]):
        return jsonify({'error': '请填写模数(m)和齿数(z1, z2)'})
    
    result = spur_gear_mesh(m, int(z1), int(z2), alpha, x1=x1, x2=x2)
    return jsonify(result)

@app.route('/api/calculate/gear/motor', methods=['POST'])
def calc_gear_motor():
    """电机选型"""
    data = request.json
    p = safe_float(data.get('power'))
    n = safe_float(data.get('speed'))
    ratio = safe_float(data.get('ratio'))
    eff = safe_float(data.get('efficiency', 0.95))
    
    if not all([p, n, ratio]):
        return jsonify({'error': '请填写功率、转速和传动比'})
    
    result = gear_motor_selection(p, n, ratio, eff)
    return jsonify(result)

@app.route('/api/calculate/gear/rack', methods=['POST'])
def calc_rack():
    """齿轮齿条"""
    data = request.json
    m = safe_float(data.get('module'))
    z = safe_float(data.get('teeth'))
    force = safe_float(data.get('force'))
    speed = safe_float(data.get('speed'))
    
    if not m or not z:
        return jsonify({'error': '请填写模数(m)和齿数(z)'})
    
    result = rack_and_pinion(m, int(z), force, speed)
    return jsonify(result)

@app.route('/api/calculate/spring/compression', methods=['POST'])
def calc_spring():
    """弹簧计算"""
    data = request.json
    d = safe_float(data.get('wire_diameter'))
    Dm = safe_float(data.get('mean_diameter'))
    n = safe_float(data.get('coils'))
    material = data.get('material', '弹簧钢')
    
    if not all([d, Dm, n]):
        return jsonify({'error': '请填写线径、中径和有效圈数'})
    
    result = coil_spring_compression(d, Dm, int(n), material=material)
    
    # 如果有载荷，加应力校核
    F = safe_float(data.get('force'))
    if F:
        stress = coil_spring_stress(d, Dm, F, material)
        result['stress_check'] = stress
        deflection = spring_deflection(result['stiffness_n_per_mm'], F)
        result['deflection'] = deflection
    
    return jsonify(result)

@app.route('/api/calculate/thread/metric', methods=['POST'])
def calc_thread():
    """螺纹计算"""
    data = request.json
    d = safe_float(data.get('nominal_diameter'))
    p = safe_float(data.get('pitch'))
    
    if not d:
        return jsonify({'error': '请填写公称直径'})
    if not p:
        # 自动推断标准螺距
        if d <= 3: p = 0.5
        elif d <= 6: p = 0.75
        elif d <= 10: p = 1.0
        elif d <= 16: p = 1.5
        elif d <= 24: p = 2.0
        elif d <= 36: p = 3.0
        else: p = 3.5
    
    result = metric_thread_basic(d, p)
    return jsonify(result)

@app.route('/api/calculate/thread/tapdrill', methods=['POST'])
def calc_tap_drill():
    """攻丝底孔"""
    data = request.json
    spec = data.get('thread_spec', '')
    if not spec:
        return jsonify({'error': '请填写螺纹规格（如 M6, M8x1）'})
    result = tap_drill_diameter(spec)
    return jsonify(result)

@app.route('/api/calculate/thread/bolt', methods=['POST'])
def calc_bolt():
    """螺栓扭矩"""
    data = request.json
    d = safe_float(data.get('diameter'))
    grade = data.get('grade', '8.8')
    
    if not d:
        return jsonify({'error': '请填写螺栓直径'})
    result = bolt_preload_torque(d, grade)
    return jsonify(result)

@app.route('/api/calculate/chain/sprocket', methods=['POST'])
def calc_sprocket():
    """链轮参数"""
    data = request.json
    p = safe_float(data.get('pitch'))
    z = safe_float(data.get('teeth'))
    
    if not p or not z:
        return jsonify({'error': '请填写节距(p)和齿数(z)'})
    result = roller_chain_params(p, int(z))
    return jsonify(result)

@app.route('/api/calculate/chain/length', methods=['POST'])
def calc_chain_length():
    """链条长度"""
    data = request.json
    p = safe_float(data.get('pitch'))
    z1 = safe_float(data.get('teeth1'))
    z2 = safe_float(data.get('teeth2'))
    a = safe_float(data.get('center_distance'))
    
    if not all([p, z1, z2, a]):
        return jsonify({'error': '请填写节距、两链轮齿数和中心距'})
    result = chain_length(p, int(z1), int(z2), a)
    return jsonify(result)

@app.route('/api/calculate/chain/conveyor', methods=['POST'])
def calc_conveyor():
    """输送链张力"""
    data = request.json
    m = safe_float(data.get('mass'))
    v = safe_float(data.get('speed'))
    l = safe_float(data.get('length'))
    mu = safe_float(data.get('friction', 0.15))
    
    if not all([m, v, l]):
        return jsonify({'error': '请填写质量、速度和长度'})
    result = conveyor_chain_tension(m, v, l, mu)
    return jsonify(result)

# ============ 材料数据搜索API ============

@app.route('/api/material/search')
def search_material():
    """搜索材料"""
    q = request.args.get('q', '').lower()
    if not q:
        return jsonify([])
    
    results = []
    for m in DB.get('materials', []):
        name = m.get('name', '').lower()
        if q in name:
            results.append(m)
    return jsonify(results[:50])

@app.route('/api/material/info')
def material_info():
    """获取材料详细信息"""
    name = request.args.get('name', '')
    for m in DB.get('materials', []):
        if m.get('name') == name:
            return jsonify(m)
    return jsonify({'error': '未找到'})

# ============ 新增模块API ============

# --- 三角皮带 ---
@app.route('/api/calculate/belt/vbelt', methods=['POST'])
def calc_vbelt():
    data = request.json
    section = data.get('section', 'A')
    p = safe_float(data.get('power'))
    n = safe_float(data.get('speed'))
    ratio = safe_float(data.get('ratio'))
    a = safe_float(data.get('center_distance'))
    if not all([p, n, ratio, a]):
        return jsonify({'error': '请填写功率、转速、传动比和中心距'})
    result = vbelt_calc(section.upper(), p, n, ratio, a)
    return jsonify(result)

# --- 同步带 ---
@app.route('/api/calculate/belt/synchronous', methods=['POST'])
def calc_sync_belt():
    data = request.json
    btype = data.get('belt_type', 'L')
    p = safe_float(data.get('power'))
    n = safe_float(data.get('speed'))
    ratio = safe_float(data.get('ratio'))
    z1 = safe_float(data.get('teeth_small'))
    a = safe_float(data.get('center_distance'))
    if not all([p, n, ratio]):
        return jsonify({'error': '请填写功率、转速和传动比'})
    z1_int = int(z1) if z1 else None
    result = synchronous_belt_calc(btype.upper(), p, n, ratio, z1_int, a)
    return jsonify(result)

# --- 凸轮轮廓 ---
@app.route('/api/calculate/cam/profile', methods=['POST'])
def calc_cam_profile():
    data = request.json
    rb = safe_float(data.get('base_radius'))
    h = safe_float(data.get('stroke'))
    beta = safe_float(data.get('angle'))
    motion = data.get('motion_type', 'sine')
    pts = int(data.get('points', 36))
    if not all([rb, h, beta]):
        return jsonify({'error': '请填写基圆半径、升程和推程角'})
    result = cam_profile_points(rb, h, beta, motion, min(pts, 360))
    analysis = cam_analysis(beta, h, motion)
    return jsonify({'points': result, 'analysis': analysis})

# --- 凸轮分析 ---
@app.route('/api/calculate/cam/analysis', methods=['POST'])
def calc_cam_analysis():
    data = request.json
    beta = safe_float(data.get('angle'))
    h = safe_float(data.get('stroke'))
    motion = data.get('motion_type', 'sine')
    if not all([beta, h]):
        return jsonify({'error': '请填写推程角和升程'})
    result = cam_analysis(beta, h, motion)
    return jsonify(result)

# --- 分割器 ---
@app.route('/api/calculate/cam/indexer', methods=['POST'])
def calc_indexer():
    data = request.json
    T = safe_float(data.get('load_torque'))
    idx = safe_float(data.get('index_angle'))
    dwell = safe_float(data.get('dwell_angle'))
    rpm = safe_float(data.get('rpm'))
    stations = int(data.get('stations', 4))
    safety = safe_float(data.get('safety', 1.5))
    if not all([T, idx, dwell, rpm]):
        return jsonify({'error': '请填写负载扭矩、动程角、静止角和转速'})
    result = indexer_selection(T, idx, dwell, rpm, stations, safety)
    return jsonify(result)

# --- 分度盘 ---
@app.route('/api/calculate/cam/divider', methods=['POST'])
def calc_divider():
    data = request.json
    pitch = safe_float(data.get('pitch_angle'))
    diam = safe_float(data.get('table_diameter'))
    mass = safe_float(data.get('mass'))
    rpm = safe_float(data.get('rpm'))
    if not all([pitch, diam, mass, rpm]):
        return jsonify({'error': '请填写分度角、转盘直径、质量和转速'})
    result = divider_general(pitch, diam, mass, rpm)
    return jsonify(result)

# --- 冲裁力 ---
@app.route('/api/calculate/press/blanking', methods=['POST'])
def calc_blanking():
    data = request.json
    L = safe_float(data.get('perimeter'))
    t = safe_float(data.get('thickness'))
    tau = safe_float(data.get('shear_strength'))
    if not all([L, t, tau]):
        return jsonify({'error': '请填写冲裁周长、板厚和抗剪强度'})
    result = blanking_force(L, t, tau)
    # 卸料力可选
    mat = data.get('material_type', 'steel')
    strip = stripping_force(result['blanking_force_kN'], mat)
    result['stripping'] = strip
    return jsonify(result)

# --- V型弯曲 ---
@app.route('/api/calculate/press/vbend', methods=['POST'])
def calc_vbend():
    data = request.json
    b = safe_float(data.get('width'))
    t = safe_float(data.get('thickness'))
    sigma = safe_float(data.get('tensile_strength'))
    w = safe_float(data.get('die_opening'))
    if not all([b, t, sigma, w]):
        return jsonify({'error': '请填写宽度、厚度、抗拉强度和凹模开口'})
    result = v_bending_force(b, t, sigma, w)
    return jsonify(result)

# --- U型弯曲 ---
@app.route('/api/calculate/press/ubend', methods=['POST'])
def calc_ubend():
    data = request.json
    b = safe_float(data.get('width'))
    t = safe_float(data.get('thickness'))
    sigma = safe_float(data.get('tensile_strength'))
    w = safe_float(data.get('die_opening'))
    if not all([b, t, sigma, w]):
        return jsonify({'error': '请填写宽度、厚度、抗拉强度和凹模开口'})
    result = u_bending_force(b, t, sigma, w)
    return jsonify(result)

# --- 压印 ---
@app.route('/api/calculate/press/embossing', methods=['POST'])
def calc_embossing():
    data = request.json
    area = safe_float(data.get('area'))
    sigma = safe_float(data.get('tensile_strength'))
    if not all([area, sigma]):
        return jsonify({'error': '请填写压印面积和抗拉强度'})
    result = embossing_force(area, sigma)
    return jsonify(result)

# --- 剪切力 ---
@app.route('/api/calculate/press/shear', methods=['POST'])
def calc_shear():
    data = request.json
    area = safe_float(data.get('area'))
    tau = safe_float(data.get('shear_strength'))
    if not all([area, tau]):
        return jsonify({'error': '请填写剪切面积和抗剪强度'})
    result = shear_force(area, tau)
    return jsonify(result)

# --- 轴的公差 ---
@app.route('/api/calculate/tolerance/shaft', methods=['POST'])
def calc_shaft_tol():
    data = request.json
    d = safe_float(data.get('nominal'))
    spec = data.get('spec', 'h7')
    if not d:
        return jsonify({'error': '请填写公称尺寸'})
    result = shaft_tolerance(d, spec)
    return jsonify(result)

# --- 孔的公差 ---
@app.route('/api/calculate/tolerance/hole', methods=['POST'])
def calc_hole_tol():
    data = request.json
    d = safe_float(data.get('nominal'))
    spec = data.get('spec', 'H7')
    if not d:
        return jsonify({'error': '请填写公称尺寸'})
    result = hole_tolerance(d, spec)
    return jsonify(result)

# --- 配合计算 ---
@app.route('/api/calculate/tolerance/fit', methods=['POST'])
def calc_fit():
    data = request.json
    d = safe_float(data.get('nominal'))
    hole_spec = data.get('hole_spec', 'H7')
    shaft_spec = data.get('shaft_spec', 'h6')
    if not d:
        return jsonify({'error': '请填写公称尺寸'})
    result = fit_calculation(d, hole_spec, shaft_spec)
    return jsonify(result)

# --- 推荐配合 ---
@app.route('/api/data/fit_recommendations')
def get_fit_recos():
    return jsonify(FIT_RECOMMENDATIONS)

# ============ 液压系统 ============

@app.route('/api/calculate/hydraulic/pipe', methods=['POST'])
def calc_hyd_pipe():
    d = request.json
    r = pipe_pressure_loss(
        safe_float(d.get('flow')),
        safe_float(d.get('diameter')),
        safe_float(d.get('length')),
        safe_float(d.get('viscosity', 46)),
        safe_float(d.get('density', 870)),
        d.get('pipe_type', 'metal')
    )
    return jsonify(r)

@app.route('/api/calculate/hydraulic/orifice', methods=['POST'])
def calc_hyd_orifice():
    d = request.json
    r = thin_orifice_flow(
        safe_float(d.get('diameter')),
        safe_float(d.get('pressure_diff')),
        safe_float(d.get('discharge_coeff', 0.62))
    )
    return jsonify(r)

@app.route('/api/calculate/hydraulic/accumulator', methods=['POST'])
def calc_hyd_accumulator():
    d = request.json
    r = accumulator_selection(
        safe_float(d.get('volume')),
        safe_float(d.get('precharge_pressure')),
        safe_float(d.get('min_pressure')),
        safe_float(d.get('max_pressure'))
    )
    return jsonify(r)

@app.route('/api/calculate/hydraulic/shock', methods=['POST'])
def calc_hyd_shock():
    d = request.json
    r = hydraulic_shock(
        v1_mps=safe_float(d.get('v1')),
        v2_mps=safe_float(d.get('v2')),
        pipe_length_m=safe_float(d.get('pipe_length')),
        bulk_modulus_mpa=safe_float(d.get('bulk_modulus', 1400)),
        density_kgm3=safe_float(d.get('density', 870)),
        pipe_diam_mm=safe_float(d.get('pipe_diameter', 20)),
        wall_thickness_mm=safe_float(d.get('wall_thickness', 2)),
        close_time_s=safe_float(d.get('close_time'))
    )
    return jsonify(r)

@app.route('/api/calculate/hydraulic/tank', methods=['POST'])
def calc_hyd_tank():
    d = request.json
    r = oil_tank_heat_balance(
        safe_float(d.get('power')),
        safe_float(d.get('volume')),
        safe_float(d.get('temp_rise', 30))
    )
    return jsonify(r)

@app.route('/api/calculate/hydraulic/viscosity', methods=['POST'])
def calc_hyd_visc():
    d = request.json
    r = oil_viscosity_temp(
        safe_float(d.get('nu_40', 46)),
        safe_float(d.get('temperature', 40)),
        safe_float(d.get('vi', 100))
    )
    return jsonify(r)

# ============ 联轴器 / O型圈 / 圆弧齿同步带 ============

@app.route('/api/calculate/coupling/gear', methods=['POST'])
def calc_coup_gear():
    d = request.json
    r = coupling_gear_torque(
        safe_float(d.get('power')), safe_float(d.get('speed')),
        safe_float(d.get('safety', 1.5))
    )
    return jsonify(r)

@app.route('/api/calculate/coupling/universal', methods=['POST'])
def calc_coup_uni():
    d = request.json
    r = coupling_universal(
        safe_float(d.get('power')), safe_float(d.get('speed')),
        safe_float(d.get('angle'))
    )
    return jsonify(r)

@app.route('/api/calculate/coupling/oring', methods=['POST'])
def calc_oring():
    d = request.json
    r = oring_groove(safe_float(d.get('section_diameter')))
    return jsonify(r)

@app.route('/api/calculate/coupling/htd', methods=['POST'])
def calc_htd():
    d = request.json
    r = htd_synchronous_belt(
        d.get('belt_type', '8M'), safe_float(d.get('power')),
        safe_float(d.get('speed')), safe_float(d.get('ratio')),
        safe_float(d.get('teeth_small'))
    )
    return jsonify(r)

# ============ 电机常识 ============

@app.route('/api/calculate/motor/speed', methods=['POST'])
def calc_motor_speed():
    d = request.json
    r = motor_sync_speed(int(d.get('poles', 4)), safe_float(d.get('freq', 50)))
    return jsonify(r)

@app.route('/api/calculate/motor/torque', methods=['POST'])
def calc_motor_torque():
    d = request.json
    r = motor_torque(
        safe_float(d.get('power')),
        safe_float(d.get('speed')),
        int(d.get('poles', 4)),
        safe_float(d.get('freq', 50))
    )
    return jsonify(r)

@app.route('/api/calculate/motor/current', methods=['POST'])
def calc_motor_current():
    d = request.json
    r = motor_current_estimate(safe_float(d.get('power')), safe_float(d.get('voltage', 380)))
    return jsonify(r)

@app.route('/api/data/motor_knowledge')
def get_motor_knowledge():
    return jsonify(MOTOR_KNOWLEDGE)

# ============ 材料力学 ============

@app.route('/api/calculate/strength/section', methods=['POST'])
def calc_strength_section():
    d = request.json
    shape = d.get('shape', 'rect')
    params = {k: safe_float(v) for k, v in d.get('params', {}).items()}
    if not params:
        return jsonify({'error': '请填写截面参数'})
    r = section_properties(shape, params)
    return jsonify(r)

@app.route('/api/calculate/strength/column', methods=['POST'])
def calc_strength_column():
    d = request.json
    r = column_stability_check(
        safe_float(d.get('force')), safe_float(d.get('area')),
        safe_float(d.get('elastic_modulus', 206000)),
        safe_float(d.get('length')), safe_float(d.get('inertia')),
        safe_float(d.get('mu', 1.0)), safe_float(d.get('yield_strength', 235)),
        safe_float(d.get('safety', 2.0))
    )
    return jsonify(r)

@app.route('/api/calculate/strength/weld', methods=['POST'])
def calc_strength_weld():
    d = request.json
    r = weld_fillet_stress(
        safe_float(d.get('force')), safe_float(d.get('leg')),
        safe_float(d.get('length')), int(d.get('num', 2))
    )
    return jsonify(r)

@app.route('/api/calculate/strength/key', methods=['POST'])
def calc_strength_key():
    d = request.json
    r = key_strength(
        safe_float(d.get('torque')) * 1000, safe_float(d.get('shaft_diameter')),
        safe_float(d.get('width')), safe_float(d.get('height')),
        safe_float(d.get('length'))
    )
    return jsonify(r)

@app.route('/api/calculate/strength/pin', methods=['POST'])
def calc_strength_pin():
    d = request.json
    r = pin_strength(
        safe_float(d.get('force')), safe_float(d.get('diameter')),
        int(d.get('num', 1))
    )
    return jsonify(r)

@app.route('/api/calculate/strength/interference', methods=['POST'])
def calc_strength_interference():
    d = request.json
    r = interference_fit(
        safe_float(d.get('shaft_diameter')), safe_float(d.get('interference')),
        safe_float(d.get('hub_od')), safe_float(d.get('elastic_modulus', 206000)),
        safe_float(d.get('elastic_modulus_hub', 206000)),
        safe_float(d.get('poisson_shaft', 0.3)),
        safe_float(d.get('poisson_hub', 0.3)),
        safe_float(d.get('friction', 0.15)),
        safe_float(d.get('length'))
    )
    return jsonify(r)

@app.route('/api/calculate/strength/pressfit', methods=['POST'])
def calc_strength_pressfit():
    d = request.json
    r = press_fit_force(
        safe_float(d.get('shaft_diameter')), safe_float(d.get('interference')),
        safe_float(d.get('hub_od')), safe_float(d.get('length')),
        safe_float(d.get('friction', 0.15))
    )
    return jsonify(r)

# ============ 15. 运动学/动力学 ============

@app.route('/api/calculate/mechanics/linear', methods=['POST'])
def calc_mec_linear():
    d = request.json
    r = linear_motion(safe_float(d.get('v0', 0)), safe_float(d.get('a', 0)), safe_float(d.get('t', 0)), safe_float(d.get('s')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/rotational', methods=['POST'])
def calc_mec_rot():
    d = request.json
    r = rotational_motion(safe_float(d.get('omega0', 0)), safe_float(d.get('alpha', 0)), safe_float(d.get('t', 0)))
    return jsonify(r)

@app.route('/api/calculate/mechanics/centrifugal', methods=['POST'])
def calc_mec_cf():
    d = request.json
    r = centrifugal_force(safe_float(d.get('mass')), safe_float(d.get('radius')),
                          safe_float(d.get('omega')), safe_float(d.get('rpm')),
                          safe_float(d.get('velocity')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/momentum', methods=['POST'])
def calc_mec_mom():
    d = request.json
    r = momentum(safe_float(d.get('mass')), safe_float(d.get('velocity')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/angular_momentum', methods=['POST'])
def calc_mec_ang():
    d = request.json
    r = angular_momentum(safe_float(d.get('inertia')), safe_float(d.get('omega')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/impulse', methods=['POST'])
def calc_mec_imp():
    d = request.json
    r = impulse(safe_float(d.get('force')), safe_float(d.get('time')), safe_float(d.get('mass')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/work_energy', methods=['POST'])
def calc_mec_work():
    d = request.json
    r = work_energy(safe_float(d.get('force')), safe_float(d.get('distance')),
                    safe_float(d.get('torque')), safe_float(d.get('angle')),
                    safe_float(d.get('mass')), safe_float(d.get('velocity')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/power', methods=['POST'])
def calc_mec_power():
    d = request.json
    r = power_calc(safe_float(d.get('force')), safe_float(d.get('velocity')),
                   safe_float(d.get('torque')), safe_float(d.get('omega')),
                   safe_float(d.get('rpm')), safe_float(d.get('work')),
                   safe_float(d.get('time')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/friction', methods=['POST'])
def calc_mec_friction():
    d = request.json
    r = friction(safe_float(d.get('normal_force', 100)),
                 safe_float(d.get('mu_static', 0)),
                 safe_float(d.get('mu_kinetic', 0)),
                 safe_float(d.get('mu_rolling', 0)))
    return jsonify(r)

@app.route('/api/calculate/mechanics/inertia', methods=['POST'])
def calc_mec_inertia():
    d = request.json
    r = mass_inertia(d.get('shape', 'solid_cylinder'),
                     safe_float(d.get('mass')),
                     safe_float(d.get('density')),
                     **{k: safe_float(v) for k, v in d.get('dims', {}).items() if v is not None})
    return jsonify(r)

# ============ 16. 振动 ============

@app.route('/api/calculate/vibration/spring_mass', methods=['POST'])
def calc_vib_sm():
    d = request.json
    r = spring_mass_vibration(safe_float(d.get('stiffness')), safe_float(d.get('mass')),
                             safe_float(d.get('damping', 0)))
    return jsonify(r)

@app.route('/api/calculate/vibration/torsional', methods=['POST'])
def calc_vib_tor():
    d = request.json
    r = torsional_vibration(safe_float(d.get('shear_modulus', 79000)),
                           safe_float(d.get('j')),
                           safe_float(d.get('length')),
                           safe_float(d.get('disc_inertia')))
    return jsonify(r)

@app.route('/api/calculate/vibration/critical_shaft', methods=['POST'])
def calc_vib_crit():
    d = request.json
    r = critical_shaft_speed(safe_float(d.get('elastic_modulus', 206000)),
                            safe_float(d.get('inertia')),
                            safe_float(d.get('mass')),
                            safe_float(d.get('length')))
    return jsonify(r)

@app.route('/api/calculate/vibration/pendulum', methods=['POST'])
def calc_vib_pend():
    d = request.json
    r = simple_pendulum(safe_float(d.get('length')))
    return jsonify(r)

# ============ 17. 飞轮/螺旋/轮系 ============

@app.route('/api/calculate/mechanics/flywheel', methods=['POST'])
def calc_flywheel():
    d = request.json
    r = flywheel_energy(safe_float(d.get('inertia')), safe_float(d.get('omega')),
                       safe_float(d.get('rpm')))
    return jsonify(r)

@app.route('/api/calculate/mechanics/leadscrew', methods=['POST'])
def calc_leadscrew():
    d = request.json
    r = lead_screw_efficiency(safe_float(d.get('diameter')), safe_float(d.get('pitch')),
                             safe_float(d.get('friction', 0.15)))
    return jsonify(r)

@app.route('/api/calculate/mechanics/screwjack', methods=['POST'])
def calc_screwjack():
    d = request.json
    r = screw_jack_torque(safe_float(d.get('load')), safe_float(d.get('diameter')),
                         safe_float(d.get('pitch')), safe_float(d.get('friction', 0.15)))
    return jsonify(r)

@app.route('/api/calculate/gear/planetary', methods=['POST'])
def calc_planetary():
    d = request.json
    r = planetary_gear(int(d.get('sun_teeth', 20)), int(d.get('ring_teeth', 60)),
                       int(d.get('planet_teeth', 20)))
    return jsonify(r)

@app.route('/api/calculate/gear/compound', methods=['POST'])
def calc_compound():
    d = request.json
    stages = d.get('stages', [(20, 60)])
    r = compound_gear_train(stages)
    return jsonify(r)

# ============ 18. 热力学/流体 ============

@app.route('/api/calculate/thermal/conduction', methods=['POST'])
def calc_th_cond():
    d = request.json
    r = conduction(safe_float(d.get('q')), safe_float(d.get('k')),
                  safe_float(d.get('area')), safe_float(d.get('dt')),
                  safe_float(d.get('thickness')))
    return jsonify(r)

@app.route('/api/calculate/thermal/convection', methods=['POST'])
def calc_th_conv():
    d = request.json
    r = convection(safe_float(d.get('q')), safe_float(d.get('h')),
                  safe_float(d.get('area')), safe_float(d.get('dt')))
    return jsonify(r)

@app.route('/api/calculate/thermal/expansion', methods=['POST'])
def calc_th_exp():
    d = request.json
    r = thermal_expansion(safe_float(d.get('length')), safe_float(d.get('dt')),
                         safe_float(d.get('alpha', 1.2e-5)))
    return jsonify(r)

@app.route('/api/calculate/thermal/stress', methods=['POST'])
def calc_th_stress():
    d = request.json
    r = thermal_stress(safe_float(d.get('elastic_modulus', 206000)),
                      safe_float(d.get('dt')),
                      safe_float(d.get('alpha', 1.2e-5)))
    return jsonify(r)

@app.route('/api/calculate/fluid/bernoulli', methods=['POST'])
def calc_fl_bern():
    d = request.json
    r = bernoulli(safe_float(d.get('p1')), safe_float(d.get('p2')),
                 safe_float(d.get('v1')), safe_float(d.get('v2')),
                 safe_float(d.get('h1', 0)), safe_float(d.get('h2', 0)),
                 safe_float(d.get('density', 1000)))
    return jsonify(r)

@app.route('/api/calculate/fluid/orifice', methods=['POST'])
def calc_fl_orifice():
    d = request.json
    r = orifice_flow(safe_float(d.get('diameter')), safe_float(d.get('pressure_drop')),
                    safe_float(d.get('cd', 0.62)), safe_float(d.get('density', 1000)))
    return jsonify(r)

@app.route('/api/calculate/fluid/pipe_velocity', methods=['POST'])
def calc_fl_pipe_vel():
    d = request.json
    r = pipe_velocity(safe_float(d.get('flow_m3s')), safe_float(d.get('flow_lpm')),
                     safe_float(d.get('diameter')))
    return jsonify(r)

@app.route('/api/calculate/fluid/gas', methods=['POST'])
def calc_fl_gas():
    d = request.json
    r = ideal_gas(safe_float(d.get('pressure')), safe_float(d.get('volume')),
                 safe_float(d.get('temperature')),
                 safe_float(d.get('moles')), safe_float(d.get('mass')))
    return jsonify(r)

# ============ 19. 单位换算 ============

@app.route('/api/units/categories')
def get_unit_categories():
    return jsonify(list_categories())

@app.route('/api/units/convert', methods=['POST'])
def convert_units():
    d = request.json
    r = convert_all(safe_float(d.get('value', 1)),
                   d.get('from', 'mm'), d.get('to', 'm'),
                   d.get('category', 'length'))
    return jsonify(r)

@app.route('/api/units/constants')
def get_constants():
    return jsonify(PHYSICAL_CONSTANTS)

# ============ 20. 轴承/蜗杆/铆接/粘接/齿轮强度 ============

@app.route('/api/calculate/bearing/life', methods=['POST'])
def calc_bearing_life():
    d = request.json
    r = bearing_life(safe_float(d.get('C')), safe_float(d.get('P')),
                     safe_float(d.get('n')), d.get('type', 'ball'))
    return jsonify(r)

@app.route('/api/calculate/bearing/equivalent', methods=['POST'])
def calc_bearing_equiv():
    d = request.json
    r = equivalent_load(safe_float(d.get('Fr')), safe_float(d.get('Fa')),
                        safe_float(d.get('X', 0.56)), safe_float(d.get('Y', 1.5)))
    return jsonify(r)

@app.route('/api/calculate/worm/geometry', methods=['POST'])
def calc_worm_geo():
    d = request.json
    r = worm_geometry(safe_float(d.get('m')), int(d.get('z1', 1)),
                      int(d.get('z2', 30)), int(d.get('q', 10)))
    return jsonify(r)

@app.route('/api/calculate/worm/efficiency', methods=['POST'])
def calc_worm_eff():
    d = request.json
    r = worm_efficiency(safe_float(d.get('gamma')), safe_float(d.get('fv', 0.06)))
    return jsonify(r)

@app.route('/api/calculate/strength/rivet', methods=['POST'])
def calc_strength_rivet():
    d = request.json
    r = rivet_strength(safe_float(d.get('force')), safe_float(d.get('diameter')),
                       safe_float(d.get('t_min')), int(d.get('n', 1)),
                       int(d.get('shear_planes', 1)))
    return jsonify(r)

@app.route('/api/calculate/strength/adhesive', methods=['POST'])
def calc_strength_adhesive():
    d = request.json
    r = adhesive_strength(safe_float(d.get('force')), safe_float(d.get('width')),
                          safe_float(d.get('length')))
    return jsonify(r)

@app.route('/api/calculate/gear/bending', methods=['POST'])
def calc_gear_bending():
    d = request.json
    r = gear_bending_strength(safe_float(d.get('Ft')), safe_float(d.get('b')),
                              safe_float(d.get('m')), safe_float(d.get('YF', 2.5)),
                              safe_float(d.get('YS', 1.6)), safe_float(d.get('Yb', 1.0)),
                              safe_float(d.get('K', 1.3)))
    return jsonify(r)

@app.route('/api/calculate/gear/contact', methods=['POST'])
def calc_gear_contact():
    d = request.json
    r = gear_contact_strength(safe_float(d.get('Ft')), safe_float(d.get('b')),
                              safe_float(d.get('d1')), safe_float(d.get('u')),
                              safe_float(d.get('K', 1.3)))
    return jsonify(r)

@app.route('/api/calculate/gear/force', methods=['POST'])
def calc_gear_force():
    d = request.json
    r = gear_force(safe_float(d.get('torque')), safe_float(d.get('diameter')),
                   safe_float(d.get('alpha', 20)), safe_float(d.get('beta', 0)))
    return jsonify(r)

# ============ 21. 轴设计计算 ============

@app.route('/api/calculate/shaft/torsion', methods=['POST'])
def api_shaft_torsion():
    try:
        data = request.get_json(force=True)
        result = calc_shaft_torsion(
            d=safe_float(data.get('d')),
            P=safe_float(data.get('P', data.get('power'))),
            n=safe_float(data.get('n', data.get('speed'))),
            tau_allow=safe_float(data.get('tau_allow', 40))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/shaft/combined', methods=['POST'])
def api_shaft_combined():
    try:
        data = request.get_json(force=True)
        result = calc_shaft_combined(
            d=safe_float(data.get('d')),
            M=safe_float(data.get('M')),
            T=safe_float(data.get('T')),
            alpha=safe_float(data.get('alpha', 1.0)),
            sigma_allow=safe_float(data.get('sigma_allow'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/shaft/fatigue', methods=['POST'])
def api_shaft_fatigue():
    try:
        data = request.get_json(force=True)
        result = calc_shaft_fatigue(
            d=safe_float(data.get('d')),
            M=safe_float(data.get('M')),
            T=safe_float(data.get('T')),
            sigma_b=safe_float(data.get('sigma_b')),
            K_sigma=safe_float(data.get('K_sigma', 1.0)),
            K_tau=safe_float(data.get('K_tau', 1.0)),
            beta=safe_float(data.get('beta', 1.0)),
            epsilon_sigma=safe_float(data.get('epsilon_sigma', 1.0)),
            epsilon_tau=safe_float(data.get('epsilon_tau', 1.0)),
            psi_sigma=safe_float(data.get('psi_sigma', 0.2)),
            psi_tau=safe_float(data.get('psi_tau', 0.1))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/shaft/critical_speed', methods=['POST'])
def api_shaft_critical_speed():
    try:
        data = request.get_json(force=True)
        result = calc_critical_speed(
            d=safe_float(data.get('d')),
            L=safe_float(data.get('L')),
            m_shaft=safe_float(data.get('m_shaft')),
            m_disk=safe_float(data.get('m_disk')),
            E=safe_float(data.get('E', 206000)),
            n_max=safe_float(data.get('n_max'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============ 22. 梁的弯矩/挠度 ============

@app.route('/api/calculate/beam/section', methods=['POST'])
def api_beam_section():
    try:
        data = request.get_json(force=True)
        shape = data.get('shape', 'circle')
        dims = {k: safe_float(v) for k, v in data.get('dims', {}).items()}
        result = beam_section_inertia(shape, **dims)
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/beam/calc', methods=['POST'])
def api_beam_calc():
    try:
        data = request.get_json(force=True)
        result = calc_beam(
            beam_type=data.get('beam_type'),
            L=safe_float(data.get('L')),
            loads=data.get('loads', []),
            E=safe_float(data.get('E')),
            I=safe_float(data.get('I'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============ 23. 滚动轴承详细选型 ============

@app.route('/api/calculate/bearing/life_modified', methods=['POST'])
def api_bearing_life_modified():
    try:
        data = request.get_json(force=True)
        result = calc_bearing_life_modified(
            C=safe_float(data.get('C')),
            P=safe_float(data.get('P')),
            n=safe_float(data.get('n')),
            a1=safe_float(data.get('a1', 1.0)),
            a23=safe_float(data.get('a23', 1.0)),
            bearing_type=data.get('bearing_type', 'ball')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/bearing/min_load', methods=['POST'])
def api_bearing_min_load():
    try:
        data = request.get_json(force=True)
        result = calc_bearing_min_load(
            C0=safe_float(data.get('C0')),
            n=safe_float(data.get('n')),
            dm=safe_float(data.get('dm')),
            bearing_type=data.get('bearing_type', 'ball')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/bearing/speed_limit', methods=['POST'])
def api_bearing_speed_limit():
    try:
        data = request.get_json(force=True)
        result = calc_bearing_speed_limit(
            dm=safe_float(data.get('dm')),
            n=safe_float(data.get('n')),
            bearing_type=data.get('bearing_type', 'deep_groove_ball'),
            lubrication=data.get('lubrication', 'grease')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============ 24. 疲劳强度 ============

@app.route('/api/calculate/fatigue/sn_curve', methods=['POST'])
def api_sn_curve():
    try:
        data = request.get_json(force=True)
        result = calc_sn_curve(
            S_ut=safe_float(data.get('S_ut')),
            N1=safe_float(data.get('N1')),
            N2=safe_float(data.get('N2')),
            Se_prime=safe_float(data.get('Se_prime')),
            N_target=safe_float(data.get('N_target'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/fatigue/stress_conc', methods=['POST'])
def api_stress_conc():
    try:
        data = request.get_json(force=True)
        result = calc_stress_concentration(
            K_t=safe_float(data.get('K_t')),
            q=safe_float(data.get('q')),
            material_type=data.get('material_type', 'steel')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/fatigue/miner', methods=['POST'])
def api_miner_damage():
    try:
        data = request.get_json(force=True)
        result = calc_miner_damage(
            stress_levels=data.get('stress_levels'),
            cycles=data.get('cycles'),
            S_ut=safe_float(data.get('S_ut')),
            Se=safe_float(data.get('Se'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============ 25. 气动系统 ============

@app.route('/api/calculate/pneumatic/cylinder_force', methods=['POST'])
def api_cylinder_force():
    try:
        data = request.get_json(force=True)
        result = calc_cylinder_force(
            D=safe_float(data.get('D')),
            d_rod=safe_float(data.get('d_rod')),
            p=safe_float(data.get('p')),
            action_type=data.get('action_type', 'extend')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/pneumatic/air_consumption', methods=['POST'])
def api_air_consumption():
    try:
        data = request.get_json(force=True)
        result = calc_cylinder_air_consumption(
            D=safe_float(data.get('D')),
            stroke=safe_float(data.get('stroke')),
            p=safe_float(data.get('p')),
            n_cycle=safe_float(data.get('n_cycle')),
            action_type=data.get('action_type', 'double')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/pneumatic/pipe_flow', methods=['POST'])
def api_pipe_flow():
    try:
        data = request.get_json(force=True)
        result = calc_pipe_flow_rate(
            d=safe_float(data.get('d')),
            p1=safe_float(data.get('p1')),
            p2=safe_float(data.get('p2')),
            L=safe_float(data.get('L')),
            T=safe_float(data.get('T', 293))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/pneumatic/receiver', methods=['POST'])
def api_air_receiver():
    try:
        data = request.get_json(force=True)
        result = calc_air_receiver_volume(
            Q=safe_float(data.get('Q')),
            p_max=safe_float(data.get('p_max')),
            p_min=safe_float(data.get('p_min')),
            t_cycle=safe_float(data.get('t_cycle'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============ 26. 表面粗糙度与硬度 ============

@app.route('/api/calculate/surface/roughness', methods=['POST'])
def api_roughness():
    try:
        data = request.get_json(force=True)
        result = calc_roughness_convert(
            Ra=safe_float(data.get('Ra'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/surface/hardness', methods=['POST'])
def api_hardness():
    try:
        data = request.get_json(force=True)
        result = calc_hardness_convert(
            value=safe_float(data.get('value')),
            from_type=data.get('from_type', 'HB'),
            to_type=data.get('to_type', 'HRC')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/surface/texture', methods=['POST'])
def api_surface_texture():
    try:
        data = request.get_json(force=True)
        result = calc_surface_texture(
            Ra=safe_float(data.get('Ra')),
            process=data.get('process')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============ 27. 制动器与离合器 ============

@app.route('/api/calculate/brake/disc', methods=['POST'])
def api_disc_brake():
    try:
        data = request.get_json(force=True)
        result = calc_disc_brake_torque(
            p=safe_float(data.get('p')),
            mu=safe_float(data.get('mu')),
            D_o=safe_float(data.get('D_o')),
            D_i=safe_float(data.get('D_i')),
            n_faces=int(data.get('n_faces', 2))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/brake/band', methods=['POST'])
def api_band_brake():
    try:
        data = request.get_json(force=True)
        result = calc_band_brake_torque(
            F1=safe_float(data.get('F1')),
            mu=safe_float(data.get('mu')),
            theta_deg=safe_float(data.get('theta_deg')),
            r=safe_float(data.get('r'))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/brake/clutch', methods=['POST'])
def api_clutch_energy():
    try:
        data = request.get_json(force=True)
        result = calc_clutch_energy(
            W=safe_float(data.get('W')),
            J=safe_float(data.get('J')),
            omega1=safe_float(data.get('omega1')),
            omega2=safe_float(data.get('omega2')),
            m_drum=safe_float(data.get('m_drum')),
            c_specific=safe_float(data.get('c_specific', 500))
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ============ 28. 焊接计算扩展 ============

@app.route('/api/calculate/weld/fillet', methods=['POST'])
def api_fillet_weld():
    try:
        data = request.get_json(force=True)
        result = calc_fillet_weld_stress(
            F=safe_float(data.get('F')),
            M=safe_float(data.get('M')),
            h=safe_float(data.get('h')),
            Lw=safe_float(data.get('Lw')),
            load_type=data.get('load_type', 'tension')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/calculate/weld/butt', methods=['POST'])
def api_butt_weld():
    try:
        data = request.get_json(force=True)
        result = calc_butt_weld_stress(
            F=safe_float(data.get('F')),
            M=safe_float(data.get('M')),
            t=safe_float(data.get('t')),
            Lw=safe_float(data.get('Lw')),
            load_type=data.get('load_type', 'tension')
        )
        result['status'] = 'success'
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9091)
