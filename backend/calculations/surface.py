"""
表面粗糙度与硬度换算模块
参考：GB/T 1031-2009, GB/T 3505, ISO 4287, GB/T 1172, ASTM E140
"""


def calc_roughness_convert(Ra=None):
    """
    Ra → Rz → Ry → RMS 近似转换
    
    常用近似关系 (适用于常规机械加工表面):
    Rz ≈ 4·Ra
    Ry ≈ 5·Ra
    RMS ≈ 1.11·Ra
    Rq ≈ 1.25·Ra
    
    参数:
        Ra: 轮廓算术平均偏差 (μm)
    
    返回: 各种粗糙度参数的近似值
    """
    if Ra is None:
        return {'error': '请提供 Ra 值 (μm)'}

    Rz = 4 * Ra
    Ry = 5 * Ra
    RMS = 1.11 * Ra
    Rq = 1.25 * Ra
    Rmax = 6 * Ra
    Rtm = 4.5 * Ra

    return {
        'Ra_um': Ra,
        'Rz_um': round(Rz, 2),
        'Ry_um': round(Ry, 2),
        'Rq_RMS_um': round(Rq, 2),
        'RMS_um': round(RMS, 2),
        'Rmax_um': round(Rmax, 2),
        'Rtm_um': round(Rtm, 2),
        'note': '近似换算关系, 精密换算需实测值',
        'formula': 'Rz≈4Ra, Ry≈5Ra, RMS≈1.11Ra, Rq≈1.25Ra',
        'reference': 'GB/T 1031-2009 / 机械设计手册(成大先)第15篇',
    }


def calc_hardness_convert(value=None, from_type='HB', to_type='HRC'):
    """
    硬度换算 (碳钢/合金钢范围)
    
    支持: HB (布氏), HV (维氏), HRC (洛氏C), HRB (洛氏B), HS (肖氏)
    
    近似换算关系 (经验公式):
    - HB≈HV (在 HB<450 范围)
    - HRC ≈ (100 - 150 / √HB) 或 HB ≈ 37.3 × (100 - HRC)^1.85 (近似的倒数)
    - HB≈HRB/0.5 (仅在 HRB 范围, 约 HB 50-130)
    - HS ≈ HB/10
    
    常用对照 (钢材):
    HB 200 ≈ HRC 14, HB 250 ≈ HRC 23, HB 300 ≈ HRC 30, HB 350 ≈ HRC 36, HB 400 ≈ HRC 41, HB 450 ≈ HRC 45
    
    参数:
        value: 数值
        from_type: 'HB'|'HV'|'HRC'|'HRB'|'HS'
        to_type: 'HB'|'HV'|'HRC'|'HRB'|'HS'
    
    返回: 换算值 + 适用范围说明
    """
    if value is None:
        return {'error': '请提供硬度值 value'}

    from_type = from_type.upper()
    to_type = to_type.upper()

    if from_type == to_type:
        return {'value': value, 'from': from_type, 'to': to_type, 'converted': value}

    def to_hb(val, t):
        """全部先转到 HB

        校准参考: ASTM E140 / GB/T 1172-1999
        HRC→HB 反向公式 (基于正向线性拟合的逆函数):
            HB = (HRC + 14.6) / 0.143
        """
        if t == 'HB':
            return val
        elif t == 'HV':
            return val  # 近似
        elif t == 'HRC':
            if val <= 0:
                return 0
            # 反向公式: HB = (HRC + 14.6) / 0.143
            return (val + 14.6) / 0.143
        elif t == 'HRB':
            return val / 0.5 if val > 0 else 0
        elif t == 'HS':
            return val * 10
        return 0

    def from_hb(val, t):
        """从 HB 转到目标

        校准参考: ASTM E140 / GB/T 1172-1999
        HB→HRC 关系在 200-450 范围内近似线性:
            HRC = 0.143 × HB - 14.6
        验证点 (ASTM E140 表):
            HB 200 → HRC 13.5   (公式: 14.0)
            HB 250 → HRC 22.0   (公式: 21.2)
            HB 300 → HRC 29.8   (公式: 28.3)
            HB 350 → HRC 36.0   (公式: 35.5)
            HB 400 → HRC 41.5   (公式: 42.6)
            HB 450 → HRC 45.7   (公式: 49.8)
        """
        if t == 'HB':
            return val
        elif t == 'HV':
            return val
        elif t == 'HRC':
            # 校准后的线性公式 (替代原 max(0, min(70, 100 - (val/37.3)^(1/1.85))) 的错误截断)
            if val <= 0:
                return 0
            if val < 180:
                # 低于 HRC 量程 (HRC 仅适用 ~20-68)
                return 0
            hrc = 0.143 * val - 14.6
            return max(0, min(70, hrc))
        elif t == 'HRB':
            return val * 0.5
        elif t == 'HS':
            return val / 10
        return 0

    hb = to_hb(value, from_type)
    converted = round(from_hb(hb, to_type), 2)

    # 适用范围
    range_notes = {
        'HB': '适用范围: 10~650 HB',
        'HV': '适用范围: 10~1800 HV',
        'HRC': '适用范围: 20~68 HRC (碳钢/合金钢)',
        'HRB': '适用范围: 20~100 HRB',
        'HS': '适用范围: 5~105 HS',
    }

    return {
        'value_original': value,
        'from_type': from_type,
        'to_type': to_type,
        'value_converted': round(converted, 1),
        'approx_HB': round(hb, 1),
        'applicable_range': range_notes.get(to_type, '近似换算, 参考值'),
        'note': '近似换算公式 (碳钢/合金钢)，精确换算需查 GB/T 1172 对照表',
        'formula': '基于 GB/T 1172 硬度换算的近似拟合',
        'reference': 'GB/T 1172-1999 / ASTM E140',
    }


