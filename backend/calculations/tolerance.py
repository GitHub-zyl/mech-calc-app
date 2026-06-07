"""
公差配合计算模块
参考：机械设计常用计算表 - 公差 / 轴的基本偏差 / 孔偏差
"""
import logging
import math
import time

# 模块级 logger
_logger = logging.getLogger(__name__)

# ============ IT公差等级 ============

# IT基本公差  单位: μm
# 标准公差因子 i = 0.45∛D + 0.001D (D为尺寸分段几何平均值, mm)


def _std_tolerance_factor(D_mm):
    """计算标准公差因子 i (μm)"""
    if D_mm <= 500:
        D = D_mm
    else:
        D = D_mm
    i = 0.45 * (D ** (1/3)) + 0.001 * D
    return i


def _it_tolerance(nominal_mm, it_grade):
    """
    计算IT公差值 (μm)
    
    参数:
        nominal_mm: 公称尺寸 (mm)
        it_grade: 公差等级 (1..18)
    """
    # 尺寸分段 (mm)
    steps = [
        (0, 3), (3, 6), (6, 10), (10, 18), (18, 30), (30, 50),
        (50, 80), (80, 120), (120, 180), (180, 250), (250, 315),
        (315, 400), (400, 500)
    ]
    
    D = nominal_mm
    for lo, hi in steps:
        if lo <= D < hi:
            D_avg = math.sqrt(lo * hi) if lo > 0 else 1.5
            break
    else:
        D_avg = math.sqrt(400 * 500) if D <= 500 else D
    
    i = _std_tolerance_factor(D_avg)
    
    # IT1-IT18 系数
    it_factors = {
        1: 0.8, 2: 1.2, 3: 2.0, 4: 3.0, 5: 5.0, 6: 7.0,
        7: 10.0, 8: 16.0, 9: 25.0, 10: 40.0, 11: 64.0,
        12: 100.0, 13: 160.0, 14: 250.0, 15: 400.0,
        16: 640.0, 17: 1000.0, 18: 1600.0
    }
    
    factor = it_factors.get(it_grade, 7)
    
    if it_grade <= 5:
        tolerance = factor * i
    else:
        tolerance = factor * i
    
    return round(tolerance, 2)


# ============ 基本偏差 ============

# 轴的基本偏差 (部分, μm, 尺寸段 ≤ 500mm)
SHAFT_DEVIATIONS = {
    'a': {3: -270, 6: -270, 10: -280, 18: -290, 30: -300, 50: -310,
          80: -320, 120: -340, 180: -360, 250: -380, 315: -410, 400: -450},
    'b': {3: -140, 6: -140, 10: -150, 18: -150, 30: -160, 50: -170,
          80: -180, 120: -200, 180: -210, 250: -240, 315: -260, 400: -280},
    'c': {3: -60, 6: -70, 10: -80, 18: -95, 30: -110, 50: -120,
          80: -130, 120: -150, 180: -170, 250: -190, 315: -210, 400: -230},
    'd': {3: -20, 6: -30, 10: -40, 18: -50, 30: -65, 50: -80,
          80: -100, 120: -120, 180: -145, 250: -170, 315: -190, 400: -210},
    'e': {3: -14, 6: -20, 10: -25, 18: -32, 30: -40, 50: -50,
          80: -60, 120: -72, 180: -85, 250: -100, 315: -110, 400: -125},
    'f': {3: -6, 6: -10, 10: -13, 18: -16, 30: -20, 50: -25,
          80: -30, 120: -36, 180: -43, 250: -50, 315: -56, 400: -62},
    'g': {3: -2, 6: -4, 10: -5, 18: -6, 30: -7, 50: -9,
          80: -10, 120: -12, 180: -14, 250: -14, 315: -16, 400: -16},
    'h': {3: 0, 6: 0, 10: 0, 18: 0, 30: 0, 50: 0, 80: 0, 120: 0,
          180: 0, 250: 0, 315: 0, 400: 0},
    'js': {'special': True},
    'k': {3: 0, 6: 1, 10: 1, 18: 2, 30: 2, 50: 2, 80: 3, 120: 3,
          180: 4, 250: 4, 315: 4, 400: 5},
    'm': {3: 2, 6: 4, 10: 6, 18: 7, 30: 8, 50: 9, 80: 11, 120: 13,
          180: 15, 250: 17, 315: 18, 400: 20},
    'n': {3: 4, 6: 8, 10: 10, 18: 12, 30: 15, 50: 17, 80: 20, 120: 23,
          180: 27, 250: 31, 315: 34, 400: 37},
    'p': {3: 6, 6: 12, 10: 15, 18: 18, 30: 22, 50: 26, 80: 30, 120: 36,
          180: 43, 250: 50, 315: 56, 400: 63},
    'r': {3: 10, 6: 15, 10: 19, 18: 23, 30: 28, 50: 34, 80: 40, 120: 48,
          180: 58, 250: 68, 315: 78, 400: 88},
    's': {3: 14, 6: 19, 10: 23, 18: 28, 30: 35, 50: 42, 80: 48, 120: 58,
          180: 70, 250: 82, 315: 94, 400: 106},
    't': {3: 18, 6: 23, 10: 28, 18: 33, 30: 41, 50: 50, 80: 58, 120: 70,
          180: 84, 250: 98, 315: 112, 400: 126},
    'u': {3: 23, 6: 28, 10: 34, 18: 41, 30: 50, 50: 61, 80: 71, 120: 85,
          180: 104, 250: 122, 315: 140, 400: 160},
}

