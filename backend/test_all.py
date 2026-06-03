"""
机械设计常用计算表 — 全量自动化测试
测试所有API的典型用例 + 边界用例，输出测试报告
"""
import sys, os, json, math, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

BASE = 'http://127.0.0.1:9090'

results = {'pass': 0, 'fail': 0, 'errors': []}

def api_post(url, data):
    d = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=d, headers={'Content-Type': 'application/json'})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception as e:
        return {'error': str(e)}

def api_get(url, is_json=True):
    try:
        data = urllib.request.urlopen(url, timeout=10).read()
        if is_json:
            return json.loads(data)
        return {'ok': True, 'size': len(data)}
    except Exception as e:
        return {'error': str(e) if is_json else f'failed: {e}'}

def test_file(name, url):
    try:
        r = urllib.request.urlopen(url, timeout=10)
        if r.status == 200:
            results['pass'] += 1
            print(f'  ✅ {name} ({len(r.read())} bytes)')
        else:
            results['fail'] += 1
            results['errors'].append(f'❌ {name}: HTTP {r.status}')
            print(f'  ❌ {name}: HTTP {r.status}')
    except Exception as e:
        results['fail'] += 1
        results['errors'].append(f'❌ {name}: {e}')
        print(f'  ❌ {name}: {e}')

def test(name, fn):
    try:
        result = fn()
        if isinstance(result, dict) and 'error' in result:
            results['fail'] += 1
            results['errors'].append(f'❌ {name}: {result["error"]}')
            print(f'  ❌ {name}')
        else:
            results['pass'] += 1
            print(f'  ✅ {name}')
    except Exception as e:
        results['fail'] += 1
        results['errors'].append(f'❌ {name}: {e}')
        print(f'  ❌ {name}: {e}')

print('=' * 60)
print('机械设计常用计算表 — 全量自动化测试')
print('=' * 60)

# 1. 首页/静态文件
print('\n📄 1. 页面加载')
test_file('首页', BASE + '/')
test_file('app.js', BASE + '/static/js/app.js')
test_file('app-ext.js', BASE + '/static/js/app-ext.js')
test_file('app-ext2.js', BASE + '/static/js/app-ext2.js')
test_file('style.css', BASE + '/static/css/style.css')

# 2. 齿轮
print('\n⚙ 2. 齿轮传动')
test('齿轮基本参数 (m=3,z=20)', lambda: api_post(BASE + '/api/calculate/gear/spur', {'module':3,'teeth':20}))
test('齿轮变位 (m=3,z=20,x=0.3)', lambda: api_post(BASE + '/api/calculate/gear/spur', {'module':3,'teeth':20,'modification_coefficient':0.3}))
test('齿轮啮合 (m=3,z1=20,z2=60)', lambda: api_post(BASE + '/api/calculate/gear/mesh', {'module':3,'teeth1':20,'teeth2':60}))
test('电机选型 (2.2kW,1450rpm,i=5)', lambda: api_post(BASE + '/api/calculate/gear/motor', {'power':2.2,'speed':1450,'ratio':5}))
test('齿轮齿条 (m=3,z=20,F=500N)', lambda: api_post(BASE + '/api/calculate/gear/rack', {'module':3,'teeth':20,'force':500,'speed':0.5}))

# 3. 弹簧
print('\n〰️ 3. 弹簧')
test('压缩弹簧 (d=4,Dm=30,n=10)', lambda: api_post(BASE + '/api/calculate/spring/compression', {'wire_diameter':4,'mean_diameter':30,'coils':10}))
test('弹簧应力校核 (F=500N)', lambda: api_post(BASE + '/api/calculate/spring/compression', {'wire_diameter':4,'mean_diameter':30,'coils':10,'force':500}))

# 4. 螺纹
print('\n🔩 4. 螺纹/紧固')
test('公制螺纹 M12×1.75', lambda: api_post(BASE + '/api/calculate/thread/metric', {'nominal_diameter':12,'pitch':1.75}))
test('公制螺纹 M24 (自动螺距)', lambda: api_post(BASE + '/api/calculate/thread/metric', {'nominal_diameter':24}))
test('攻丝底孔 M6', lambda: api_post(BASE + '/api/calculate/thread/tapdrill', {'thread_spec':'M6'}))
test('攻丝底孔 M8×1.25', lambda: api_post(BASE + '/api/calculate/thread/tapdrill', {'thread_spec':'M8x1.25'}))
test('螺栓扭矩 M12-8.8级', lambda: api_post(BASE + '/api/calculate/thread/bolt', {'diameter':12,'grade':'8.8'}))
test('螺栓扭矩 M20-10.9级', lambda: api_post(BASE + '/api/calculate/thread/bolt', {'diameter':20,'grade':'10.9'}))

