"""
全面单位换算工具模块 — 覆盖机械设计常用所有单位
"""
import math

# ============ 单位换算表 ============

# 长度 → mm
LENGTH = {
    'mm': 1, 'cm': 10, 'dm': 100, 'm': 1000, 'km': 1e6,
    'inch': 25.4, 'in': 25.4, 'ft': 304.8, 'yard': 914.4,
    'mile': 1609344, 'um': 0.001, 'nm': 1e-6,
}

# 面积 → mm²
AREA = {
    'mm2': 1, 'cm2': 100, 'm2': 1e6, 'km2': 1e12,
    'in2': 645.16, 'ft2': 92903.04,
}

# 体积 → mm³
VOLUME = {
    'mm3': 1, 'cm3': 1000, 'm3': 1e9, 'L': 1e6, 'mL': 1000,
    'in3': 16387.064, 'ft3': 28316846.6, 'gal': 3785411.78,
}

# 力 → N
FORCE = {
    'N': 1, 'kN': 1000, 'MN': 1e6,
    'kgf': 9.80665, 'gf': 0.00980665, 'tf': 9806.65,
    'lbf': 4.44822, 'kip': 4448.22,
}

# 压力/应力 → Pa
PRESSURE = {
    'Pa': 1, 'kPa': 1000, 'MPa': 1e6, 'GPa': 1e9,
    'bar': 1e5, 'mbar': 100,
    'kgf/cm2': 98066.5, 'kgf/mm2': 9806650,
    'psi': 6894.76, 'ksi': 6894760,
    'atm': 101325, 'mmHg': 133.322, 'mmH2O': 9.80665,
}

# 扭矩 → N·mm
TORQUE = {
    'N·mm': 1, 'N·m': 1000, 'kN·m': 1e6,
    'kgf·mm': 9.80665, 'kgf·m': 9806.65,
    'lbf·in': 112.985, 'lbf·ft': 1355.82,
}

# 功率 → W
POWER = {
    'W': 1, 'kW': 1000, 'MW': 1e6,
    'hp': 745.7,  # 英制马力
    'ps': 735.5,  # 公制马力
}

# 速度 → m/s
VELOCITY = {
    'm/s': 1, 'km/h': 0.277778, 'm/min': 0.0166667,
    'ft/s': 0.3048, 'mph': 0.44704, 'knot': 0.514444,
}

# 加速度 → m/s²
ACCELERATION = {
    'm/s2': 1, 'g': 9.80665, 'ft/s2': 0.3048,
}

# 角速度 → rad/s
ANGULAR_VELOCITY = {
    'rad/s': 1, 'rpm': 0.1047198, 'deg/s': 0.0174533,
    'rps': 6.283185,  # 转/秒
}

# 角度 → rad
ANGLE = {
    'rad': 1, 'deg': 0.0174533, 'rev': 6.283185, 'grad': 0.01570796,
}

# 温度
# 特殊处理：非比例换算

# 转动惯量 → kg·m²
INERTIA = {
    'kg·m2': 1, 'kg·cm2': 0.0001, 'kg·mm2': 1e-6,
    'g·cm2': 1e-7, 'lbf·ft·s2': 1.35581795,
}

# 能量/功 → J
ENERGY = {
    'J': 1, 'kJ': 1000, 'MJ': 1e6,
    'Nm': 1, 'kgf·m': 9.80665,
    'Wh': 3600, 'kWh': 3.6e6,
    'cal': 4.184, 'kcal': 4184,
    'BTU': 1055.06, 'ft·lbf': 1.35582,
}

# 流量 → m³/s
FLOW = {
    'm3/s': 1, 'm3/h': 0.000277778, 'L/min': 1.66667e-5,
    'L/s': 0.001, 'GPM': 6.309e-5, 'CFM': 0.000471947,
}

# 黏度 → Pa·s
VISCOSITY = {
    'Pa·s': 1, 'mPa·s': 0.001, 'P': 0.1, 'cP': 0.001,
}

# ============ 换算函数 ============

UNIT_CATEGORIES = {
    'length': ('长度', LENGTH, 'mm'),
    'area': ('面积', AREA, 'mm²'),
    'volume': ('体积', VOLUME, 'mm³'),
    'force': ('力', FORCE, 'N'),
    'pressure': ('压力/应力', PRESSURE, 'Pa'),
    'torque': ('扭矩', TORQUE, 'N·mm'),
    'power': ('功率', POWER, 'W'),
    'velocity': ('速度', VELOCITY, 'm/s'),
    'acceleration': ('加速度', ACCELERATION, 'm/s²'),
    'angular_velocity': ('角速度', ANGULAR_VELOCITY, 'rad/s'),
    'angle': ('角度', ANGLE, 'rad'),
    'inertia': ('转动惯量', INERTIA, 'kg·m²'),
    'energy': ('能量/功', ENERGY, 'J'),
    'flow': ('流量', FLOW, 'm³/s'),
    'viscosity': ('黏度', VISCOSITY, 'Pa·s'),
}


def convert(value, from_unit, to_unit, unit_map):
    if from_unit not in unit_map or to_unit not in unit_map:
        return None
    return value * unit_map[from_unit] / unit_map[to_unit]


def convert_temperature(value, from_unit, to_unit):
    """温度特殊处理"""
    if from_unit == '°C' and to_unit == '°F':
        return value * 9/5 + 32
    elif from_unit == '°F' and to_unit == '°C':
        return (value - 32) * 5/9
    elif from_unit == '°C' and to_unit == 'K':
        return value + 273.15
    elif from_unit == 'K' and to_unit == '°C':
        return value - 273.15
    elif from_unit == '°F' and to_unit == 'K':
        return (value - 32) * 5/9 + 273.15
    elif from_unit == 'K' and to_unit == '°F':
        return (value - 273.15) * 9/5 + 32
    return value  # same unit


def list_categories():
    """列出所有单位类别和可用单位"""
    result = []
    for key, (name, units, default) in UNIT_CATEGORIES.items():
        result.append({
            'id': key, 'name': name, 'default': default,
            'units': sorted(units.keys(), key=lambda x: len(x)),
        })
    return result


def convert_all(value, from_unit, to_unit, category):
    """统一入口"""
    if category == 'temperature':
        result = convert_temperature(value, from_unit, to_unit)
        return {
            'category': '温度',
            'value': value, 'from': from_unit,
            'result': round(result, 6), 'to': to_unit,
        }
    
    entry = UNIT_CATEGORIES.get(category)
    if not entry:
        return {'error': f'未知类别: {category}'}
    
    _, units, _ = entry
    result = convert(value, from_unit, to_unit, units)
    if result is None:
        return {'error': f'无法换算: {from_unit} → {to_unit}'}
    
    return {
        'category': entry[0],
        'value': value, 'from': from_unit,
        'result': round(result, 6), 'to': to_unit,
    }


# ============ 便捷函数 ============

def format_value(v, decimals=4):
    if v is None:
        return '-'
    if isinstance(v, float):
        return f"{v:.{decimals}f}".rstrip('0').rstrip('.')
    return str(v)


PHYSICAL_CONSTANTS = {
    'g': 9.80665,           # 重力加速度 m/s²
    'G': 6.674e-11,         # 万有引力常数
    'pi': math.pi,
    'R': 8.314,             # 气体常数 J/(mol·K)
    'atm': 101325,          # 标准大气压 Pa
    'c': 299792458,         # 光速 m/s
    'sigma': 5.67e-8,       # 斯特藩-玻尔兹曼常数 W/(m²·K⁴)
}