# 孔的基本偏差 (相对于轴取反)
HOLE_DEVIATIONS = {
    'A': {3: 270, 6: 270, 10: 280, 18: 290, 30: 300, 50: 310,
          80: 320, 120: 340, 180: 360, 250: 380, 315: 410, 400: 450},
    'B': {3: 140, 6: 140, 10: 150, 18: 150, 30: 160, 50: 170,
          80: 180, 120: 200, 180: 210, 250: 240, 315: 260, 400: 280},
    'C': {3: 60, 6: 70, 10: 80, 18: 95, 30: 110, 50: 120,
          80: 130, 120: 150, 180: 170, 250: 190, 315: 210, 400: 230},
    'D': {3: 20, 6: 30, 10: 40, 18: 50, 30: 65, 50: 80,
          80: 100, 120: 120, 180: 145, 250: 170, 315: 190, 400: 210},
    'E': {3: 14, 6: 20, 10: 25, 18: 32, 30: 40, 50: 50,
          80: 60, 120: 72, 180: 85, 250: 100, 315: 110, 400: 125},
    'F': {3: 6, 6: 10, 10: 13, 18: 16, 30: 20, 50: 25,
          80: 30, 120: 36, 180: 43, 250: 50, 315: 56, 400: 62},
    'G': {3: 2, 6: 4, 10: 5, 18: 6, 30: 7, 50: 9,
          80: 10, 120: 12, 180: 14, 250: 14, 315: 16, 400: 16},
    'H': {3: 0, 6: 0, 10: 0, 18: 0, 30: 0, 50: 0, 80: 0, 120: 0,
          180: 0, 250: 0, 315: 0, 400: 0},
    'JS': {'special': True},
    'K': {3: 0, 6: 2, 10: 2, 18: 2, 30: 3, 50: 4, 80: 5, 120: 6,
          180: 8, 250: 10, 315: 12, 400: 13},
    'M': {3: -2, 6: -4, 10: -6, 18: -7, 30: -8, 50: -9, 80: -11, 120: -13,
          180: -15, 250: -17, 315: -18, 400: -20},
    'N': {3: -4, 6: -8, 10: -10, 18: -12, 30: -15, 50: -17, 80: -20, 120: -23,
          180: -27, 250: -31, 315: -34, 400: -37},
    'P': {3: -6, 6: -12, 10: -15, 18: -18, 30: -22, 50: -26, 80: -30, 120: -36,
          180: -43, 250: -50, 315: -56, 400: -63},
    'R': {3: -10, 6: -15, 10: -19, 18: -23, 30: -28, 50: -34, 80: -40, 120: -48,
          180: -58, 250: -68, 315: -78, 400: -88},
    'S': {3: -14, 6: -19, 10: -23, 18: -28, 30: -35, 50: -42, 80: -48, 120: -58,
          180: -70, 250: -82, 315: -94, 400: -106},
    'T': {3: -18, 6: -23, 10: -28, 18: -33, 30: -41, 50: -50, 80: -58, 120: -70,
          180: -84, 250: -98, 315: -112, 400: -126},
    'U': {3: -23, 6: -28, 10: -34, 18: -41, 30: -50, 50: -61, 80: -71, 120: -85,
          180: -104, 250: -122, 315: -140, 400: -160},
}


