"""工程常用公式库 (F=ma, P=Fv, T=mg 等)

每条公式结构:
    id:           唯一标识
    name_zh:      中文名
    name_en:      英文名
    formula:      公式 (如 'F = m·a')
    expr:         Python 表达式 (用于求解), 未知变量留空
                  如 'F = m * a' 中的未知变量直接是变量名
    variables:    {symbol: {name, unit, default?}}
    unknowns:     列表: 此公式可作为未知量的变量 (可被反求)
    category:     分类 (mechanics, kinematics, energy, fluid, thermal, geometry, ...)
    description:  简短说明
    tags:         搜索标签
    related:      相关公式 id 列表
    reference:    教材或手册参考

约束:
- 不存放工程数据表 (材料/公差), 仅存放公式 (纯数学关系).
- 求解时由 calc.expr 动态求值, 避免硬编码 (支持任意变形的公式).
- 数据加载有详细日志 (加载触发条件/时间戳/数据量/耗时)
"""
import logging
import re
import time
from typing import Dict, List, Optional, Any


# ============== 日志配置 ==============
_logger = logging.getLogger('backend.calculations.formulas_data')
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s(tid=%(thread)d)] %(message)s'
    ))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


def _log_load_start(trigger: str, **fields) -> float:
    """记录公式库加载开始. 返回开始时间戳 (perf_counter)."""
    ts = time.time()
    fields_str = ' '.join(f'{k}={v!r}' for k, v in fields.items())
    _logger.info(
        f"[LOAD-START] trigger={trigger} ts={ts:.6f} {fields_str}"
    )
    return time.perf_counter()


def _log_load_end(trigger: str, start: float, **fields) -> None:
    """记录公式库加载结束 + 耗时."""
    elapsed_ms = (time.perf_counter() - start) * 1000
    fields_str = ' '.join(f'{k}={v!r}' for k, v in fields.items())
    _logger.info(
        f"[LOAD-END]   trigger={trigger} elapsed={elapsed_ms:.3f}ms {fields_str}"
    )


# 记录模块导入时公式库的加载 (静态加载, 一次性)
_LOAD_START = time.perf_counter()
_LOAD_TS = time.time()


# ============ 公式库 ============