def calc_surface_texture(Ra=None, process=None):
    """
    推荐加工方法和精度等级
    
    根据 Ra 值推荐对应的加工方法和应用场景
    
    参数:
        Ra: 表面粗糙度 (μm)
        process: 加工方法（可选，用于验证可行性）
    """
    if Ra is None:
        return {'error': '请提供 Ra 值 (μm)'}

    # Ra 等级表
    ra_table = [
        {'Ra_max': 0.025, 'Ra_min': 0.012, 'grade': 'IT5', 'symbol': '▽▽▽▽',
         'process': '超精磨/珩磨/超精加工', 'application': '精密量具、精密轴承、块规'},
        {'Ra_max': 0.05, 'Ra_min': 0.025, 'grade': 'IT5-6', 'symbol': '▽▽▽▽',
         'process': '精磨/珩磨', 'application': '量具工作面、高速精密主轴'},
        {'Ra_max': 0.10, 'Ra_min': 0.05, 'grade': 'IT6', 'symbol': '▽▽▽',
         'process': '精磨/研磨/精铰', 'application': '轴承轴颈、活塞销、精密齿轮'},
        {'Ra_max': 0.20, 'Ra_min': 0.10, 'grade': 'IT6-7', 'symbol': '▽▽▽',
         'process': '磨削/精铰', 'application': '一般精密配件、导轨面、凸轮轴'},
        {'Ra_max': 0.40, 'Ra_min': 0.20, 'grade': 'IT7', 'symbol': '▽▽▽',
         'process': '磨削/精车/精铣', 'application': '齿轮齿面、滚动轴承配合面'},
        {'Ra_max': 0.80, 'Ra_min': 0.40, 'grade': 'IT8', 'symbol': '▽▽',
         'process': '精车/精铣/铰削', 'application': '一般配合面、轴套、法兰面'},
        {'Ra_max': 1.60, 'Ra_min': 0.80, 'grade': 'IT8-9', 'symbol': '▽▽',
         'process': '车削/铣削/镗削', 'application': '键槽、非配合面、支架面'},
        {'Ra_max': 3.20, 'Ra_min': 1.60, 'grade': 'IT9-10', 'symbol': '▽▽',
         'process': '粗车/粗铣/钻削', 'application': '一般非重要表面、焊接件'},
        {'Ra_max': 6.30, 'Ra_min': 3.20, 'grade': 'IT10-11', 'symbol': '▽',
         'process': '粗加工/锯切', 'application': '不打磨的焊接件、铸件'},
        {'Ra_max': 12.5, 'Ra_min': 6.30, 'grade': 'IT11-12', 'symbol': '▽',
         'process': '粗加工/热轧', 'application': '非功能面、毛坯面'},
        {'Ra_max': 25.0, 'Ra_min': 12.5, 'grade': 'IT12+', 'symbol': '▽',
         'process': '锻造/铸造', 'application': '毛坯面、自由公差面'},
    ]

    matched = None
    for row in ra_table:
        if Ra <= row['Ra_max'] and Ra >= row['Ra_min']:
            matched = row
            break

    result = {
        'Ra_um': Ra,
    }

    if matched:
        result['IT_grade'] = matched['grade']
        result['symbol'] = matched['symbol']
        result['recommended_process'] = matched['process']
        result['application'] = matched['application']
    else:
        result['IT_grade'] = '超出常见范围'
        result['recommended_process'] = '需特殊工艺' if Ra < 0.012 else '铸造/锻造毛坯'
        result['application'] = '特殊精密件' if Ra < 0.012 else '毛坯'

    result['reference'] = 'GB/T 1031-2009 / 机械设计手册(成大先)第15篇 §2'

    return result