def _get_basic_deviation(nominal_mm, letter, is_hole=False):
    """获取基本偏差值 (μm)"""
    table = HOLE_DEVIATIONS if is_hole else SHAFT_DEVIATIONS
    dev_data = table.get(letter)
    if dev_data is None:
        return None
    
    if isinstance(dev_data, dict) and dev_data.get('special'):
        return 0  # JS/js 对称偏差
    
    # 找到对应的尺寸分段
    size_limits = sorted(dev_data.keys())
    for limit in size_limits:
        if nominal_mm <= limit:
            return dev_data[limit]
    return dev_data[size_limits[-1]] if size_limits else 0


def shaft_tolerance(nominal_mm, tolerance_spec):
    """
    轴的公差计算
    
    参数:
        nominal_mm: 公称尺寸 (mm)
        tolerance_spec: 公差带代号，如 'h7', 'g6', 'f8'
    
    返回: dict
    """
    import re
    m = re.match(r'([a-zA-Z]+)(\d+)', tolerance_spec)
    if not m:
        return {'error': f'格式错误: {tolerance_spec}，示例: h7, g6, f8'}
    
    letter = m.group(1).lower()
    grade = int(m.group(2))
    
    if grade < 1 or grade > 18:
        return {'error': f'公差等级超出范围 (1-18): {grade}'}
    
    # 根据基本偏差字母确定查表值是上偏差还是下偏差:
    #   a~h: 基本偏差为上偏差(es), ei = es - IT
    #   k~zc: 基本偏差为下偏差(ei), es = ei + IT
    #   js: 对称偏差, es = +IT/2, ei = -IT/2
    basic_dev = _get_basic_deviation(nominal_mm, letter)
    if basic_dev is None:
        return {'error': f'未知基本偏差代号: {letter}'}

    it = _it_tolerance(nominal_mm, grade)

    if letter == 'js':
        es = it / 2
        ei = -it / 2
    elif letter <= 'h':
        # a~h: 基本偏差为上偏差(es)
        es = basic_dev
        ei = es - it
    else:
        # k~zc: 基本偏差为下偏差(ei)
        ei = basic_dev
        es = ei + it
    
    return {
        'type': '轴',
        'spec': f'φ{nominal_mm}{tolerance_spec}',
        'nominal_mm': nominal_mm,
        'basic_deviation': letter,
        'it_grade': grade,
        'tolerance_um': round(it, 2),
        'upper_dev_um': es,
        'lower_dev_um': round(ei, 2),
        'max_size_mm': round(nominal_mm + es / 1000, 4),
        'min_size_mm': round(nominal_mm + ei / 1000, 4),
    }


def hole_tolerance(nominal_mm, tolerance_spec):
    """
    孔的公差计算
    """
    import re
    m = re.match(r'([a-zA-Z]+)(\d+)', tolerance_spec)
    if not m:
        return {'error': f'格式错误: {tolerance_spec}，示例: H7, G6, F8'}
    
    letter = m.group(1).upper()
    grade = int(m.group(2))
    
    if grade < 1 or grade > 18:
        return {'error': f'公差等级超出范围 (1-18): {grade}'}
    
    EI = _get_basic_deviation(nominal_mm, letter, is_hole=True)  # 下偏差
    if EI is None:
        return {'error': f'未知基本偏差代号: {letter}'}
    
    it = _it_tolerance(nominal_mm, grade)
    ES = EI + it  # 上偏差
    
    return {
        'type': '孔',
        'spec': f'φ{nominal_mm}{tolerance_spec}',
        'nominal_mm': nominal_mm,
        'basic_deviation': letter,
        'it_grade': grade,
        'tolerance_um': round(it, 2),
        'lower_dev_um': EI,
        'upper_dev_um': round(ES, 2),
        'min_size_mm': round(nominal_mm + EI / 1000, 4),
        'max_size_mm': round(nominal_mm + ES / 1000, 4),
    }