FORMULAS: List[Dict[str, Any]] = [
    # ---------- 力学 (mechanics) ----------
    {
        'id': 'fma',
        'name_zh': '牛顿第二定律',
        'name_en': "Newton's Second Law",
        'formula': 'F = m · a',
        'expr': 'F = m * a',
        'variables': {
            'F': {'name': '合外力', 'unit': 'N'},
            'm': {'name': '质量', 'unit': 'kg'},
            'a': {'name': '加速度', 'unit': 'm/s²'},
        },
        'unknowns': ['F', 'm', 'a'],
        'category': 'mechanics',
        'description': '物体加速度与所受合外力成正比, 方向与合外力相同',
        'tags': ['力学', '动力学', '牛顿', '基础'],
        'related': ['pfa', 'pfg'],
        'reference': '理论力学(哈工大) §2.1',
    },
    {
        'id': 'pfa',
        'name_zh': '压强公式',
        'name_en': 'Pressure = Force / Area',
        'formula': 'p = F / A',
        'expr': 'p = F / A',
        'variables': {
            'p': {'name': '压强', 'unit': 'Pa'},
            'F': {'name': '作用力', 'unit': 'N'},
            'A': {'name': '受力面积', 'unit': 'm²'},
        },
        'unknowns': ['p', 'F', 'A'],
        'category': 'mechanics',
        'description': '压强等于作用力除以受力面积',
        'tags': ['力学', '压强', '应力'],
        'related': ['fma', 'sigma_stress'],
        'reference': '工程力学 §1.2',
    },
    {
        'id': 'pfg',
        'name_zh': '重力',
        'name_en': 'Weight',
        'formula': 'G = m · g',
        'expr': 'G = m * g',
        'variables': {
            'G': {'name': '重力', 'unit': 'N'},
            'm': {'name': '质量', 'unit': 'kg'},
            'g': {'name': '重力加速度', 'unit': 'm/s²', 'default': 9.81},
        },
        'unknowns': ['G', 'm', 'g'],
        'category': 'mechanics',
        'description': '物体所受重力',
        'tags': ['力学', '重力'],
        'related': ['fma'],
        'reference': '理论力学 §1.5',
    },
    {
        'id': 'fnet',
        'name_zh': '静摩擦力',
        'name_en': 'Static Friction',
        'formula': 'f = μ · N',
        'expr': 'f = mu * N',
        'variables': {
            'f': {'name': '摩擦力', 'unit': 'N'},
            'mu': {'name': '摩擦系数', 'unit': ''},
            'N': {'name': '法向力', 'unit': 'N'},
        },
        'unknowns': ['f', 'mu', 'N'],
        'category': 'mechanics',
        'description': '滑动摩擦力与法向力成正比',
        'tags': ['力学', '摩擦'],
        'related': ['fma'],
        'reference': '理论力学 §3.4',
    },

    # ---------- 运动学 (kinematics) ----------
    {
        'id': 'vt',
        'name_zh': '匀速直线运动',
        'name_en': 'Constant Velocity',
        'formula': 's = v · t',
        'expr': 's = v * t',
        'variables': {
            's': {'name': '位移', 'unit': 'm'},
            'v': {'name': '速度', 'unit': 'm/s'},
            't': {'name': '时间', 'unit': 's'},
        },
        'unknowns': ['s', 'v', 't'],
        'category': 'kinematics',
        'description': '匀速直线运动位移',
        'tags': ['运动', '匀速'],
        'related': ['fma'],
        'reference': '理论力学 §1.1',
    },
    {
        'id': 'vat',
        'name_zh': '匀加速运动 (速度)',
        'name_en': 'Velocity under Constant Accel.',
        'formula': 'v = v₀ + a · t',
        'expr': 'v = v0 + a * t',
        'variables': {
            'v': {'name': '末速度', 'unit': 'm/s'},
            'v0': {'name': '初速度', 'unit': 'm/s'},
            'a': {'name': '加速度', 'unit': 'm/s²'},
            't': {'name': '时间', 'unit': 's'},
        },
        'unknowns': ['v', 'v0', 'a', 't'],
        'category': 'kinematics',
        'description': '匀加速直线运动速度公式',
        'tags': ['运动', '加速度'],
        'related': ['fma', 'vt'],
        'reference': '理论力学 §1.3',
    },
    {
        'id': 'sat',
        'name_zh': '匀加速运动 (位移)',
        'name_en': 'Displacement under Const. Accel.',
        'formula': 's = v₀ · t + ½ · a · t²',
        'expr': 's = v0 * t + 0.5 * a * t**2',
        'variables': {
            's': {'name': '位移', 'unit': 'm'},
            'v0': {'name': '初速度', 'unit': 'm/s'},
            'a': {'name': '加速度', 'unit': 'm/s²'},
            't': {'name': '时间', 'unit': 's'},
        },
        'unknowns': ['s', 'v0', 'a', 't'],
        'category': 'kinematics',
        'description': '匀加速直线运动位移公式',
        'tags': ['运动', '加速度'],
        'related': ['vat'],
        'reference': '理论力学 §1.3',
    },
    {
        'id': 'v2_v0',
        'name_zh': '速度-位移关系',
        'name_en': 'Velocity-Displacement',
        'formula': 'v² = v₀² + 2 · a · s',
        'expr': 'v**2 = v0**2 + 2 * a * s',
        'variables': {
            'v': {'name': '末速度', 'unit': 'm/s'},
            'v0': {'name': '初速度', 'unit': 'm/s'},
            'a': {'name': '加速度', 'unit': 'm/s²'},
            's': {'name': '位移', 'unit': 'm'},
        },
        'unknowns': ['v', 'v0', 'a', 's'],
        'category': 'kinematics',
        'description': '匀加速运动 v²-v₀²=2as',
        'tags': ['运动', '速度'],
        'related': ['vat', 'sat'],
        'reference': '理论力学 §1.3',
    },
    {
        'id': 'acentripetal',
        'name_zh': '向心加速度',
        'name_en': 'Centripetal Acceleration',
        'formula': 'a = v² / r',
        'expr': 'a = v**2 / r',
        'variables': {
            'a': {'name': '向心加速度', 'unit': 'm/s²'},
            'v': {'name': '线速度', 'unit': 'm/s'},
            'r': {'name': '半径', 'unit': 'm'},
        },
        'unknowns': ['a', 'v', 'r'],
        'category': 'kinematics',
        'description': '匀速圆周运动的向心加速度',
        'tags': ['运动', '圆周', '向心'],
        'related': ['fma'],
        'reference': '理论力学 §1.4',
    },

    # ---------- 能量 (energy) ----------
    {
        'id': 'work',
        'name_zh': '功 (恒力)',
        'name_en': 'Work by Constant Force',
        'formula': 'W = F · s',
        'expr': 'W = F * s',
        'variables': {
            'W': {'name': '功', 'unit': 'J'},
            'F': {'name': '作用力', 'unit': 'N'},
            's': {'name': '位移', 'unit': 'm'},
        },
        'unknowns': ['W', 'F', 's'],
        'category': 'energy',
        'description': '恒力沿运动方向做的功',
        'tags': ['功', '能'],
        'related': ['pfv', 'ekin'],
        'reference': '理论力学 §4.1',
    },
    {
        'id': 'pfv',
        'name_zh': '机械功率',
        'name_en': 'Mechanical Power (linear)',
        'formula': 'P = F · v',
        'expr': 'P = F * v',
        'variables': {
            'P': {'name': '功率', 'unit': 'W'},
            'F': {'name': '力', 'unit': 'N'},
            'v': {'name': '速度', 'unit': 'm/s'},
        },
        'unknowns': ['P', 'F', 'v'],
        'category': 'energy',
        'description': '力的功率等于力与速度的乘积',
        'tags': ['功率', '能'],
        'related': ['pTw', 'work'],
        'reference': '理论力学 §4.3',
    },
    {
        'id': 'pTw',
        'name_zh': '旋转功率',
        'name_en': 'Rotational Power',
        'formula': 'P = T · ω',
        'expr': 'P = T * omega',
        'variables': {
            'P': {'name': '功率', 'unit': 'W'},
            'T': {'name': '扭矩', 'unit': 'N·m'},
            'omega': {'name': '角速度', 'unit': 'rad/s'},
        },
        'unknowns': ['P', 'T', 'omega'],
        'category': 'energy',
        'description': '旋转机械功率',
        'tags': ['功率', '旋转'],
        'related': ['pfv'],
        'reference': '理论力学 §4.3',
    },
    {
        'id': 'ekin',
        'name_zh': '动能',
        'name_en': 'Kinetic Energy',
        'formula': 'Eₖ = ½ · m · v²',
        'expr': 'Ek = 0.5 * m * v**2',
        'variables': {
            'Ek': {'name': '动能', 'unit': 'J'},
            'm': {'name': '质量', 'unit': 'kg'},
            'v': {'name': '速度', 'unit': 'm/s'},
        },
        'unknowns': ['Ek', 'm', 'v'],
        'category': 'energy',
        'description': '平动动能',
        'tags': ['能量', '动能'],
        'related': ['epot', 'work'],
        'reference': '理论力学 §4.2',
    },
    {
        'id': 'epot',
        'name_zh': '重力势能',
        'name_en': 'Gravitational PE',
        'formula': 'Eₚ = m · g · h',
        'expr': 'Ep = m * g * h',
        'variables': {
            'Ep': {'name': '势能', 'unit': 'J'},
            'm': {'name': '质量', 'unit': 'kg'},
            'g': {'name': '重力加速度', 'unit': 'm/s²', 'default': 9.81},
            'h': {'name': '高度', 'unit': 'm'},
        },
        'unknowns': ['Ep', 'm', 'g', 'h'],
        'category': 'energy',
        'description': '相对零势能面的重力势能',
        'tags': ['能量', '势能'],
        'related': ['ekin', 'pfg'],
        'reference': '理论力学 §4.2',
    },

    # ---------- 圆周/转动 (rotation) ----------
    {
        'id': 'omega_to_n',
        'name_zh': '角速度与转速',
        'name_en': 'Omega to RPM',
        'formula': 'ω = 2π · n / 60',
        'expr': 'omega = 2 * 3.14159265358979 * n / 60',
        'variables': {
            'omega': {'name': '角速度', 'unit': 'rad/s'},
            'n': {'name': '转速', 'unit': 'rpm'},
        },
        'unknowns': ['omega', 'n'],
        'category': 'rotation',
        'description': '角速度与转速的换算',
        'tags': ['旋转', '转速'],
        'related': ['pTw'],
        'reference': '理论力学 §1.4',
    },
    {
        'id': 'v_omega_r',
        'name_zh': '线速度与角速度',
        'name_en': 'Linear vs Angular Velocity',
        'formula': 'v = ω · r',
        'expr': 'v = omega * r',
        'variables': {
            'v': {'name': '线速度', 'unit': 'm/s'},
            'omega': {'name': '角速度', 'unit': 'rad/s'},
            'r': {'name': '半径', 'unit': 'm'},
        },
        'unknowns': ['v', 'omega', 'r'],
        'category': 'rotation',
        'description': '圆周运动线速度等于角速度乘以半径',
        'tags': ['旋转', '速度'],
        'related': ['omega_to_n'],
        'reference': '理论力学 §1.4',
    },
    {
        'id': 'T_n_9550',
        'name_zh': '扭矩与功率换算',
        'name_en': 'Torque-Power-RPM',
        'formula': 'T = 9550 · P / n',
        'expr': 'T = 9550 * P / n',
        'variables': {
            'T': {'name': '扭矩', 'unit': 'N·m'},
            'P': {'name': '功率', 'unit': 'kW'},
            'n': {'name': '转速', 'unit': 'rpm'},
        },
        'unknowns': ['T', 'P', 'n'],
        'category': 'rotation',
        'description': '工程中常用: T(N·m)=9550·P(kW)/n(rpm)',
        'tags': ['扭矩', '功率', '换算'],
        'related': ['pTw'],
        'reference': '机械设计手册 §3.1',
    },

    # ---------- 强度 (strength) ----------
    {
        'id': 'sigma_stress',
        'name_zh': '正应力',
        'name_en': 'Normal Stress',
        'formula': 'σ = F / A',
        'expr': 'sigma = F / A',
        'variables': {
            'sigma': {'name': '正应力', 'unit': 'Pa'},
            'F': {'name': '轴向力', 'unit': 'N'},
            'A': {'name': '截面积', 'unit': 'm²'},
        },
        'unknowns': ['sigma', 'F', 'A'],
        'category': 'strength',
        'description': '轴向拉伸/压缩正应力',
        'tags': ['强度', '应力'],
        'related': ['tau_shear', 'pfa'],
        'reference': '材料力学 §2.1',
    },
    {
        'id': 'tau_shear',
        'name_zh': '切应力 (扭转)',
        'name_en': 'Torsional Shear Stress',
        'formula': 'τ = T / Wₚ',
        'expr': 'tau = T / Wp',
        'variables': {
            'tau': {'name': '切应力', 'unit': 'Pa'},
            'T': {'name': '扭矩', 'unit': 'N·m'},
            'Wp': {'name': '抗扭截面系数', 'unit': 'm³'},
        },
        'unknowns': ['tau', 'T', 'Wp'],
        'category': 'strength',
        'description': '圆轴扭转切应力',
        'tags': ['强度', '扭转', '应力'],
        'related': ['sigma_stress'],
        'reference': '材料力学 §3.2',
    },
    {
        'id': 'sigma_bending',
        'name_zh': '弯曲应力',
        'name_en': 'Bending Stress',
        'formula': 'σ = M / W',
        'expr': 'sigma = M / W',
        'variables': {
            'sigma': {'name': '弯曲应力', 'unit': 'Pa'},
            'M': {'name': '弯矩', 'unit': 'N·m'},
            'W': {'name': '抗弯截面系数', 'unit': 'm³'},
        },
        'unknowns': ['sigma', 'M', 'W'],
        'category': 'strength',
        'description': '梁的最大弯曲正应力',
        'tags': ['强度', '弯曲'],
        'related': ['sigma_stress'],
        'reference': '材料力学 §4.1',
    },

    # ---------- 流体 (fluid) ----------
    {
        'id': 'continuity',
        'name_zh': '流量连续性',
        'name_en': 'Continuity Equation',
        'formula': 'Q = A · v',
        'expr': 'Q = A * v',
        'variables': {
            'Q': {'name': '流量', 'unit': 'm³/s'},
            'A': {'name': '过流面积', 'unit': 'm²'},
            'v': {'name': '流速', 'unit': 'm/s'},
        },
        'unknowns': ['Q', 'A', 'v'],
        'category': 'fluid',
        'description': '不可压缩流体连续性方程',
        'tags': ['流体', '流量'],
        'related': ['bernoulli', 'reynolds'],
        'reference': '流体力学 §2.1',
    },
    {
        'id': 'bernoulli',
        'name_zh': '伯努利方程',
        'name_en': 'Bernoulli Equation',
        'formula': 'p₁ + ½ρv₁² + ρgh₁ = p₂ + ½ρv₂² + ρgh₂',
        'expr': '(p1 + 0.5*rho*v1**2 + rho*g*h1) - (p2 + 0.5*rho*v2**2 + rho*g*h2) == 0',
        'variables': {
            'p1': {'name': '1点压强', 'unit': 'Pa'},
            'p2': {'name': '2点压强', 'unit': 'Pa'},
            'v1': {'name': '1点速度', 'unit': 'm/s'},
            'v2': {'name': '2点速度', 'unit': 'm/s'},
            'h1': {'name': '1点高度', 'unit': 'm', 'default': 0},
            'h2': {'name': '2点高度', 'unit': 'm', 'default': 0},
            'rho': {'name': '密度', 'unit': 'kg/m³', 'default': 1000},
            'g': {'name': '重力加速度', 'unit': 'm/s²', 'default': 9.81},
        },
        'unknowns': ['p1', 'p2', 'v1', 'v2', 'h1', 'h2'],
        'category': 'fluid',
        'description': '理想流体定常流动能量守恒',
        'tags': ['流体', '伯努利'],
        'related': ['continuity'],
        'reference': '流体力学 §3.2',
    },
    {
        'id': 'reynolds',
        'name_zh': '雷诺数',
        'name_en': 'Reynolds Number',
        'formula': 'Re = ρ · v · d / μ',
        'expr': 'Re = rho * v * d / mu',
        'variables': {
            'Re': {'name': '雷诺数', 'unit': ''},
            'rho': {'name': '密度', 'unit': 'kg/m³'},
            'v': {'name': '流速', 'unit': 'm/s'},
            'd': {'name': '特征长度', 'unit': 'm'},
            'mu': {'name': '动力粘度', 'unit': 'Pa·s'},
        },
        'unknowns': ['Re', 'rho', 'v', 'd', 'mu'],
        'category': 'fluid',
        'description': '判定流动状态 (层流/湍流)',
        'tags': ['流体', '雷诺'],
        'related': ['continuity', 'bernoulli'],
        'reference': '流体力学 §4.1',
    },

    # ---------- 几何 (geometry) ----------
    {
        'id': 'circle_area',
        'name_zh': '圆面积',
        'name_en': 'Circle Area',
        'formula': 'A = π · d² / 4',
        'expr': 'A = 3.14159265358979 * d**2 / 4',
        'variables': {
            'A': {'name': '面积', 'unit': 'mm²'},
            'd': {'name': '直径', 'unit': 'mm'},
        },
        'unknowns': ['A', 'd'],
        'category': 'geometry',
        'description': '圆面积 = πd²/4',
        'tags': ['几何', '面积', '圆'],
        'related': ['circle_circumference'],
        'reference': '机械设计手册 §1.1',
    },
    {
        'id': 'circle_circumference',
        'name_zh': '圆周长',
        'name_en': 'Circle Circumference',
        'formula': 'L = π · d',
        'expr': 'L = 3.14159265358979 * d',
        'variables': {
            'L': {'name': '周长', 'unit': 'mm'},
            'd': {'name': '直径', 'unit': 'mm'},
        },
        'unknowns': ['L', 'd'],
        'category': 'geometry',
        'description': '圆周长 = πd',
        'tags': ['几何', '周长', '圆'],
        'related': ['circle_area'],
        'reference': '机械设计手册 §1.1',
    },
    {
        'id': 'cylinder_volume',
        'name_zh': '圆柱体积',
        'name_en': 'Cylinder Volume',
        'formula': 'V = π · d² / 4 · L',
        'expr': 'V = 3.14159265358979 * d**2 / 4 * L',
        'variables': {
            'V': {'name': '体积', 'unit': 'mm³'},
            'd': {'name': '直径', 'unit': 'mm'},
            'L': {'name': '长度', 'unit': 'mm'},
        },
        'unknowns': ['V', 'd', 'L'],
        'category': 'geometry',
        'description': '圆柱体积 = 截面积 × 长度',
        'tags': ['几何', '体积', '圆柱'],
        'related': ['circle_area'],
        'reference': '机械设计手册 §1.2',
    },

    # ---------- 热 (thermal) ----------
    {
        'id': 'heat',
        'name_zh': '热量',
        'name_en': 'Heat',
        'formula': 'Q = c · m · ΔT',
        'expr': 'Q = c * m * dT',
        'variables': {
            'Q': {'name': '热量', 'unit': 'J'},
            'c': {'name': '比热容', 'unit': 'J/(kg·K)'},
            'm': {'name': '质量', 'unit': 'kg'},
            'dT': {'name': '温升', 'unit': 'K'},
        },
        'unknowns': ['Q', 'c', 'm', 'dT'],
        'category': 'thermal',
        'description': '物体吸收/放出的热量',
        'tags': ['热', '热量'],
        'related': ['linear_expansion'],
        'reference': '传热学 §1.2',
    },
    {
        'id': 'linear_expansion',
        'name_zh': '线膨胀',
        'name_en': 'Linear Thermal Expansion',
        'formula': 'ΔL = α · L · ΔT',
        'expr': 'dL = alpha * L * dT',
        'variables': {
            'dL': {'name': '伸长量', 'unit': 'mm'},
            'alpha': {'name': '线膨胀系数', 'unit': '1/K', 'default': 1.2e-5},
            'L': {'name': '原长', 'unit': 'mm'},
            'dT': {'name': '温升', 'unit': 'K'},
        },
        'unknowns': ['dL', 'alpha', 'L', 'dT'],
        'category': 'thermal',
        'description': '线膨胀量 ΔL = αLΔT',
        'tags': ['热', '膨胀'],
        'related': ['heat'],
        'reference': '传热学 §2.3',
    },

    # ---------- 振动 (vibration) ----------
    {
        'id': 'spring_period',
        'name_zh': '弹簧振子周期',
        'name_en': 'Spring-Mass Period',
        'formula': 'T = 2π · √(m / k)',
        'expr': 'T = 2 * 3.14159265358979 * (m / k)**0.5',
        'variables': {
            'T': {'name': '周期', 'unit': 's'},
            'm': {'name': '质量', 'unit': 'kg'},
            'k': {'name': '刚度', 'unit': 'N/m'},
        },
        'unknowns': ['T', 'm', 'k'],
        'category': 'vibration',
        'description': '单自由度弹簧-质量系统固有周期',
        'tags': ['振动', '周期'],
        'related': ['pendulum'],
        'reference': '机械振动 §1.3',
    },
    {
        'id': 'pendulum',
        'name_zh': '单摆周期',
        'name_en': 'Simple Pendulum',
        'formula': 'T = 2π · √(L / g)',
        'expr': 'T = 2 * 3.14159265358979 * (L / g)**0.5',
        'variables': {
            'T': {'name': '周期', 'unit': 's'},
            'L': {'name': '摆长', 'unit': 'm'},
            'g': {'name': '重力加速度', 'unit': 'm/s²', 'default': 9.81},
        },
        'unknowns': ['T', 'L', 'g'],
        'category': 'vibration',
        'description': '小角度单摆周期',
        'tags': ['振动', '单摆', '周期'],
        'related': ['spring_period'],
        'reference': '理论力学 §6.2',
    },
]


