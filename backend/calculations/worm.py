"""蜗杆传动计算"""
import math


def worm_geometry(m, z1, z2, q=10):
    d1 = m * q
    d2 = m * z2
    gamma = math.atan(z1 / q)
    a = (d1 + d2) / 2
    return {
        'module_m': m, 'worm_threads': z1, 'wheel_teeth': z2,
        'diameter_quotient_q': q,
        'worm_pitch_diameter_mm': round(d1, 2),
        'wheel_pitch_diameter_mm': round(d2, 2),
        'lead_angle_deg': round(math.degrees(gamma), 3),
        'center_distance_mm': round(a, 2),
        'ratio': round(z2/z1, 2),
        'formula': 'd1=mq, d2=mz2, lead_angle=atan(z1/q)'
    }


def worm_efficiency(gamma_deg, fv=0.06):
    gamma = math.radians(gamma_deg)
    rho_v = math.atan(fv)
    eta = math.tan(gamma) / math.tan(gamma + rho_v)
    self_lock = gamma < rho_v
    return {
        'lead_angle_deg': gamma_deg, 'friction_coeff': fv,
        'efficiency': round(eta, 4),
        'self_locking': self_lock,
    }
