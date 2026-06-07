"""
凸轮 / 分割器计算模块
参考：机械设计常用计算表 - 正弦加速度凸轮 / 分割器选型
"""
import math

# ============ 凸轮从动件运动规律 ============


def cam_motion_uniform(beta, h, theta):
    """
    等速运动 (直线) 位移曲线
    
    参数:
        beta: 推程角 (rad)
        h: 总升程 (mm)
        theta: 当前角度 (rad, 0~beta)
    """
    s = h * theta / beta
    v = h / beta
    a = 0
    return s, v, a


def cam_motion_sine(beta, h, theta):
    """
    正弦加速度运动
    
    s = h[θ/β - sin(2πθ/β)/(2π)]
    v = h/β[1 - cos(2πθ/β)]
    a = 2πh/β²·sin(2πθ/β)
    """
    phi = theta / beta
    s = h * (phi - math.sin(2 * math.pi * phi) / (2 * math.pi))
    v = h / beta * (1 - math.cos(2 * math.pi * phi))
    a = 2 * math.pi * h / (beta * beta) * math.sin(2 * math.pi * phi)
    return s, v, a


def cam_motion_cosine(beta, h, theta):
    """
    余弦加速度运动
    
    s = h/2[1 - cos(πθ/β)]
    v = πh/(2β)·sin(πθ/β)
    a = π²h/(2β²)·cos(πθ/β)
    """
    phi = theta / beta
    s = h / 2 * (1 - math.cos(math.pi * phi))
    v = math.pi * h / (2 * beta) * math.sin(math.pi * phi)
    a = math.pi * math.pi * h / (2 * beta * beta) * math.cos(math.pi * phi)
    return s, v, a


def cam_motion_modified_trapezoid(beta, h, theta):
    """
    修正梯形加速度运动曲线
    多项式近似，适应高速凸轮
    """
    phi = theta / beta
    if phi <= 0.125:
        s = h * (4 * phi**2 / (2 + math.pi))
        v = h / beta * (8 * phi / (2 + math.pi))
        a = h / (beta * beta) * (8 / (2 + math.pi))
    elif phi <= 0.375:
        t = 4 * phi - 1
        s = h * ((4 * phi - 1)**2 / (8 * (2 + math.pi)) + 1 / (2 * (2 + math.pi)))
        v = h / beta * (t / (2 + math.pi))
        a = h / (beta * beta) * (4 / (2 + math.pi))
    else:
        # 简化近似
        s = cam_motion_sine(beta, h, theta)[0]
        v = cam_motion_sine(beta, h, theta)[1]
        a = cam_motion_sine(beta, h, theta)[2]
    return s, v, a


def cam_profile_points(rb, h, beta_deg, motion_type='sine', num_points=36):
    """
    计算凸轮轮廓坐标（对心直动从动件）
    
    参数:
        rb: 基圆半径 (mm)
        h: 升程 (mm)
        beta_deg: 推程角 (度)
        motion_type: 运动规律 (sine/cosine/uniform/modified_trapezoid)
        num_points: 输出点数
    
    返回: [{'theta': deg, 'x': mm, 'y': mm, 's': mm}, ...]
    """
    motion_funcs = {
        'sine': cam_motion_sine,
        'cosine': cam_motion_cosine,
        'uniform': cam_motion_uniform,
        'modified_trapezoid': cam_motion_modified_trapezoid,
    }
    func = motion_funcs.get(motion_type, cam_motion_sine)
    beta = math.radians(beta_deg)
    
    points = []
    for i in range(num_points + 1):
        theta = beta * i / num_points
        s, v, a = func(beta, h, theta)
        r = rb + s
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        points.append({
            'theta_deg': round(math.degrees(theta), 1),
            's_mm': round(s, 3),
            'v': round(v, 3),
            'a': round(a, 3),
            'x_mm': round(x, 3),
            'y_mm': round(y, 3),
            'r_mm': round(r, 3),
        })
    return points