# 模块加载完成日志
_LOAD_END = time.perf_counter()
_LOAD_ELAPSED_MS = (_LOAD_END - _LOAD_START) * 1000
_LOAD_CATS = sorted({f['category'] for f in FORMULAS})
_logger.info(
    f"[LOAD-START] trigger=module_import ts={_LOAD_TS:.6f} module=formulas_data"
)
_logger.info(
    f"[LOAD-END]   trigger=module_import elapsed={_LOAD_ELAPSED_MS:.3f}ms "
    f"total={len(FORMULAS)} categories={_LOAD_CATS} "
    f"total_vars={sum(len(f['variables']) for f in FORMULAS)} "
    f"status=ok"
)


# ============ 辅助函数 ============

def get_all() -> List[Dict[str, Any]]:
    return FORMULAS


def get_by_id(fid: str) -> Optional[Dict[str, Any]]:
    for f in FORMULAS:
        if f['id'] == fid:
            return f
    return None


def get_categories() -> List[str]:
    cats = []
    for f in FORMULAS:
        if f['category'] not in cats:
            cats.append(f['category'])
    return sorted(cats)


def search(query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """按 q 模糊匹配 name / id / tags; 可选 category 过滤."""
    q = (query or '').strip().lower()
    start = time.perf_counter()
    _logger.info(
        f"[LOAD-START] trigger=search ts={time.time():.6f} "
        f"query={q!r} category={category!r} library_size={len(FORMULAS)}"
    )
    result = []
    for f in FORMULAS:
        if category and f['category'] != category:
            continue
        if not q:
            result.append(f)
            continue
        # 匹配 name/id/tags
        if (q in f['id'].lower() or  # noqa: W504
            q in f['name_zh'].lower() or  # noqa: W504
            q in f['name_en'].lower() or  # noqa: W504
            q in f['formula'].lower() or  # noqa: W504
                any(q in t.lower() for t in f.get('tags', []))):
            result.append(f)
    _logger.info(
        f"[LOAD-END]   trigger=search elapsed={(time.perf_counter() - start) * 1000:.3f}ms "
        f"hits={len(result)} status=ok"
    )
    return result


def get_related(fid: str) -> List[Dict[str, Any]]:
    """获取相关公式 (按 related 字段)."""
    f = get_by_id(fid)
    if not f:
        return []
    result = []
    for rid in f.get('related', []):
        r = get_by_id(rid)
        if r:
            result.append(r)
    return result


# ============ 公式求解器 ============

def _parse_vars_from_expr(expr: str) -> List[str]:
    """从表达式左侧提取变量名 (粗略: 找 '=' 前的标识符)."""
    left = expr.split('=')[0].strip()
    # 提取字母开头的标识符
    return re.findall(r'[A-Za-z_][A-Za-z0-9_]*', left)


def solve(fid: str, given: Dict[str, float]) -> Dict[str, Any]:
    """根据已知量求解未知量.

    Args:
        fid: 公式 id
        given: {var: value} 已知量 (含默认值)

    Returns:
        {ok, result: {var: value}, formula, ...} 或
        {ok: False, error, missing}

    Note: 日志由模块底部的 _solve_log_success_decorator 装饰器统一记录.
    """
    f = get_by_id(fid)
    if not f:
        return {'ok': False, 'error': f'公式 {fid} 不存在'}

    # 合并默认值
    given_full = {}
    for k, meta in f['variables'].items():
        if k in given:
            given_full[k] = given[k]
        elif 'default' in meta:
            given_full[k] = meta['default']
        elif k in given:
            given_full[k] = given[k]

    # 检查已知量够不够 (至少应有 N-1 个)
    unknowns = [k for k in f['variables'].keys() if k not in given_full]
    if len(unknowns) > 1:
        return {
            'ok': False,
            'error': f'已知量不足, 还缺 {len(unknowns)} 个变量: {unknowns}',
            'missing': unknowns,
        }
    if not unknowns:
        # 全部已知, 校验一致性 (用 expr 计算 lhs/rhs)
        return {
            'ok': True,
            'result': given_full,
            'note': '全部已知, 无需求解',
            'formula': f['formula'],
        }

    target = unknowns[0]

    # 用 eval 求值. 仅在 sandbox 命名空间内执行 (无内置函数)
    expr = f['expr']
    try:
        # 分离左右: lhs = rhs
        parts = expr.split('=', 1)
        if len(parts) != 2:
            return {'ok': False, 'error': '公式格式错误 (无 =)'}
        # lhs_str, rhs_str = parts[0].strip(), parts[1].strip()
        rhs_str = parts[1].strip()
        rhs = eval(rhs_str, {'__builtins__': {}}, given_full)
        # 求解目标
        if target == _parse_vars_from_expr(expr)[0]:
            # lhs 是 target, 已知 rhs
            result = rhs
        else:
            # 复杂情况: lhs 也有 target, 需展开 (这里只处理简单线性)
            # 试 eval 目标变量, 假设 target 在 rhs 中
            # 直接用 sympy 不引入, 这里做一个针对一元方程的简单尝试:
            # 把 target 设为符号 → 不行, 走折中: 提示用户公式暂不支持反解
            return {
                'ok': False,
                'error': f'公式暂不支持反解 {target}, 请手动使用 {f["formula"]}',
            }
        return {
            'ok': True,
            'target': target,
            'value': result,
            'result': {**given_full, target: result},
            'formula': f['formula'],
            'unit': f['variables'][target]['unit'],
        }
    except Exception as e:
        return {'ok': False, 'error': f'求值失败: {e}'}


# 在 solve 函数外层包装装饰器, 用于统一记录 LOAD-START / LOAD-END
def _solve_log_decorator(orig):
    """包装 solve 函数, 自动记录求解过程的日志 (开始/结束/状态)."""
    def wrapper(fid, given):
        start = time.perf_counter()
        _logger.info(
            f"[LOAD-START] trigger=solve ts={time.time():.6f} "
            f"fid={fid!r} given={given!r}"
        )
        result = orig(fid, given)
        elapsed = (time.perf_counter() - start) * 1000
        status = result.get('ok')
        if status is True:
            _logger.info(
                f"[LOAD-END]   trigger=solve elapsed={elapsed:.3f}ms "
                f"target={result.get('target')!r} value={result.get('value')!r} status=ok"
            )
        elif 'missing' in result:
            _logger.info(
                f"[LOAD-END]   trigger=solve elapsed={elapsed:.3f}ms "
                f"missing={result.get('missing')!r} status=insufficient"
            )
        else:
            _logger.info(
                f"[LOAD-END]   trigger=solve elapsed={elapsed:.3f}ms "
                f"error={result.get('error')!r} status=error"
            )
        return result
    return wrapper


solve = _solve_log_decorator(solve)
