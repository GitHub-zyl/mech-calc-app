/**
 * 机械计算 — 最终修复脚本
 * 解决: 翻译/公式示例/Wiki/面板点击无反应
 */
(function(){
'use strict';

// 1. 翻译字典 (小写 → 多语言)
var TRANS = {
  addendum:{ja:'歯たけ'}, dedendum:{ja:'歯末たけ'}, 'whole depth':{ja:'全歯たけ'},
  'circular pitch':{ja:'円ピッチ'}, 'tooth thickness':{ja:'歯厚'}, 'space width':{ja:'歯溝幅'},
  'pitch diameter':{ja:'ピッチ円直径'}, 'tip diameter':{ja:'歯先円直径'},
  'root diameter':{ja:'歯底円直径'}, 'base circle diameter':{ja:'基礎円'},
  module:{ja:'モジュール'}, teeth:{ja:'歯数'}, 'pressure angle deg':{ja:'圧力角'},
  'center distance':{ja:'中心距離'}, ratio:{ja:'比'},
  'input torque':{ja:'入力トルク'}, 'output torque':{ja:'出力トルク'},
  'input speed':{ja:'入力回転数'}, 'output speed':{ja:'出力回転数'},
  'power kw':{ja:'動力kW'}, efficiency:{ja:'効率'},
  'wire diameter':{ja:'線径'}, 'mean diameter':{ja:'平均径'},
  'active coils':{ja:'有効巻数'}, 'spring index':{ja:'ばね指数'},
  'stiffness n per mm':{ja:'剛性N/mm'}, 'shear modulus':{ja:'弾性係数'},
  material:{ja:'材料'}, 'deflection mm':{ja:'たわみmm'},
  'max shear stress mpa':{ja:'最大せん断応力MPa'},
  'allowable stress mpa':{ja:'許容応力MPa'},
  'safety factor':{ja:'安全率'}, 'is safe':{ja:'安全か'},
  'nominal diameter':{ja:'呼び径'}, pitch:{ja:'ピッチ'},
  'minor diameter':{ja:'谷径'}, 'thread height':{ja:'ねじ山高さ'},
  'tap drill diameter':{ja:'下穴径'},
  'belt section':{ja:'ベルト形'}, 'belt speed mps':{ja:'ベルト速度'},
  'wrap angle deg':{ja:'巻付角'}, 'single belt power kw':{ja:'単ベルトkW'},
  'required belts':{ja:'必要本数'},
  'blanking force kn':{ja:'抜き力kN'}, 'blanking force ton':{ja:'抜き力トン'},
  'bending force kn':{ja:'曲げ力kN'}, 'bending force ton':{ja:'曲げ力トン'},
  'shear force kn':{ja:'せん断力kN'},
  'flow type':{ja:'流れ状態'}, 'flow velocity mps':{ja:'流速'},
  'reynolds number':{ja:'レイノルズ数'}, 'pressure loss bar':{ja:'圧損bar'},
  'area mm2':{ja:'断面積mm2'}, 'inertia mm4':{ja:'慣性mm4'},
  'shear stress mpa':{ja:'せん断応力'}, 'bearing stress mpa':{ja:'面圧'},
  'bending stress mpa':{ja:'曲げ応力'}, 'contact stress mpa':{ja:'接触応力'},
  gear1:{ja:'歯車1'}, gear2:{ja:'歯車2'}, force:{ja:'力'},
  'working stress mpa':{ja:'使用応力'}, 'failure mode':{ja:'破壊様式'},
  'slenderness ratio':{ja:'細長比'},
  'lead angle deg':{ja:'進み角'}, 'self locking':{ja:'セルフロック'},
  'L10 life hours':{ja:'L10寿命'}, 'natural freq Hz':{ja:'固有振動数'},
  'kinetic energy J':{ja:'運動エネ'}, 'momentum kgms':{ja:'運動量'},
  'centrifugal force N':{ja:'遠心力'},
  'contact pressure mpa':{ja:'接触圧'}, 'press force N':{ja:'圧入力'},
  'transmission ratio':{ja:'伝達比'},
};

// 2. 公式示例
var EXAMPLES = {
  'gear-basic':{f:'d=mz=3x20=60mm, da=60+6=66mm, df=60-7.5=52.5mm',p:'m=3,z=20'},
  'gear-mesh':{f:'a=3(20+60)/2=120mm, i=60/20=3',p:'m=3,z1=20,z2=60'},
  'spring-compression':{f:'k=79000x4^4/(8x30^3x10)=9.36N/mm',p:'d=4,Dm=30,n=10'},
  'thread-metric':{f:'d2=12-0.6495x1.75=10.863mm',p:'M12x1.75'},
  'thread-tapdrill':{f:'D底=M6=5mm(钢), 4.95mm(不锈钢)',p:'M6'},
  'chain-sprocket':{f:'d=12.7/sin(pi/17)=69.116mm',p:'P=12.7,z=17'},
  'chain-length':{f:'Lp=104.43→106节',p:'z1=17,z2=34,a=500'},
  'press-blanking':{f:'F=1.3x200x2x350=182kN',p:'L=200,t=2,tau=350'},
  'press-vbend':{f:'F=1.33x100x1.5^2x400/12=9.98kN',p:'b=100,t=1.5'},
  'motor-speed':{f:'n=60x50/2=1500rpm(4极)',p:'4极,50Hz'},
  'motor-torque':{f:'T=9550x5.5/1455=36.1Nm',p:'5.5kW'},
  'tolerance-fit':{f:'50H7:ES=+25,EI=0; 50g6:es=-9,ei=-25',p:'50 H7/g6'},
  'strength-section':{f:'矩形I=50x100^3/12=4.17e6mm4',p:'50x100mm'},
  'strength-column':{f:'lambda=49,Pcr=pi^2x2.06e5x5e6/2000^2=2.54e6N',p:'L=2m,I=5e6'},
  'strength-weld':{f:'tau=30000/(0.707x6x100x2)=35.4MPa',p:'K=6,l=100,n=2'},
};

// ======== displayResult 补丁 ========
var ORIG = window.displayResult || function() {};
window.displayResult = function(panelId, data) {
  ORIG(panelId, data);

  var container = document.getElementById('result-' + panelId);
  if (!container) return;

  // 翻译结果表头
  var lang = (localStorage.getItem('mech_lang')||'zh');
  if (lang !== 'zh') {
    var rows = container.querySelectorAll('.result-table tr');
    rows.forEach(function(tr){
      var td = tr.children[0];
      if (!td) return;
      var key = td.textContent.trim().toLowerCase();
      if (TRANS[key] && TRANS[key][lang]) td.textContent = TRANS[key][lang];
    });
  }

  // 追加公式示例
  var ex = EXAMPLES[panelId];
  if (ex) {
    ex.innerHTML = '<div style="margin-top:8px;padding:10px;background:#f0fdf4;border-radius:6px;font-size:12px">' +
      '<strong>\ud83d\udca1 \u516c\u5f0f\u793a\u4f8b</strong><br>' +
      '<code>' + ex.f + '</code><br>' +
      '<span style="color:#888">\u53c2\u6570: ' + ex.p + '</span></div>';
    container.appendChild(typeof ex.innerHTML === 'string' ? 
      Object.assign(document.createElement('div'), {innerHTML: ex.innerHTML}) : 
      (function(){var d=document.createElement('div');d.innerHTML=ex.innerHTML;return d;})());
  }
};

// ======== showKnowledge ========
window.showKnowledge = function(topic) {
  var db = window.WIKI_KNOWLEDGE || {};
  var k = db[topic];
  if (!k) { alert(topic + ': no data'); return; }
  var o = document.createElement('div');
  o.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center';
  o.onclick = function(e){ if(e.target===o) o.remove(); };
  o.innerHTML = '<div style="background:white;border-radius:12px;padding:24px;max-width:500px;width:90%">' +
    '<h3 style="color:#2563eb">\ud83d\udcd6 ' + topic + '</h3>' +
    '<div style="background:#f0f9ff;padding:10px;border-radius:6px;margin:10px 0"><code>' +
    k.formula + '</code></div>' +
    '<p style="color:#555">' + k.desc + '</p>' +
    (k.note ? '<p style="color:#888;font-size:12px;padding:8px;background:#f8fafc">\ud83d\udca1 ' + k.note + '</p>' : '') +
    (k.url ? '<a href="' + k.url + '" target="_blank" style="color:#2563eb">\ud83d\udd17 \u767e\u5ea6\u767e\u79d1</a>' : '') +
    '<br><button onclick="this.parentElement.parentElement.remove()" style="margin-top:12px;padding:8px 24px;background:#2563eb;color:#fff;border:none;border-radius:4px;cursor:pointer">\u5173\u95ed</button></div>';
  document.body.appendChild(o);
};

console.log('app-fix.js loaded: displayResult patched, showKnowledge ready, lang='+(localStorage.getItem('mech_lang')||'zh'));
})();
