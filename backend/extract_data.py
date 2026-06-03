"""
从《机械设计常用计算表.xlsx》提取所有结构化数据，导出为JSON
"""
import openpyxl
import json
import os

EXCEL_PATH = r'\\192.168.0.20\张有亮的个人云\研究用\机械相关计算\机械设计常用计算表.xlsx'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def to_num(v):
    """尝试转为数字"""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return v

def sheet_to_dict(ws, header_rows=1, key_col=0, val_col=1):
    """简单地将工作表转换为 {key: value} 字典"""
    data = {}
    for row in ws.iter_rows(min_row=header_rows+1, values_only=True):
        if row[0] is not None:
            key = str(row[key_col]).strip() if row[key_col] else ''
            val = row[val_col] if val_col < len(row) else None
            if key:
                data[key] = to_num(val) if val is not None else None
    return data

def extract_materials(ws):
    """提取常用工程材料属性"""
    materials = []
    headers = []
    for row in ws.iter_rows(min_row=1, max_row=2, values_only=True):
        for cell in row:
            if cell and str(cell).strip():
                headers.append(str(cell).strip())
    
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] is None or str(row[0]).strip() == '':
            continue
        name = str(row[0]).strip()
        if name in ('材料名称', '') or '返回' in name:
            continue
        entry = {
            'name': name,
            'elastic_modulus': to_num(row[1]),        # 弹性模量 N/m²
            'poisson_ratio': to_num(row[2]),           # 泊松比
            'density': to_num(row[3]),                 # 密度 kg/m³
            'shear_modulus': to_num(row[4]),           # 抗剪模量
            'tensile_strength': to_num(row[5]),        # 抗拉强度 N/m²
            'tensile_strength_mpa': to_num(row[6]),    # 抗拉强度 MPa
            'yield_strength': to_num(row[7]),          # 屈服强度 N/m²
            'yield_strength_mpa': to_num(row[8]),      # 屈服强度 MPa
            'thermal_expansion': to_num(row[9]),       # 热膨胀系数
            'specific_heat': to_num(row[10]),          # 比热
            'thermal_conductivity': to_num(row[11]),   # 热导率
        }
        materials.append(entry)
    return materials

def extract_steel_grades(ws):
    """提取七国钢材牌号对照"""
    steels = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] is None:
            continue
        name = str(row[0]).strip()
        if name in ('钢号', '', 'GB') or '返回' in name:
            continue
        entry = {
            'category': str(row[0]).strip() if row[0] else '',
            'china_gb': str(row[1]).strip() if row[1] else '',
            'russia_gost': str(row[2]).strip() if row[2] else '',
            'usa_astm': str(row[3]).strip() if row[3] else '',
            'uk_bs': str(row[4]).strip() if row[4] else '',
            'japan_jis': str(row[5]).strip() if row[5] else '',
            'france_nf': str(row[6]).strip() if row[6] else '',
            'germany_din': str(row[7]).strip() if row[7] else '',
        }
        steels.append(entry)
    return steels

def extract_aluminum_grades(ws):
    """提取七国铝及铝合金牌号对照"""
    alums = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] is None:
            continue
        name = str(row[0]).strip()
        if name in ('类', '', '别') or '返回' in name:
            continue
        entry = {
            'category': str(row[0]).strip() if row[0] else '',
            'china_gb': str(row[1]).strip() if row[1] else '',
            'usa_astm': str(row[2]).strip() if row[2] else '',
            'uk_bs': str(row[3]).strip() if row[3] else '',
            'japan_jis': str(row[4]).strip() if row[4] else '',
            'france_nf': str(row[5]).strip() if row[5] else '',
            'germany_din': str(row[6]).strip() if row[6] else '',
        }
        alums.append(entry)
    return alums

def extract_plastics(ws):
    """提取塑料材料性能"""
    plastics = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] is None:
            continue
        name = str(row[0]).strip()
        if name in ('序号', '', '塑料名称') or '返回' in name:
            continue
        entry = {
            'name': name,
            'code': str(row[1]).strip() if row[1] and str(row[1]).strip() else '',
            'fluidity': str(row[2]).strip() if row[2] and str(row[2]).strip() else '',
            'yield_strength': to_num(row[3]),
            'tensile_strength': to_num(row[4]),
            'shrinkage': to_num(row[5]),
            'water_absorption': to_num(row[6]),
            'thermal_expansion': to_num(row[7]),
            'density': to_num(row[11]) if row[11] else None,
            'bending_strength': to_num(row[12]),
        }
        plastics.append(entry)
    return plastics