# 5. 链传动
print('\n⛓ 5. 链传动')
test('链轮参数 (p=12.7,z=17)', lambda: api_post(BASE + '/api/calculate/chain/sprocket', {'pitch':12.7,'teeth':17}))
test('链条长度 (z1=17,z2=34,a=500)', lambda: api_post(BASE + '/api/calculate/chain/length', {'pitch':12.7,'teeth1':17,'teeth2':34,'center_distance':500}))
test('输送链张力 (100kg,0.5m/s)', lambda: api_post(BASE + '/api/calculate/chain/conveyor', {'mass':100,'speed':0.5,'length':5}))

# 6. 带传动
print('\n🔗 6. 带传动')
test('三角皮带 A型', lambda: api_post(BASE + '/api/calculate/belt/vbelt', {'section':'A','power':3,'speed':1440,'ratio':2.5,'center_distance':400}))
test('三角皮带 SPA型 大功率', lambda: api_post(BASE + '/api/calculate/belt/vbelt', {'section':'SPA','power':15,'speed':1450,'ratio':3,'center_distance':800}))
test('同步带 L型', lambda: api_post(BASE + '/api/calculate/belt/synchronous', {'belt_type':'L','power':0.75,'speed':1000,'ratio':2}))
test('同步带 H型', lambda: api_post(BASE + '/api/calculate/belt/synchronous', {'belt_type':'H','power':3,'speed':800,'ratio':3}))

# 7. 凸轮/分割器
print('\n🥏 7. 凸轮/分割器')
test('凸轮轮廓 (正弦)', lambda: api_post(BASE + '/api/calculate/cam/profile', {'base_radius':50,'stroke':30,'angle':120,'motion_type':'sine','points':36}))
test('凸轮轮廓 (余弦)', lambda: api_post(BASE + '/api/calculate/cam/profile', {'base_radius':50,'stroke':30,'angle':120,'motion_type':'cosine','points':36}))
test('凸轮分析', lambda: api_post(BASE + '/api/calculate/cam/analysis', {'angle':120,'stroke':30,'motion_type':'sine'}))
test('分割器选型', lambda: api_post(BASE + '/api/calculate/cam/indexer', {'load_torque':50,'index_angle':120,'dwell_angle':240,'rpm':60,'stations':4}))
test('分度盘计算', lambda: api_post(BASE + '/api/calculate/cam/divider', {'pitch_angle':90,'table_diameter':600,'mass':50,'rpm':30}))

# 8. 冲压
print('\n✂️ 8. 冲压钣金')
test('冲裁力 (L=200,t=2,τ=350)', lambda: api_post(BASE + '/api/calculate/press/blanking', {'perimeter':200,'thickness':2,'shear_strength':350}))
test('V型弯曲 (b=100,t=1.5,σb=400)', lambda: api_post(BASE + '/api/calculate/press/vbend', {'width':100,'thickness':1.5,'tensile_strength':400,'die_opening':12}))
test('U型弯曲', lambda: api_post(BASE + '/api/calculate/press/ubend', {'width':100,'thickness':1.5,'tensile_strength':400,'die_opening':12}))
test('压印力 (A=500mm²,σb=400)', lambda: api_post(BASE + '/api/calculate/press/embossing', {'area':500,'tensile_strength':400}))
test('剪切力 (A=1000mm²,τ=300)', lambda: api_post(BASE + '/api/calculate/press/shear', {'area':1000,'shear_strength':300}))

# 9. 公差配合
print('\n📐 9. 公差配合')
test('轴公差 φ50h7', lambda: api_post(BASE + '/api/calculate/tolerance/shaft', {'nominal':50,'spec':'h7'}))
test('孔公差 φ50H7', lambda: api_post(BASE + '/api/calculate/tolerance/hole', {'nominal':50,'spec':'H7'}))
test('配合 H7/g6 @ φ50', lambda: api_post(BASE + '/api/calculate/tolerance/fit', {'nominal':50,'hole_spec':'H7','shaft_spec':'g6'}))
test('配合 H7/s6 @ φ50 (过盈)', lambda: api_post(BASE + '/api/calculate/tolerance/fit', {'nominal':50,'hole_spec':'H7','shaft_spec':'s6'}))
test('推荐配合列表', lambda: api_get(BASE + '/api/data/fit_recommendations'))

# 10. 液压系统
print('\n💧 10. 液压')
test('管路压损 (Q=70,d=15,L=2)', lambda: api_post(BASE + '/api/calculate/hydraulic/pipe', {'flow':70,'diameter':15,'length':2}))
test('薄壁小孔流量', lambda: api_post(BASE + '/api/calculate/hydraulic/orifice', {'diameter':5,'pressure_diff':3}))
test('蓄能器选型 (40L,100/120/200bar)', lambda: api_post(BASE + '/api/calculate/hydraulic/accumulator', {'volume':40,'precharge_pressure':100,'min_pressure':120,'max_pressure':200}))
test('液压冲击 (v=4→0, L=10)', lambda: api_post(BASE + '/api/calculate/hydraulic/shock', {'v1':4,'v2':0,'pipe_length':10}))
test('油箱热平衡 (5kW,200L)', lambda: api_post(BASE + '/api/calculate/hydraulic/tank', {'power':5,'volume':200}))
test('油液粘度-温度', lambda: api_post(BASE + '/api/calculate/hydraulic/viscosity', {'nu_40':46,'temperature':60}))

