"""轴承寿命计算 L10"""


def bearing_life(C_kN, P_kN, n_rpm, bearing_type='ball'):
    p = 3.0 if bearing_type == 'ball' else 10/3
    L10_rev = (C_kN / P_kN) ** p * 1e6 if P_kN > 0 else 0
    L10h = L10_rev / (60 * n_rpm) if n_rpm > 0 else 0
    return {
        'dynamic_load_rating_kN': C_kN, 'equivalent_load_kN': P_kN,
        'speed_rpm': n_rpm, 'bearing_type': bearing_type,
        'L10_revolutions_Mr': round(L10_rev / 1e6, 2),
        'L10_life_hours': round(L10h, 1),
        'formula': 'L10 = (C/P)^p x 10^6 / (60n)'
    }


def equivalent_load(Fr_kN, Fa_kN, X=0.56, Y=1.5):
    P = X * Fr_kN + Y * Fa_kN
    return {'radial_load_kN': Fr_kN, 'axial_load_kN': Fa_kN,
            'X_factor': X, 'Y_factor': Y,
            'equivalent_load_kN': round(P, 3)}


def bearing_static_check(C0_kN, P0_kN, safety=1.0):
    S0 = C0_kN / P0_kN if P0_kN > 0 else 0
    return {'static_safety_factor': round(S0, 2), 'is_safe': S0 >= safety}