def fit_calculation(nominal_mm, hole_spec, shaft_spec):
    """
    配合计算 (孔轴配合)

    参数:
        nominal_mm: 公称尺寸
        hole_spec: 孔公差带 如 'H7'
        shaft_spec: 轴公差带 如 'h6', 'g6'

    配合判别 (GB/T 1800.1-2009 §5):
        - 间隙配合: Xmin >= 0
        - 过盈配合: Xmax <= 0
        - 过渡配合: Xmin < 0 AND Xmax > 0

    日志策略 (优化后, 共 4 条 INFO):
        - [FIT-ENTRY]    入口: 记录调用时间戳 + 输入参数
        - [FIT-CALC]     计算中间值: ES/EI/es/ei/Xmax/Xmin/Ymax/Ymin
                         (合并了原 [FIT-HOLE]/[FIT-SHAFT]/[FIT-XCALC]/[FIT-YCALC])
        - [FIT-BRANCH]   分支决策: 命中规则 + Xmin/Xmax 符号 + 配合范围
                         (合并了原 [FIT-CHECK])
        - [FIT-DECISION] 综合决策: 配合类型最终结论 + 关键参数 (审计追溯用)
        - [FIT-ERR-HOLE/SHAFT] 错误分支 (warning 级别)
    """
    ts = time.time()
    _logger.info(
        "[FIT-ENTRY] ts=%.6f nominal=%.1fmm hole=%s shaft=%s",
        ts, nominal_mm, hole_spec, shaft_spec,
    )

    hole = hole_tolerance(nominal_mm, hole_spec)
    shaft = shaft_tolerance(nominal_mm, shaft_spec)

    if 'error' in hole:
        _logger.warning(
            "[FIT-ERR-HOLE] ts=%.6f nominal=%.1fmm hole=%s -> %s",
            ts, nominal_mm, hole_spec, hole.get('error'),
        )
        return hole
    if 'error' in shaft:
        _logger.warning(
            "[FIT-ERR-SHAFT] ts=%.6f nominal=%.1fmm shaft=%s -> %s",
            ts, nominal_mm, shaft_spec, shaft.get('error'),
        )
        return shaft

    ES = hole['upper_dev_um']
    EI = hole['lower_dev_um']
    es = shaft['upper_dev_um']
    ei = shaft['lower_dev_um']

    # Xmax/Xmin: 孔-轴的间隙 (正=间隙, 负=过盈)
    #   Xmax = ES - ei   (最大间隙)  — 孔最大 - 轴最小
    #   Xmin = EI - es   (最小间隙)  — 孔最小 - 轴最大
    # Ymax/Ymin: 实际过盈量 (正=过盈, 与 Xmin/Xmax 互为相反数)
    #   Ymax = ei - ES   (最大过盈)  = -Xmax
    #   Ymin = es - EI   (最小过盈)  = -Xmin
    #
    # 三种配合的判别依据 (GB/T 1800.1-2009 §5):
    #   间隙配合: Xmin >= 0  (最小间隙为正, 即 Ymin <= 0)
    #   过盈配合: Xmax <= 0  (最大间隙为负, 即 Ymax >= 0)
    #   过渡配合: Xmin < 0 AND Xmax > 0  (既有过盈又有间隙)
    Xmax = ES - ei
    Xmin = EI - es
    Ymax = ei - ES   # 最大过盈 (正=过盈)
    Ymin = es - EI   # 最小过盈 (正=过盈)

    # [FIT-CALC] 合并原 [FIT-HOLE] + [FIT-SHAFT] + [FIT-XCALC] + [FIT-YCALC]
    # 单条日志同时记录孔/轴偏差与所有间隙/过盈值, 6 位小数精度
    _logger.info(
        "[FIT-CALC] ts=%.6f ES=%.6f EI=%.6f es=%.6f ei=%.6f "
        "Xmax=%.6f Xmin=%.6f Ymax=%.6f Ymin=%.6f",
        ts, ES, EI, es, ei,
        Xmax, Xmin, Ymax, Ymin,
    )

    # Ymax/Ymin 与 Xmax/Xmin 的不变性 (Ymax==-Xmax, Ymin==-Xmin) 是固定数学事实,
    # 无需每次记录. 调试时打开 DEBUG 级别可验证.
    _logger.debug(
        "[FIT-INVARIANT] ts=%.6f Ymax==-Xmax=%s Ymin==-Xmin=%s",
        ts, abs(Ymax + Xmax) < 1e-9, abs(Ymin + Xmin) < 1e-9,
    )

    # 判断配合类型 (基于 Xmin/Xmax 的符号, 互斥且完备)
    if Xmin >= 0:
        fit_type = '间隙配合'
        rule_hit = 'rule1(Xmin>=0)'
        xmin_mark = '>=0'
        xmax_mark = '>=0' if Xmax >= 0 else '<0'
        clearance = f'{Xmin} ~ {Xmax} μm'
        interference = '-'
        clearance_range = (Xmin, Xmax)
        interference_range = None
    elif Xmax <= 0:
        fit_type = '过盈配合'
        rule_hit = 'rule2(Xmax<=0)'
        xmin_mark = '<0' if Xmin < 0 else '=0'
        xmax_mark = '<=0'
        clearance = '-'
        interference = f'{-Xmax} ~ {-Xmin} μm'
        clearance_range = None
        interference_range = (-Xmax, -Xmin)
    else:
        fit_type = '过渡配合'
        rule_hit = 'rule3(Xmin<0 & Xmax>0)'
        xmin_mark = '<0'
        xmax_mark = '>0'
        # 过渡配合: 既有过盈又有间隙
        # 最大间隙 = Xmax (正), 最小过盈 = -Xmin (正)
        clearance = f'0 ~ {Xmax} μm' if Xmax > 0 else '-'
        interference = f'0 ~ {-Xmin} μm' if Xmin < 0 else '-'
        clearance_range = (0, Xmax) if Xmax > 0 else None
        interference_range = (0, -Xmin) if Xmin < 0 else None

        # [FIT-RULE3-DEBUG] 过渡配合分支详细中间变量日志
        # 用途: 排查过渡配合判定逻辑问题时, 完整复现决策过程
        #   - inputs: 孔轴偏差 (来自 hole_tolerance / shaft_tolerance)
        #   - calc:   Xmax/Xmin/Ymax/Ymin 数值构造 + 符号
        #   - rule_eval: 三条规则布尔评估 (确认 rule3 唯一命中)
        #   - derived: 派生量 (最大间隙 / 最小过盈)
        #   - range:  间隙/过盈区间
        rule1_eval = (Xmin >= 0)                              # 间隙配合
        rule2_eval = (Xmax <= 0)                              # 过盈配合
        rule3_eval = (Xmin < 0 and Xmax > 0)                  # 过渡配合
        min_interference = -Xmin if Xmin < 0 else 0
        _logger.info(
            "[FIT-RULE3-DEBUG] ts=%.6f nominal=%.1fmm hole=%s shaft=%s\n"
            "  inputs:    ES=%.6f EI=%.6f es=%.6f ei=%.6f\n"
            "  calc:      Xmax=ES-ei=%.6f-%.6f=%.6f(sign=%s)\n"
            "             Xmin=EI-es=%.6f-%.6f=%.6f(sign=%s)\n"
            "             Ymax=ei-ES=%.6f-%.6f=%.6f\n"
            "             Ymin=es-EI=%.6f-%.6f=%.6f\n"
            "  rule_eval: rule1(Xmin>=0)=%s  rule2(Xmax<=0)=%s  rule3(Xmin<0&Xmax>0)=%s\n"
            "  derived:   max_clearance=Xmax=%.6fμm  min_interference=-Xmin=%.6fμm\n"
            "  range:     clearance=%s  interference=%s\n"
            "  verdict:   fit_type=过渡配合 (rule3 命中)",
            ts, nominal_mm, hole_spec, shaft_spec,
            ES, EI, es, ei,
            ES, ei, Xmax, '+' if Xmax > 0 else ('=' if Xmax == 0 else '-'),
            EI, es, Xmin, '+' if Xmin > 0 else ('=' if Xmin == 0 else '-'),
            ei, ES, Ymax,
            es, EI, Ymin,
            rule1_eval, rule2_eval, rule3_eval,
            Xmax, min_interference,
            (f'[0, {Xmax:.6f}]μm' if clearance_range else 'N/A'),
            (f'[0, {min_interference:.6f}]μm' if interference_range else 'N/A'),
        )

    # [FIT-BRANCH] 合并原 [FIT-CHECK] + 分支判断逻辑
    # 单条日志: 命中规则 + Xmin/Xmax 符号 + 配合范围 (间隙/过盈)
    branch_msg = (
        "[FIT-BRANCH] ts=%.6f rule=%s "
        "Xmin=%.6f(%s) Xmax=%.6f(%s) Ymin=%.6f Ymax=%.6f -> fit_type=%s"
    )
    branch_args = [ts, rule_hit, Xmin, xmin_mark, Xmax, xmax_mark, Ymin, Ymax, fit_type]
    if clearance_range is not None:
        branch_msg += " clearance=[%.6f, %.6f]μm"
        branch_args += [clearance_range[0], clearance_range[1]]
    else:
        branch_msg += " clearance=N/A"
    if interference_range is not None:
        branch_msg += " interference=[%.6f, %.6f]μm"
        branch_args += [interference_range[0], interference_range[1]]
    else:
        branch_msg += " interference=N/A"
    _logger.info(branch_msg, *branch_args)

    # [FIT-DECISION] 综合决策日志: 配合类型最终结论 (审计追溯)
    _logger.info(
        "[FIT-DECISION] ts=%.6f nominal=%.1fmm hole=%s shaft=%s fit_type=%s "
        "Xmin=%.6f Xmax=%.6f Ymin=%.6f Ymax=%.6f",
        ts, nominal_mm, hole_spec, shaft_spec, fit_type,
        Xmin, Xmax, Ymin, Ymax,
    )

    return {
        'nominal_mm': nominal_mm,
        'hole_spec': hole['spec'],
        'shaft_spec': shaft['spec'],
        'hole_info': hole,
        'shaft_info': shaft,
        'fit_type': fit_type,
        'max_clearance_um': round(Xmax, 2),
        'min_clearance_um': round(Xmin, 2),
        # 最大过盈: 取 max(Xmax, 0) 与 min(Xmin, 0) 的差值的相反数
        # 当 Xmin<0 时, 最大过盈 = -Xmin; 当 Xmin>=0 时, 无过盈
        'max_interference_um': round(-Xmin if Xmin < 0 else 0, 2),
        'tolerance_um': round(abs(ES - EI) + abs(es - ei), 2),
        'fit_description': f'{fit_type}: {clearance if Xmin >= 0 else interference}',
    }


# 常用配合推荐
FIT_RECOMMENDATIONS = [
    {'fit': 'H7/h6', 'desc': '间隙配合', 'use': '精密滑动配合，如轴承座'},
    {'fit': 'H7/g6', 'desc': '间隙配合', 'use': '精密滑动配合，往复运动'},
    {'fit': 'H7/f7', 'desc': '间隙配合', 'use': '一般滑动配合，普通精度'},
    {'fit': 'H7/k6', 'desc': '过渡配合', 'use': '精确定位，可拆卸'},
    {'fit': 'H7/m6', 'desc': '过渡配合', 'use': '较紧定位，可拆卸'},
    {'fit': 'H7/n6', 'desc': '过渡配合', 'use': '紧配合，小过盈可能'},
    {'fit': 'H7/p6', 'desc': '过盈配合', 'use': '轻过盈，不常拆卸'},
    {'fit': 'H7/s6', 'desc': '过盈配合', 'use': '中等过盈，需压力装配'},
    {'fit': 'H7/u6', 'desc': '过盈配合', 'use': '重过盈，热装'},
]
