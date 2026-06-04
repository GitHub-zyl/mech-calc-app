"""P2 任务: 配合度推荐表 + 电机常识表 数据源

数据来源: 机械设计手册 (公差配合 / 电机选型)
"""
from typing import List, Dict, Any


# ============== 配合度推荐表 ==============
# 来源: GB/T 1800.1-2009 公差配合基础
# 字段说明:
#   - id:        唯一标识
#   - fit_type:  配合类型 (间隙/过渡/过盈)
#   - hole:      孔公差带代号 (如 H7)
#   - shaft:     轴公差带代号 (如 g6)
#   - application: 典型应用场景
#   - min_clearance_mm: 最小间隙 (mm, 过盈为负)
#   - max_clearance_mm: 最大间隙 (mm)
#   - nominal_range_mm: 适用公称尺寸范围 (mm)
#   - notes:     备注

FIT_RECOMMENDATIONS: List[Dict[str, Any]] = [
    # 间隙配合 (可相对运动)
    {
        'id': 'H7g6',
        'fit_type': '间隙',
        'category': '滑动',
        'hole': 'H7',
        'shaft': 'g6',
        'application': '精密滑动, 频繁拆装, 需精确定心',
        'min_clearance_mm': 0.001,
        'max_clearance_mm': 0.030,
        'nominal_range_mm': [3, 500],
        'examples': ['机床主轴', '精密分度盘', '活塞与缸套'],
        'notes': '最常用的精密滑动配合',
    },
    {
        'id': 'H7h6',
        'fit_type': '间隙',
        'category': '滑动',
        'hole': 'H7',
        'shaft': 'h6',
        'application': '一般滑动, 高定位精度',
        'min_clearance_mm': 0.000,
        'max_clearance_mm': 0.021,
        'nominal_range_mm': [3, 500],
        'examples': ['变速箱齿轮', '钻套与衬套'],
        'notes': '零间隙临界状态',
    },
    {
        'id': 'H8f7',
        'fit_type': '间隙',
        'category': '滑动',
        'hole': 'H8',
        'shaft': 'f7',
        'application': '中等转速滑动, 需良好润滑',
        'min_clearance_mm': 0.013,
        'max_clearance_mm': 0.071,
        'nominal_range_mm': [3, 500],
        'examples': ['轴瓦', '滑动轴承', '一般传动轴'],
        'notes': '中速滑动, 需要润滑油膜',
    },
    {
        'id': 'H9d9',
        'fit_type': '间隙',
        'category': '滑动',
        'hole': 'H9',
        'shaft': 'd9',
        'application': '粗大间隙, 低速重载',
        'min_clearance_mm': 0.045,
        'max_clearance_mm': 0.205,
        'nominal_range_mm': [3, 500],
        'examples': ['农业机械', '传动链条', '粗糙连接'],
        'notes': '粗糙机械常用, 公差松',
    },
    {
        'id': 'H11c11',
        'fit_type': '间隙',
        'category': '粗滑动',
        'hole': 'H11',
        'shaft': 'c11',
        'application': '粗大间隙, 露天设备',
        'min_clearance_mm': 0.060,
        'max_clearance_mm': 0.330,
        'nominal_range_mm': [3, 500],
        'examples': ['农机轴端', '粗糙连接器', '铰链接头'],
        'notes': '最粗糙间隙配合',
    },

    # 过渡配合 (可拆装, 需精确定心)
    {
        'id': 'H7k6',
        'fit_type': '过渡',
        'category': '轻过盈',
        'hole': 'H7',
        'shaft': 'k6',
        'application': '精确定心, 需偶尔拆装',
        'min_clearance_mm': -0.018,
        'max_clearance_mm': 0.012,
        'nominal_range_mm': [3, 500],
        'examples': ['带轮', '链轮', '齿轮与轴', '联轴器'],
        'notes': '最常用过渡配合, 可用木锤敲击拆装',
    },
    {
        'id': 'H7n6',
        'fit_type': '过渡',
        'category': '重过盈',
        'hole': 'H7',
        'shaft': 'n6',
        'application': '精确定心, 大冲击载荷',
        'min_clearance_mm': -0.023,
        'max_clearance_mm': 0.007,
        'nominal_range_mm': [3, 500],
        'examples': ['蜗轮', '重载齿轮', '飞轮'],
        'notes': '需用压力机装拆',
    },
    {
        'id': 'H7js6',
        'fit_type': '过渡',
        'category': '零过盈',
        'hole': 'H7',
        'shaft': 'js6',
        'application': '精确定心, 中等载荷',
        'min_clearance_mm': -0.006,
        'max_clearance_mm': 0.006,
        'nominal_range_mm': [3, 500],
        'examples': ['定位销', '定位套', '模具导柱'],
        'notes': '过渡区窄, 拆装频率高',
    },

    # 过盈配合 (永久连接)
    {
        'id': 'H7p6',
        'fit_type': '过盈',
        'category': '轻过盈',
        'hole': 'H7',
        'shaft': 'p6',
        'application': '永久连接, 需加热/加压',
        'min_clearance_mm': -0.030,
        'max_clearance_mm': 0.000,
        'nominal_range_mm': [3, 500],
        'examples': ['滚动轴承内圈', '衬套', '销钉'],
        'notes': '常用加热装配法 (200°C)',
    },
    {
        'id': 'H7s6',
        'fit_type': '过盈',
        'category': '重过盈',
        'hole': 'H7',
        'shaft': 's6',
        'application': '高载荷永久连接',
        'min_clearance_mm': -0.047,
        'max_clearance_mm': 0.000,
        'nominal_range_mm': [3, 500],
        'examples': ['重载衬套', '轴套', '大齿轮'],
        'notes': '需用压力机或加热装配',
    },
    {
        'id': 'H8u8',
        'fit_type': '过盈',
        'category': '特重过盈',
        'hole': 'H8',
        'shaft': 'u8',
        'application': '特大过盈, 永久连接',
        'min_clearance_mm': -0.110,
        'max_clearance_mm': 0.000,
        'nominal_range_mm': [3, 500],
        'examples': ['大型轴瓦', '重载法兰', '联轴器'],
        'notes': '需用热装+冷压组合',
    },

    # 压入装配 (常用)
    {
        'id': 'H7r6',
        'fit_type': '过盈',
        'category': '中过盈',
        'hole': 'H7',
        'shaft': 'r6',
        'application': '中等过盈, 压力机装配',
        'min_clearance_mm': -0.038,
        'max_clearance_mm': 0.000,
        'nominal_range_mm': [3, 500],
        'examples': ['滚动轴承内圈', '中等衬套'],
        'notes': '常用压力机冷装',
    },
    {
        'id': 'H6n5',
        'fit_type': '过渡',
        'category': '精密',
        'hole': 'H6',
        'shaft': 'n5',
        'application': '高精度定心',
        'min_clearance_mm': -0.016,
        'max_clearance_mm': 0.004,
        'nominal_range_mm': [3, 500],
        'examples': ['精密轴承', '测量仪器'],
        'notes': 'IT6 精度级别, 精密设备',
    },
    {
        'id': 'H11a11',
        'fit_type': '间隙',
        'category': '特大',
        'hole': 'H11',
        'shaft': 'a11',
        'application': '极大间隙, 热胀冷缩补偿',
        'min_clearance_mm': 0.180,
        'max_clearance_mm': 0.560,
        'nominal_range_mm': [3, 500],
        'examples': ['管道法兰', '热补偿接头'],
        'notes': '温度变化大场合',
    },
]