def extract_thread_data(ws):
    """提取公制螺纹数据 (ISO 68格式)"""
    threads = []
    seen = set()
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[0] is None:
            continue
        try:
            size = str(row[0]).strip()
            if size == '' or '返回' in size:
                continue
            fd = float(size)
            if fd <= 0:
                continue
        except (ValueError, TypeError):
            continue
        
        # 螺纹代号在B列，如 "M6x1"
        designation = str(row[1]).strip() if row[1] else ''
        if designation and designation.startswith('M') and designation not in seen:
            seen.add(designation)
            # 提取公称直径和螺距
            try:
                # M6x1 → (6, 1), M6 → (6, None)
                import re
                m = re.match(r'M(\d+(?:\.\d+)?)[xX]?(\d+(?:\.\d+)?)?', designation)
                if m:
                    major = float(m.group(1))
                    pitch = float(m.group(2)) if m.group(2) else None
                    entry = {
                        'designation': designation,
                        'nominal_diameter': major,
                        'pitch': pitch,
                        'external_major_max': to_num(row[3]),
                        'external_major_min': to_num(row[4]),
                        'external_pitch_max': to_num(row[5]),
                        'external_pitch_min': to_num(row[6]),
                        'external_minor_max': to_num(row[7]),
                        'external_minor_min': to_num(row[8]),
                    }
                    threads.append(entry)
            except:
                continue
    
    # 去重
    unique = {}
    for t in threads:
        key = t['designation']
        if key not in unique:
            unique[key] = t
    return list(unique.values())


def extract_imperial_thread(ws):
    """提取英制/美制螺纹底孔数据"""
    threads = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        try:
            spec = str(row[0]).strip()
            if not spec or '返回' in spec or spec in ('规格', '螺纹规格'):
                continue
            entry = {
                'spec': spec,
                'pitch_mm': to_num(row[1]),
                'tap_drill_mm': to_num(row[2]),
                'pitch_diameter_mm': to_num(row[3]),
                'minor_diameter_mm': to_num(row[4]),
            }
            threads.append(entry)
        except:
            continue
    return threads


def extract_bearings_more(ws_deep, ws_thrust):
    """提取更多轴承型号数据"""
    bearings = []
    for ws in [ws_deep, ws_thrust] if ws_thrust else [ws_deep]:
        if ws is None:
            continue
        for row in ws.iter_rows(min_row=3, values_only=True):
            if row[0] is None:
                continue
            try:
                model = str(row[0]).strip()
                if not model or '返回' in model or model in ('型号',):
                    continue
                bore = to_num(row[1])
                if bore and isinstance(bore, (int, float)):
                    bearings.append({
                        'model': model,
                        'bore_mm': float(row[1]) if row[1] else None,
                        'outer_mm': float(row[2]) if row[2] else None,
                        'width_mm': float(row[3]) if row[3] else None,
                    })
            except:
                continue
    return bearings

def extract_bearing_data(ws, bearing_type='deep_groove'):
    """提取轴承数据"""
    bearings = []
    start_row = 3 if bearing_type == 'deep_groove' else 2
    for row in ws.iter_rows(min_row=start_row, values_only=True):
        if row[0] is None:
            continue
        try:
            bore = to_num(row[1]) if row[1] else None
            if bore and isinstance(bore, (int, float)):
                entry = {
                    'model': str(row[0]).strip() if row[0] else '',
                    'bore_diameter': float(row[1]) if row[1] else None,
                    'outer_diameter': float(row[2]) if row[2] else None,
                    'width': float(row[3]) if row[3] else None,
                }
                bearings.append(entry)
        except (ValueError, TypeError):
            continue
    return bearings