def cam_analysis(beta_deg, h, motion_type='sine'):
    """
    凸轮运动特性分析
    
    返回: 最大速度/加速度/跃度特征值
    """
    beta = math.radians(beta_deg)
    
    # 特征值系数 (Cv, Ca)
    coeff = {
        'sine':       {'Cv': 2.00, 'Ca': 6.28, 'desc': '正弦加速度 — 高速轻载，无冲击'},  # noqa: E241
        'cosine':     {'Cv': 1.57, 'Ca': 4.93, 'desc': '余弦加速度 — 中高速，柔性冲击'},  # noqa: E241
        'uniform':    {'Cv': 1.00, 'Ca': 0,    'desc': '等速 — 低速，刚性冲击'},  # noqa: E241
        'modified_trapezoid': {'Cv': 1.76, 'Ca': 4.89, 'desc': '修正梯形 — 高速，综合性能好'},  # noqa: E241
    }
    c = coeff.get(motion_type, coeff['sine'])
    
    v_max = c['Cv'] * h / beta
    a_max = c['Ca'] * h / (beta * beta)
    
    return {
        'motion_type': motion_type,
        'motion_desc': c['desc'],
        'max_velocity': round(v_max, 3),
        'max_acceleration': round(a_max, 3),
        'cv_factor': c['Cv'],
        'ca_factor': c['Ca'],
    }


# ============ 凸轮分割器 ============

def indexer_selection(load_torque_nm, index_angle_deg, dwell_angle_deg,
                      rpm_input, num_stations, safety=1.5):
    """
    凸轮分割器选型计算
    
    参数:
        load_torque_nm: 负载扭矩 (N·m)
        index_angle_deg: 分割器动程角 (度)
        dwell_angle_deg: 静止角 (度)
        rpm_input: 入力轴转速
        num_stations: 工位数
        safety: 安全系数
    """
    # total_angle = index_angle_deg + dwell_angle_deg
    
    # 出力轴扭矩（考虑安全系数）
    T_out = load_torque_nm * safety
    
    # 入力轴扭矩（近似）
    ratio = 360 / index_angle_deg
    T_in = T_out / ratio  # 忽略摩擦
    
    # 分割时间
    t_index = index_angle_deg / (rpm_input * 360 / 60)  # 秒
    t_dwell = dwell_angle_deg / (rpm_input * 360 / 60)  # 秒
    
    # 输入功率
    P_kw = 2 * math.pi * rpm_input * T_in / 60000
    
    return {
        'num_stations': num_stations,
        'index_angle_deg': index_angle_deg,
        'dwell_angle_deg': dwell_angle_deg,
        'input_rpm': rpm_input,
        'output_torque_nm': round(T_out, 2),
        'input_torque_nm': round(T_in, 3),
        'ratio': round(ratio, 1),
        'index_time_s': round(t_index, 3),
        'dwell_time_s': round(t_dwell, 3),
        'cycle_time_s': round(t_index + t_dwell, 3),
        'power_kw': round(P_kw, 4),
        'safety_factor': safety,
        'note': f'建议选型型号参考: {num_stations}工位，出力扭矩≥{round(T_out)}N·m',
    }


def divider_general(pitch_angle_deg, table_diameter_mm, load_mass_kg,
                    rpm_input, safety=1.5):
    """
    分度盘通用选型计算
    
    参数:
        pitch_angle_deg: 分度角 (度)
        table_diameter_mm: 转盘直径 (mm)
        load_mass_kg: 负载总质量 (kg)
        rpm_input: 入力轴转速
    """
    stations = round(360 / pitch_angle_deg)
    
    # 转盘转动惯量
    J_table = 0.5 * load_mass_kg * (table_diameter_mm / 2000)**2  # kg·m²
    
    # 角加速度（近似）
    omega_out = 2 * math.pi / (60 / rpm_input * stations)  # rad/s
    alpha_out = omega_out / 0.1  # 假定加速时间0.1s
    
    T_inertia = J_table * alpha_out  # N·m
    
    return {
        'stations': stations,
        'pitch_angle_deg': pitch_angle_deg,
        'table_moment_of_inertia_kgm2': round(J_table, 4),
        'angular_acceleration_rad_s2': round(alpha_out, 2),
        'inertia_torque_nm': round(T_inertia, 2),
        'input_rpm': rpm_input,
    }