# ============== 电机常识表 ==============
# 来源: 电机选型手册 / 电工手册
# 字段说明:
#   - id:           唯一标识
#   - name_zh:      中文名
#   - name_en:      英文名
#   - category:     分类 (类型/启动/调速/制动/保护/铭牌)
#   - value:        参数值或说明
#   - unit:         单位 (如有)
#   - description:  详细说明
#   - formula:      关联公式 (如有)
#   - reference:    手册参考

MOTOR_KNOWLEDGE: List[Dict[str, Any]] = [
    # 电机类型
    {
        'id': 'motor_type_3phase_async',
        'name_zh': '三相异步电动机',
        'name_en': 'Three-Phase Asynchronous Motor',
        'category': '类型',
        'value': 'Y系列',
        'description': '最常用的工业电机, 结构简单、运行可靠、价格低, 适用于一般机械传动',
        'formula': None,
        'reference': 'GB/T 28575',
    },
    {
        'id': 'motor_type_servo',
        'name_zh': '伺服电动机',
        'name_en': 'Servo Motor',
        'category': '类型',
        'value': '永磁同步',
        'description': '高精度位置/速度控制, 用于 CNC、机器人、印刷设备',
        'formula': None,
        'reference': 'GB/T 16439',
    },
    {
        'id': 'motor_type_stepper',
        'name_zh': '步进电动机',
        'name_en': 'Stepper Motor',
        'category': '类型',
        'value': '两相/三相混合式',
        'description': '开环控制, 适用于低速高精度场景 (3D 打印机, 小型 CNC)',
        'formula': None,
        'reference': 'GB/T 20638',
    },
    {
        'id': 'motor_type_dc',
        'name_zh': '直流电动机',
        'name_en': 'DC Motor',
        'category': '类型',
        'value': '有刷/无刷',
        'description': '调速范围宽, 起动转矩大, 用于牵引、起重、精密调速系统',
        'formula': None,
        'reference': 'GB/T 1311',
    },

    # 同步转速
    {
        'id': 'motor_sync_speed_50hz_2p',
        'name_zh': '同步转速 50Hz 2极',
        'name_en': 'Synchronous Speed 50Hz 2P',
        'category': '转速',
        'value': 3000,
        'unit': 'r/min',
        'description': '电网频率 50Hz, 2 极电机的同步转速',
        'formula': 'n0 = 60 * f / p',
        'reference': '电工手册 §3.2',
    },
    {
        'id': 'motor_sync_speed_50hz_4p',
        'name_zh': '同步转速 50Hz 4极',
        'name_en': 'Synchronous Speed 50Hz 4P',
        'category': '转速',
        'value': 1500,
        'unit': 'r/min',
        'description': '电网频率 50Hz, 4 极电机的同步转速 (最常用)',
        'formula': 'n0 = 60 * f / p',
        'reference': '电工手册 §3.2',
    },
    {
        'id': 'motor_sync_speed_50hz_6p',
        'name_zh': '同步转速 50Hz 6极',
        'name_en': 'Synchronous Speed 50Hz 6P',
        'category': '转速',
        'value': 1000,
        'unit': 'r/min',
        'description': '电网频率 50Hz, 6 极电机的同步转速',
        'formula': 'n0 = 60 * f / p',
        'reference': '电工手册 §3.2',
    },
    {
        'id': 'motor_async_slip',
        'name_zh': '异步电机转差率',
        'name_en': 'Asynchronous Motor Slip',
        'category': '转速',
        'value': '1%~5%',
        'description': '转差率 s = (n0 - n) / n0, 额定负载时通常 1%~5%, 决定转矩特性',
        'formula': 's = (n0 - n) / n0',
        'reference': '电机学 §4.3',
    },

    # 起动
    {
        'id': 'motor_start_direct',
        'name_zh': '直接起动',
        'name_en': 'Direct-on-line Start',
        'category': '起动',
        'value': 'DOL',
        'description': '起动电流为额定电流 4~7 倍, 适用于小功率 (≤7.5kW) 或电网容量大的场合',
        'formula': None,
        'reference': 'GB 50054',
    },
    {
        'id': 'motor_start_star_delta',
        'name_zh': '星-三角起动',
        'name_en': 'Star-Delta Start',
        'category': '起动',
        'value': 'Y-Δ',
        'description': '起动电流降为直接起动的 1/3, 起动转矩也降为 1/3, 适用于空载/轻载起动',
        'formula': 'I_Y = I_Δ / 3, T_Y = T_Δ / 3',
        'reference': 'GB 50054',
    },
    {
        'id': 'motor_start_soft',
        'name_zh': '软起动器',
        'name_en': 'Soft Starter',
        'category': '起动',
        'value': '晶闸管调压',
        'description': '通过降压平滑起动, 起动电流可调, 减小电网冲击',
        'formula': None,
        'reference': 'GB 14048.6',
    },
    {
        'id': 'motor_start_vfd',
        'name_zh': '变频起动',
        'name_en': 'Variable Frequency Start',
        'category': '起动',
        'value': 'VFD/变频器',
        'description': '通过变频实现真正软起动, 同时具备调速功能, 节能效果好',
        'formula': 'n = 60 * f * (1-s) / p',
        'reference': 'GB 12668',
    },

    # 调速
    {
        'id': 'motor_speed_regulation_vfd',
        'name_zh': '变频调速',
        'name_en': 'VFD Speed Regulation',
        'category': '调速',
        'value': '1:10 以上',
        'description': '通过改变电源频率实现无级调速, 调速范围宽, 节能, 是现代主流调速方式',
        'formula': 'n = 60 * f * (1-s) / p',
        'reference': 'GB 12668',
    },
    {
        'id': 'motor_speed_regulation_dc',
        'name_zh': '直流调速',
        'name_en': 'DC Speed Regulation',
        'category': '调速',
        'value': '1:20 以上',
        'description': '通过改变电枢电压调速, 调速平滑, 范围宽, 但维护成本高',
        'formula': 'n = (U - I*R) / (k*Φ)',
        'reference': '电机学 §5.4',
    },

    # 制动
    {
        'id': 'motor_brake_plug',
        'name_zh': '能耗制动',
        'name_en': 'Dynamic Braking',
        'category': '制动',
        'value': 'DC 注入',
        'description': '切断交流电源后注入直流电产生制动转矩, 快速停车',
        'formula': None,
        'reference': '电工手册 §3.5',
    },
    {
        'id': 'motor_brake_regen',
        'name_zh': '回馈制动',
        'name_en': 'Regenerative Braking',
        'category': '制动',
        'value': '发电状态',
        'description': '电机超同步运行 (如重物下放) 时作为发电机, 将能量回馈电网',
        'formula': None,
        'reference': '电工手册 §3.5',
    },
    {
        'id': 'motor_brake_mech',
        'name_zh': '机械制动',
        'name_en': 'Mechanical Brake',
        'category': '制动',
        'value': '电磁制动器',
        'description': '通过弹簧+电磁铁的失电制动器实现停车, 简单可靠',
        'formula': None,
        'reference': 'GB/T 24478',
    },

    # 保护
    {
        'id': 'motor_protection_overload',
        'name_zh': '过载保护',
        'name_en': 'Overload Protection',
        'category': '保护',
        'value': '热继电器',
        'description': '通过双金属片或电子元件检测过载电流, 延时跳闸',
        'formula': None,
        'reference': 'GB 14048.4',
    },
    {
        'id': 'motor_protection_short',
        'name_zh': '短路保护',
        'name_en': 'Short-Circuit Protection',
        'category': '保护',
        'value': '熔断器/断路器',
        'description': '瞬时切断短路电流, 保护电机绕组',
        'formula': None,
        'reference': 'GB 14048.2',
    },
    {
        'id': 'motor_protection_phase_loss',
        'name_zh': '缺相保护',
        'name_en': 'Phase-Loss Protection',
        'category': '保护',
        'value': '相序继电器',
        'description': '检测三相电源缺相, 防止单相运行烧毁电机',
        'formula': None,
        'reference': 'GB 14048.4',
    },

    # 铭牌参数
    {
        'id': 'motor_nameplate_power',
        'name_zh': '额定功率',
        'name_en': 'Rated Power',
        'category': '铭牌',
        'value': 'Pn',
        'unit': 'kW',
        'description': '电机轴端输出的机械功率, 选型时按负载功率×系数(1.1~1.3)',
        'formula': None,
        'reference': 'GB 755',
    },
    {
        'id': 'motor_nameplate_voltage',
        'name_zh': '额定电压',
        'name_en': 'Rated Voltage',
        'category': '铭牌',
        'value': '380V / 220V / 660V',
        'unit': 'V',
        'description': '中国常用 380V 三相, 660V 用于矿井, 220V 单相',
        'formula': None,
        'reference': 'GB 755',
    },
    {
        'id': 'motor_nameplate_current',
        'name_zh': '额定电流',
        'name_en': 'Rated Current',
        'category': '铭牌',
        'value': 'In',
        'unit': 'A',
        'description': '电机额定运行时的线电流, 用于选配电缆/开关',
        'formula': 'I = P / (√3 * U * cosφ * η)',
        'reference': 'GB 755',
    },
    {
        'id': 'motor_nameplate_efficiency',
        'name_zh': '效率',
        'name_en': 'Efficiency',
        'category': '铭牌',
        'value': 'IE3 85%~95%',
        'description': '电机效率等级 IE1~IE4, IE3 为目前国标强制最低, IE4 高效',
        'formula': 'η = P_out / P_in',
        'reference': 'GB 18613',
    },
    {
        'id': 'motor_nameplate_cosphi',
        'name_zh': '功率因数',
        'name_en': 'Power Factor',
        'category': '铭牌',
        'value': '0.85~0.90',
        'description': 'cosφ, 电机消耗的有功功率与视在功率之比, 异步电机滞后',
        'formula': 'cosφ = P / (√3 * U * I)',
        'reference': 'GB 755',
    },

    # 防护等级
    {
        'id': 'motor_ip44',
        'name_zh': 'IP44 防护',
        'name_en': 'IP44 Protection',
        'category': '防护',
        'value': 'IP44',
        'description': '防溅水+防直径≥1mm 固体, 适用于一般工业环境',
        'formula': None,
        'reference': 'GB 4208',
    },
    {
        'id': 'motor_ip54',
        'name_zh': 'IP54 防护',
        'name_en': 'IP54 Protection',
        'category': '防护',
        'value': 'IP54',
        'description': '防尘+防溅水, 适用于多尘或潮湿环境',
        'formula': None,
        'reference': 'GB 4208',
    },
    {
        'id': 'motor_ip55',
        'name_zh': 'IP55 防护',
        'name_en': 'IP55 Protection',
        'category': '防护',
        'value': 'IP55',
        'description': '防尘+防喷水, 户外或水雾环境',
        'formula': None,
        'reference': 'GB 4208',
    },

    # 绝缘等级
    {
        'id': 'motor_insulation_b',
        'name_zh': 'B 级绝缘',
        'name_en': 'Class B Insulation',
        'category': '绝缘',
        'value': '130°C',
        'description': '最高工作温度 130°C, 旧标准电机常用',
        'formula': None,
        'reference': 'GB 11021',
    },
    {
        'id': 'motor_insulation_f',
        'name_zh': 'F 级绝缘',
        'name_en': 'Class F Insulation',
        'category': '绝缘',
        'value': '155°C',
        'description': '最高工作温度 155°C, 现代电机主流',
        'formula': None,
        'reference': 'GB 11021',
    },
    {
        'id': 'motor_insulation_h',
        'name_zh': 'H 级绝缘',
        'name_en': 'Class H Insulation',
        'category': '绝缘',
        'value': '180°C',
        'description': '最高工作温度 180°C, 用于高温/特殊场合',
        'formula': None,
        'reference': 'GB 11021',
    },
]


# ============== 工具函数 ==============

def get_fit_recommendations(fit_type: str = None, category: str = None) -> List[Dict[str, Any]]:
    """获取配合度推荐表. 可选筛选."""
    result = FIT_RECOMMENDATIONS
    if fit_type:
        result = [f for f in result if f['fit_type'] == fit_type]
    if category:
        result = [f for f in result if f['category'] == category]
    return result


def get_motor_knowledge(category: str = None) -> List[Dict[str, Any]]:
    """获取电机常识. 可选分类筛选."""
    result = MOTOR_KNOWLEDGE
    if category:
        result = [k for k in result if k['category'] == category]
    return result


def get_motor_categories() -> List[str]:
    """获取电机常识的所有分类."""
    return sorted({k['category'] for k in MOTOR_KNOWLEDGE})


def get_fit_categories() -> List[str]:
    """获取配合度推荐的所有分类."""
    return sorted({f['category'] for f in FIT_RECOMMENDATIONS})


def get_fit_types() -> List[str]:
    """获取配合类型 (间隙/过渡/过盈)."""
    return sorted({f['fit_type'] for f in FIT_RECOMMENDATIONS})