def extract_oring_data():
    """提取O型圈沟槽数据"""
    orings = [
        {'section_diameter': 1.8, 'groove_depth': 1.3, 'groove_width': 2.4},
        {'section_diameter': 1.9, 'groove_depth': 1.4, 'groove_width': 2.6},
        {'section_diameter': 2.0, 'groove_depth': 1.5, 'groove_width': 2.8},
        {'section_diameter': 2.4, 'groove_depth': 1.8, 'groove_width': 3.2},
        {'section_diameter': 2.5, 'groove_depth': 1.9, 'groove_width': 3.4},
        {'section_diameter': 2.6, 'groove_depth': 2.0, 'groove_width': 3.6},
        {'section_diameter': 3.0, 'groove_depth': 2.3, 'groove_width': 4.0},
        {'section_diameter': 3.1, 'groove_depth': 2.4, 'groove_width': 4.2},
        {'section_diameter': 3.5, 'groove_depth': 2.7, 'groove_width': 4.8},
        {'section_diameter': 4.0, 'groove_depth': 3.1, 'groove_width': 5.4},
        {'section_diameter': 4.5, 'groove_depth': 3.5, 'groove_width': 6.0},
        {'section_diameter': 5.0, 'groove_depth': 3.9, 'groove_width': 6.8},
        {'section_diameter': 5.5, 'groove_depth': 4.3, 'groove_width': 7.4},
        {'section_diameter': 6.0, 'groove_depth': 4.7, 'groove_width': 8.0},
        {'section_diameter': 7.0, 'groove_depth': 5.5, 'groove_width': 9.2},
    ]
    return orings


def main():
    print("正在加载Excel文件...")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    
    data = {
        'materials': [],
        'steel_grades': [],
        'aluminum_grades': [],
        'plastics': [],
        'threads_metric': [],
        'threads_imperial': [],
        'bearings_deep_groove': [],
        'bearings_thrust': [],
        'misc': {}
    }
    
    # 1. 常用工程材料属性
    print("提取材料属性...")
    if '常用工程材料属性' in wb.sheetnames:
        ws = wb['常用工程材料属性']
        data['materials'] = extract_materials(ws)
        print(f"  → {len(data['materials'])} 种材料")
    
    # 2. 钢材牌号对照
    print("提取钢材牌号对照...")
    if '七国钢材牌号对照表' in wb.sheetnames:
        ws = wb['七国钢材牌号对照表']
        data['steel_grades'] = extract_steel_grades(ws)
        print(f"  → {len(data['steel_grades'])} 种钢材")
    
    # 3. 铝材牌号对照
    print("提取铝材牌号对照...")
    if '七国铝及其合金牌号对照表' in wb.sheetnames:
        ws = wb['七国铝及其合金牌号对照表']
        data['aluminum_grades'] = extract_aluminum_grades(ws)
        print(f"  → {len(data['aluminum_grades'])} 种铝材")
    
    # 4. 塑料材料性能
    print("提取塑料材料性能...")
    if '塑料材料性能' in wb.sheetnames:
        ws = wb['塑料材料性能']
        data['plastics'] = extract_plastics(ws)
        print(f"  → {len(data['plastics'])} 种塑料")
    
    # 5. 公制螺纹 (ISO格式)
    print("提取公制螺纹数据...")
    if '公制螺纹大全' in wb.sheetnames:
        ws = wb['公制螺纹大全']
        data['threads_metric'] = extract_thread_data(ws)
        print(f"  → {len(data['threads_metric'])} 种螺纹规格")
    
    # 6. 英制螺纹底孔
    print("提取英制螺纹底孔...")
    for sname in ['英制螺纹底孔对照表', '英制螺纹']:
        if sname in wb.sheetnames:
            ws = wb[sname]
            data['threads_imperial'] = extract_imperial_thread(ws)
            print(f"  → {len(data['threads_imperial'])} 种英制螺纹 (来自{sname})")
            break
    
    # 7. 深沟球轴承
    if '深沟球轴承查询 ' in wb.sheetnames:
        ws = wb['深沟球轴承查询 ']
        data['bearings_deep_groove'] = extract_bearing_data(ws, 'deep_groove')
        print(f"  → {len(data['bearings_deep_groove'])} 种深沟球轴承")
    
    # 8. 推力球轴承
    if '推力球轴承尺寸表' in wb.sheetnames:
        ws = wb['推力球轴承尺寸表']
        data['bearings_thrust'] = extract_bearing_data(ws, 'thrust')
        print(f"  → {len(data['bearings_thrust'])} 种推力球轴承")
    
    # 9. O型圈数据
    oring_data = extract_oring_data()
    if oring_data:
        data['oring_groove'] = oring_data
        print(f"  → {len(oring_data)} 种O型圈规格")
    
    # 写入JSON
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'extracted_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n数据已导出到: {output_path}")
    print(f"文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == '__main__':
    main()
