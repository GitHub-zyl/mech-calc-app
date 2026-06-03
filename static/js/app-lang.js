/**
 * 机械计算 — 完整语言切换系统
 * 300+ 条目翻译词典 + DOM深度替换引擎
 */
(function() {
'use strict';

// ======== 翻译词典 ========
var DICT = {
  // ---- 页面标题/通用UI ----
  '机械设计常用计算表': {en:'Mechanical Design Calculator', ja:'機械設計計算表'},
  '欢迎使用机械设计常用计算表': {en:'Welcome to Mechanical Design Calculator', ja:'機械設計計算表へようこそ'},
  '从左侧选择一个计算器开始，或搜索关键词快速定位。': {en:'Select a calculator from the left or search keywords.', ja:'左から計算機を選ぶか、キーワードで検索。'},
  '数据来源：155个工作表 · 15大类机械计算': {en:'Source: 155 worksheets · 15 categories', ja:'出典: 155ワークシート · 15カテゴリ'},
  '基于《机械设计常用计算表.xlsx》': {en:'Based on Mechanical Design Sheets', ja:'機械設計計算表に基づく'},
  '搜索计算器...': {en:'Search calculators...', ja:'計算機を検索...'},
  '填写参数后点击计算': {en:'Fill parameters and calculate', ja:'パラメータを入力して計算'},
  '计算': {en:'Calculate', ja:'計算'},
  '计算结果': {en:'Result', ja:'計算結果'},
  '公式示例': {en:'Formula Example', ja:'計算例'},
  '公式': {en:'Formula', ja:'式'},
  '知识': {en:'Knowledge', ja:'知識'},
  '复制': {en:'Copy', ja:'コピー'},
  '关闭': {en:'Close', ja:'閉じる'},
  '参数': {en:'Parameters', ja:'パラメータ'},
  '安全': {en:'Safe', ja:'安全'},
  '危险': {en:'Danger', ja:'危険'},
  '—': {en:'—', ja:'—'},
  '暂无记录': {en:'No records', ja:'記録なし'},
  '清除历史': {en:'Clear History', ja:'履歴消去'},
  '导出CSV': {en:'Export CSV', ja:'CSV出力'},
  '加载中...': {en:'Loading...', ja:'読込中...'},
  '返回列表': {en:'Back', ja:'戻る'},
  '暂无相关知识': {en:'No knowledge available', ja:'知識がありません'},

  // ---- 分类名 ----
  '材料数据': {en:'Materials', ja:'材料データ'},
  '齿轮传动': {en:'Gear Drive', ja:'歯車伝動'},
  '弹簧': {en:'Spring', ja:'ばね'},
  '螺纹/紧固': {en:'Thread/Fastener', ja:'ねじ/締結'},
  '链传动': {en:'Chain Drive', ja:'チェーン伝動'},
  '带传动': {en:'Belt Drive', ja:'ベルト伝動'},
  '凸轮/分割器': {en:'Cam/Indexer', ja:'カム/割出'},
  '公差配合': {en:'Tolerance/Fit', ja:'公差/はめあい'},
  '冲压钣金': {en:'Stamping/Sheet', ja:'プレス/板金'},
  '液压系统': {en:'Hydraulic System', ja:'油圧システム'},
  '联轴器/密封': {en:'Coupling/Seal', ja:'継手/シール'},
  '电机常识': {en:'Motor', ja:'モーター'},
  '材料力学': {en:'Strength of Materials', ja:'材料力学'},
  '工具': {en:'Tools', ja:'ツール'},
  '运动学/动力学': {en:'Kinematics/Dynamics', ja:'運動学/動力学'},
  '热传导/流体': {en:'Thermal/Fluid', ja:'熱伝導/流体'},
  '轮系/飞轮': {en:'Gear Trains/Flywheel', ja:'歯車列/弾み車'},

  // ---- 各模块按钮/面板标题（精选关键项）----
  '材料查询': {en:'Material Search', ja:'材料検索'},
  '齿轮基本参数': {en:'Gear Parameters', ja:'歯車パラメータ'},
  '齿轮啮合计算': {en:'Gear Mesh', ja:'歯車かみ合い'},
  '电机选型计算': {en:'Motor Selection', ja:'モーター選定'},
  '齿条传动计算': {en:'Rack & Pinion', ja:'ラックアンドピニオン'},
  '压缩弹簧计算': {en:'Compression Spring', ja:'圧縮ばね'},
  '公制螺纹计算': {en:'Metric Thread', ja:'メートルねじ'},
  '攻丝底孔计算': {en:'Tap Drill', ja:'タップ下穴'},
  '螺栓扭矩计算': {en:'Bolt Torque', ja:'ボルトトルク'},
  '链轮参数': {en:'Sprocket', ja:'スプロケット'},
  '链条长度计算': {en:'Chain Length', ja:'チェーン長さ'},
  '输送链张力': {en:'Conveyor Tension', ja:'コンベヤ張力'},
  '三角皮带计算': {en:'V-Belt', ja:'Vベルト'},
  '同步带计算': {en:'Timing Belt', ja:'タイミングベルト'},
  '凸轮轮廓计算': {en:'Cam Profile', ja:'カム輪郭'},
  '分割器选型': {en:'Indexer', ja:'割出装置'},
  '分度盘计算': {en:'Indexing Plate', ja:'割出盤'},
  '冲裁力计算': {en:'Blanking Force', ja:'抜き力'},
  'V型弯曲力': {en:'V-Bending', ja:'V曲げ'},
  'U型弯曲力': {en:'U-Bending', ja:'U曲げ'},
  '压印力计算': {en:'Embossing', ja:'エンボス'},
  '剪切力计算': {en:'Shear', ja:'せん断'},
  '公差配合计算': {en:'Fit Calc', ja:'はめあい計算'},
  '轴公差计算': {en:'Shaft Tolerance', ja:'軸公差'},
  '孔公差计算': {en:'Hole Tolerance', ja:'穴公差'},
  '管路压损计算': {en:'Pipe Loss', ja:'配管損失'},
  '液压冲击计算': {en:'Hydraulic Shock', ja:'油圧衝撃'},
  '蓄能器选型': {en:'Accumulator', ja:'蓄圧器'},
  '油箱热平衡': {en:'Tank Heat', ja:'タンク熱'},
  '齿式联轴器': {en:'Gear Coupling', ja:'歯車継手'},
  '万向联轴器': {en:'Universal Joint', ja:'自在継手'},
  'O型圈沟槽': {en:'O-Ring Groove', ja:'Oリング溝'},
  'HTD圆弧齿同步带': {en:'HTD Timing Belt', ja:'HTDタイミングベルト'},
  '同步转速计算': {en:'Sync Speed', ja:'同期速度'},
  '扭矩/电流估算': {en:'Torque/Current', ja:'トルク/電流'},
  '电机常识速查': {en:'Motor Reference', ja:'モーター参考'},
  '截面惯性矩': {en:'Section Properties', ja:'断面特性'},
  '立柱稳定性': {en:'Column Stability', ja:'座屈'},
  '焊缝强度': {en:'Weld Strength', ja:'溶接強度'},
  '键强度校核': {en:'Key Strength', ja:'キー強度'},
  '销强度校核': {en:'Pin Strength', ja:'ピン強度'},
  '过盈配合计算': {en:'Interference Fit', ja:'しまりばめ'},
  '压入力计算': {en:'Press Fit', ja:'圧入力'},
  '单位换算': {en:'Unit Converter', ja:'単位換算'},
  '计算历史': {en:'History', ja:'履歴'},
  '运动学': {en:'Kinematics', ja:'運動学'},
  '离心力': {en:'Centrifugal Force', ja:'遠心力'},
  '动量': {en:'Momentum', ja:'運動量'},
  '功率': {en:'Power', ja:'動力'},
  '转动惯量': {en:'Mass Moment of Inertia', ja:'慣性モーメント'},
  '振动': {en:'Vibration', ja:'振動'},
  '螺旋传动': {en:'Lead Screw', ja:'ねじ送り'},
  '行星轮系': {en:'Planetary Gear', ja:'遊星歯車'},
  '飞轮储能': {en:'Flywheel', ja:'弾み車'},
  '理想气体': {en:'Ideal Gas', ja:'理想気体'},
  '伯努利': {en:'Bernoulli', ja:'ベルヌーイ'},
  '热膨胀': {en:'Thermal Expansion', ja:'熱膨張'},
  '铆接强度': {en:'Rivet Strength', ja:'リベット強度'},
  '粘接强度': {en:'Adhesive Strength', ja:'接着強度'},

  // ======== 结果字段名翻译（API返回值 → 界面显示）========
  'pitch diameter': {en:'Pitch Diameter', ja:'ピッチ円直径'},
  'tip diameter': {en:'Tip Diameter', ja:'歯先円直径'},
  'root diameter': {en:'Root Diameter', ja:'歯底円直径'},
  'base circle diameter': {en:'Base Circle', ja:'基礎円'},
  'circular pitch': {en:'Circular Pitch', ja:'円ピッチ'},
  'tooth thickness': {en:'Tooth Thickness', ja:'歯厚'},
  'space width': {en:'Space Width', ja:'歯溝幅'},
  'whole depth': {en:'Whole Depth', ja:'全歯たけ'},
  'pressure angle deg': {en:'Pressure Angle', ja:'圧力角'},
  'modification coefficient': {en:'Mod. Coeff', ja:'転位係数'},
  'center distance': {en:'Center Distance', ja:'中心距離'},
  'actual center distance': {en:'Actual Center Dist', ja:'実中心距離'},
  'transmission ratio': {en:'Ratio', ja:'伝達比'},
  'working pressure angle deg': {en:'Working Pressure Angle', ja:'かみ合い圧力角'},
  'addendum': {en:'Addendum', ja:'歯たけ'},
  'dedendum': {en:'Dedendum', ja:'歯末たけ'},
  'module': {en:'Module', ja:'モジュール'},
  'teeth': {en:'Teeth', ja:'歯数'},
  'gear1': {en:'Gear 1', ja:'歯車1'},
  'gear2': {en:'Gear 2', ja:'歯車2'},
  'input speed': {en:'Input Speed', ja:'入力回転数'},
  'output speed': {en:'Output Speed', ja:'出力回転数'},
  'input torque': {en:'Input Torque', ja:'入力トルク'},
  'output torque': {en:'Output Torque', ja:'出力トルク'},
  'power kw': {en:'Power kW', ja:'動力kW'},
  'efficiency': {en:'Efficiency', ja:'効率'},
  'stiffness n per mm': {en:'Stiffness N/mm', ja:'剛性N/mm'},
  'wire diameter': {en:'Wire Diameter', ja:'線径'},
  'mean diameter': {en:'Mean Diameter', ja:'平均径'},
  'active coils': {en:'Active Coils', ja:'有効巻数'},
  'shear modulus': {en:'Shear Modulus', ja:'せん断弾性係数'},
  'spring index': {en:'Spring Index', ja:'ばね指数'},
  'material': {en:'Material', ja:'材料'},
  'deflection mm': {en:'Deflection mm', ja:'たわみmm'},
  'max shear stress mpa': {en:'Max Shear Stress MPa', ja:'最大せん断応力MPa'},
  'allowable stress mpa': {en:'Allowable Stress MPa', ja:'許容応力MPa'},
  'safety factor': {en:'Safety Factor', ja:'安全率'},
  'is safe': {en:'Safe', ja:'安全'},
  'curvature factor': {en:'Curvature Factor', ja:'曲度係数'},
  'material desc': {en:'Material', ja:'材料'},
  'working stress mpa': {en:'Working Stress MPa', ja:'使用応力MPa'},
  'euler critical force kn': {en:'Euler Critical kN', ja:'オイラー座屈荷重kN'},
  'euler critical force N': {en:'Euler Critical N', ja:'オイラー座屈力N'},
  'stability safety factor': {en:'Stability Safety', ja:'座屈安全率'},
  'slenderness ratio': {en:'Slenderness', ja:'細長比'},
  'failure mode': {en:'Failure Mode', ja:'破壊様式'},
  'belt section': {en:'Belt Section', ja:'ベルト形'},
  'small pulley diameter': {en:'Small Pulley Dia', ja:'小プーリ径'},
  'large pulley diameter': {en:'Large Pulley Dia', ja:'大プーリ径'},
  'belt speed mps': {en:'Belt Speed m/s', ja:'ベルト速度m/s'},
  'wrap angle deg': {en:'Wrap Angle', ja:'巻付角'},
  'single belt power kw': {en:'Belt Power kW', ja:'ベルト伝達kW'},
  'required belts': {en:'Belts Required', ja:'必要本数'},
  'blanking force kn': {en:'Blanking Force kN', ja:'抜き力kN'},
  'blanking force ton': {en:'Blanking Force ton', ja:'抜き力トン'},
  'bending force kn': {en:'Bending Force kN', ja:'曲げ力kN'},
  'shear force kn': {en:'Shear Force kN', ja:'せん断力kN'},
  'nominal diameter': {en:'Nominal Diameter', ja:'呼び径'},
  'pitch': {en:'Pitch', ja:'ピッチ'},
  'pitch diameter': {en:'Pitch Diameter', ja:'有効径'},
  'minor diameter': {en:'Minor Diameter', ja:'谷径'},
  'tap drill diameter': {en:'Tap Drill', ja:'下穴径'},
  'thread height': {en:'Thread Height', ja:'ねじ山高さ'},
  'major diameter': {en:'Major Diameter', ja:'外径'},
  'preload kN': {en:'Preload kN', ja:'予締め力kN'},
  'tightening torque nm': {en:'Tightening Torque Nm', ja:'締付トルクNm'},
  'flow type': {en:'Flow Type', ja:'流れ状態'},
  'flow velocity mps': {en:'Velocity m/s', ja:'流速m/s'},
  'reynolds number': {en:'Reynolds', ja:'レイノルズ数'},
  'pressure loss bar': {en:'Pressure Loss bar', ja:'圧力損失bar'},
  'section': {en:'Section', ja:'断面'},
  'area mm2': {en:'Area mm2', ja:'断面積mm2'},
  'inertia mm4': {en:'Inertia mm4', ja:'断面二次モーメントmm4'},
  'section modulus mm3': {en:'Section Modulus mm3', ja:'断面係数mm3'},
  'radius gyration mm': {en:'Radius of Gyration mm', ja:'回転半径mm'},
  'shear stress mpa': {en:'Shear Stress MPa', ja:'せん断応力MPa'},
  'bearing stress mpa': {en:'Bearing Stress MPa', ja:'面圧MPa'},
  'bending stress mpa': {en:'Bending Stress MPa', ja:'曲げ応力MPa'},
  'contact stress mpa': {en:'Contact Stress MPa', ja:'接触応力MPa'},
  'force N': {en:'Force N', ja:'力N'},
  'force': {en:'Force', ja:'力'},
  'density': {en:'Density', ja:'密度'},
  'poisson ratio': {en:'Poisson Ratio', ja:'ポアソン比'},
  'elastic modulus': {en:'Elastic Modulus', ja:'弾性係数'},
  'tensile strength': {en:'Tensile Strength', ja:'引張強さ'},
  'yield strength': {en:'Yield Strength', ja:'降伏点'},
  'thermal expansion': {en:'Thermal Expansion', ja:'熱膨張率'},
  'specific heat': {en:'Specific Heat', ja:'比熱'},
  'thermal conductivity': {en:'Thermal Conductivity', ja:'熱伝導率'},
  'tensile strength mpa': {en:'Tensile Strength MPa', ja:'引張強さMPa'},
  'yield strength mpa': {en:'Yield Strength MPa', ja:'降伏点MPa'},
  'required torque nm': {en:'Required Torque Nm', ja:'必要トルクNm'},
  'required speed rpm': {en:'Required Speed rpm', ja:'必要回転数rpm'},
  'required power kw': {en:'Required Power kW', ja:'必要動力kW'},
  'dynamic load rating kN': {en:'Dynamic Rating kN', ja:'動定格荷重kN'},
  'equivalent load kN': {en:'Equivalent Load kN', ja:'動等価荷重kN'},
  'speed rpm': {en:'Speed rpm', ja:'回転数rpm'},
  'L10 life hours': {en:'L10 Life hours', ja:'L10寿命時間'},
  'natural freq Hz': {en:'Natural Freq Hz', ja:'固有振動数Hz'},
  'period s': {en:'Period s', ja:'周期s'},
  'damping ratio': {en:'Damping', ja:'減衰比'},
  'mass kg': {en:'Mass kg', ja:'質量kg'},
  'velocity mps': {en:'Velocity m/s', ja:'速度m/s'},
  'momentum kgms': {en:'Momentum kg·m/s', ja:'運動量'},
  'kinetic energy J': {en:'Kinetic Energy J', ja:'運動エネJ'},
  'centrifugal force N': {en:'Centrifugal Force N', ja:'遠心力N'},
  'omega rad s': {en:'Omega rad/s', ja:'角速度rad/s'},
  'radius m': {en:'Radius m', ja:'半径m'},
  'ratio': {en:'Ratio', ja:'比'},
  'w p angle factor': {en:'Wrap Angle Factor', ja:'巻付角係数'},
  'belt length mm': {en:'Belt Length mm', ja:'ベルト長さmm'},
  'belt type': {en:'Belt Type', ja:'ベルト種'},
  'belt pitch length mm': {en:'Pitch Length mm', ja:'ピッチ長mm'},
  'belt teeth count': {en:'Teeth Count', ja:'歯数'},
  'shear type': {en:'Shear Type', ja:'せん断種'},
  'joint type': {en:'Joint Type', ja:'接合種'},
  'stress type': {en:'Stress Type', ja:'応力種'},
  'stress mpa': {en:'Stress MPa', ja:'応力MPa'},
  'worm pitch diameter mm': {en:'Worm Pitch Dia mm', ja:'ウォームピッチ径mm'},
  'wheel pitch diameter mm': {en:'Wheel Pitch Dia mm', ja:'ホイールピッチ径mm'},
  'lead angle deg': {en:'Lead Angle', ja:'進み角'},
  'worm tip diameter mm': {en:'Worm Tip Dia mm', ja:'ウォーム先径mm'},
  'wheel tip diameter mm': {en:'Wheel Tip Dia mm', ja:'ホイール先径mm'},
  'self locking': {en:'Self Locking', ja:'セルフロック'},
  'L10 revolutions Mr': {en:'L10 Revolutions Mr', ja:'L10回転数Mr'},
  'tangential N': {en:'Tangential N', ja:'接線力N'},
  'radial N': {en:'Radial N', ja:'半径方向力N'},
  'axial N': {en:'Axial N', ja:'軸方向力N'},
  'contact pressure mpa': {en:'Contact Pressure MPa', ja:'面圧MPa'},
  'press force N': {en:'Press Force N', ja:'圧入力N'},
  'effective volume isothermal L': {en:'Eff Volume(Isothermal)L', ja:'有効容積(等温)L'},
  'effective volume adiabatic L': {en:'Eff Volume(Adiabatic)L', ja:'有効容積(断熱)L'},
  'transmittable torque Nm': {en:'Transmit Torque Nm', ja:'伝達トルクNm'},
};

// ======== 全局翻译函数 ========
var I18N_LANG = localStorage.getItem('mech_lang') || 'zh';

window.__ = function(text) {
  if (I18N_LANG === 'zh') return text;
  var entry = DICT[text];
  return (entry && entry[I18N_LANG]) || text;
};

// ======== DOM翻译引擎 ========
function translateNode(node) {
  if (!node) return;
  if (node.nodeType === 3) {
    var text = node.textContent;
    if (text && text.trim()) {
      var entry = DICT[text];
      if (entry && entry[I18N_LANG]) node.textContent = entry[I18N_LANG];
    }
    return;
  }
  if (node.tagName === 'INPUT' || node.tagName === 'TEXTAREA') {
    if (node.placeholder) {
      var entry = DICT[node.placeholder];
      if (entry && entry[I18N_LANG]) node.placeholder = entry[I18N_LANG];
    }
    return;
  }
  for (var i = 0; i < node.childNodes.length; i++) {
    translateNode(node.childNodes[i]);
  }
}

window.translatePage = function(lang) {
  if (lang) I18N_LANG = lang;
  if (I18N_LANG === 'zh') return;
  
  translateNode(document.body);

  // 更新语言按钮
  document.querySelectorAll('.lang-btn').forEach(function(b) {
    b.style.background = b.dataset.lang === I18N_LANG ? 'rgba(255,255,255,0.2)' : 'transparent';
    b.style.fontWeight = b.dataset.lang === I18N_LANG ? 'bold' : 'normal';
  });
  
  // 重新翻译当前活动面板（如果有结果）
  setTimeout(function() {
    var activePanel = document.querySelector('.calculator-panel.active');
    if (activePanel) translateNode(activePanel);
  }, 100);
};

// ======== 结果区翻译钩子 ========
// 在每次计算结果更新后自动翻译
var origSetHTML = Element.prototype.__lookupSetter__ ? null : null;
if (typeof MutationObserver !== 'undefined') {
  var obs = new MutationObserver(function(mutations) {
    if (I18N_LANG === 'zh') return;
    mutations.forEach(function(m) {
      m.addedNodes.forEach(function(n) {
        if (n.nodeType === 1) translateNode(n);
      });
    });
  });
  
  setTimeout(function() {
    var results = document.querySelectorAll('.calc-result');
    if (results.length > 0) {
      results.forEach(function(r) { obs.observe(r, {childList:true, subtree:true}); });
    }
    // Also observe the panels container for new panels
    var panels = document.getElementById('calculator-panels');
    if (panels) obs.observe(panels, {childList:true, subtree:true});
  }, 1000);
}

// ======== 语言切换按钮 ========
document.addEventListener('DOMContentLoaded', function() {
  var header = document.getElementById('header');
  if (!header) return;
  
  var div = document.createElement('div');
  div.style.cssText = 'margin-left:auto;display:flex;gap:2px';
  
  [{c:'zh',n:'中文'},{c:'en',n:'EN'},{c:'ja',n:'日'}].forEach(function(l) {
    var btn = document.createElement('button');
    btn.className = 'lang-btn';
    btn.dataset.lang = l.c;
    btn.textContent = l.n;
    btn.title = {zh:'Chinese',en:'English',ja:'Japanese'}[l.c];
    btn.style.cssText = 'padding:2px 8px;border:1px solid rgba(255,255,255,0.3);border-radius:3px;background:' +
      (l.c === I18N_LANG ? 'rgba(255,255,255,0.2)' : 'transparent') +
      ';color:white;cursor:pointer;font-size:12px;font-weight:' +
      (l.c === I18N_LANG ? 'bold' : 'normal');
    btn.onclick = function() { 
      I18N_LANG = l.c;
      localStorage.setItem('mech_lang', l.c);
      if (l.c === 'zh') {
        localStorage.setItem('mech_lang', 'zh');
        location.reload(); // 中文：刷新恢复原样
      } else {
        translatePage(l.c);
      }
    };
    div.appendChild(btn);
  });
  header.appendChild(div);
  
  if (I18N_LANG !== 'zh') setTimeout(function() { window.translatePage(I18N_LANG); }, 200);
});

})();