# 11. 联轴器/O型圈
print('\n🔧 11. 联轴器/密封')
test('齿式联轴器 (15kW,1450rpm)', lambda: api_post(BASE + '/api/calculate/coupling/gear', {'power':15,'speed':1450}))
test('万向联轴器 (5kW,500rpm,15°)', lambda: api_post(BASE + '/api/calculate/coupling/universal', {'power':5,'speed':500,'angle':15}))
test('O型圈 (d=3.5mm)', lambda: api_post(BASE + '/api/calculate/coupling/oring', {'section_diameter':3.5}))
test('HTD同步带 (8M,2.2kW)', lambda: api_post(BASE + '/api/calculate/coupling/htd', {'belt_type':'8M','power':2.2,'speed':1000,'ratio':2.5}))

# 12. 电机常识
print('\n⚡ 12. 电机')
test('同步转速 (4极,50Hz)', lambda: api_post(BASE + '/api/calculate/motor/speed', {'poles':4,'freq':50}))
test('电机扭矩 (5.5kW,4极)', lambda: api_post(BASE + '/api/calculate/motor/torque', {'power':5.5,'poles':4}))
test('电机电流 (11kW,380V)', lambda: api_post(BASE + '/api/calculate/motor/current', {'power':11,'voltage':380}))
test('电机知识速查', lambda: api_get(BASE + '/api/data/motor_knowledge'))

# 13. 材料力学
print('\n📐 13. 材料力学')
test('截面惯性矩 (矩形50×100)', lambda: api_post(BASE + '/api/calculate/strength/section', {'shape':'rect','params':{'b':50,'h':100}}))
test('截面惯性矩 (圆φ50)', lambda: api_post(BASE + '/api/calculate/strength/section', {'shape':'circle','params':{'d':50}}))
test('截面惯性矩 (空心管)', lambda: api_post(BASE + '/api/calculate/strength/section', {'shape':'tube','params':{'D':50,'d':40}}))
test('立柱稳定 (F=50kN,L=2m)', lambda: api_post(BASE + '/api/calculate/strength/column', {'force':50000,'area':3000,'elastic_modulus':206000,'length':2000,'inertia':5000000}))
test('焊缝强度 (F=30kN,K=6)', lambda: api_post(BASE + '/api/calculate/strength/weld', {'force':30000,'leg':6,'length':100,'num':2}))
test('键强度 (T=500N·m,d=40)', lambda: api_post(BASE + '/api/calculate/strength/key', {'torque':500,'shaft_diameter':40,'width':12,'height':8,'length':40}))
test('销强度 (F=10kN,d=10)', lambda: api_post(BASE + '/api/calculate/strength/pin', {'force':10000,'diameter':10}))
test('过盈配合 (d=50,δ=30μm)', lambda: api_post(BASE + '/api/calculate/strength/interference', {'shaft_diameter':50,'interference':30,'hub_od':100,'length':60}))
test('压入力 (d=50,δ=30μm,L=60)', lambda: api_post(BASE + '/api/calculate/strength/pressfit', {'shaft_diameter':50,'interference':30,'hub_od':100,'length':60}))

# 14. 材料数据
print('\n📦 14. 数据查询')
test('材料搜索 (45钢)', lambda: api_get(BASE + '/api/material/search?q=45'))
test('材料搜索 (HT200)', lambda: api_get(BASE + '/api/material/search?q=HT200'))
test('材料详情 (45钢)', lambda: api_get(BASE + '/api/material/info?name=45'))
test('钢材牌号对照', lambda: api_get(BASE + '/api/data/steels'))
test('铝材牌号对照', lambda: api_get(BASE + '/api/data/aluminum'))
test('塑料数据', lambda: api_get(BASE + '/api/data/plastics'))
test('轴承数据', lambda: api_get(BASE + '/api/data/bearings'))

# 报告
print('\n' + '=' * 60)
print(f'📊 测试报告')
print(f'   通过: {results["pass"]}')
print(f'   失败: {results["fail"]}')
print(f'   总计: {results["pass"] + results["fail"]}')
if results['errors']:
    print(f'\n详细错误:')
    for e in results['errors']:
        print(f'  {e}')
print('=' * 60)
print(f'结果: {"✅ 全部通过!" if results["fail"] == 0 else "❌ 有失败项"}')
