// 机械计算 — 运行时诊断脚本
// 通过 API 返回数据，在浏览器 Console 中运行或通过 curl 模拟检测
(function() {
var report = [];

function log(msg) { report.push(msg); console.log(msg); }

log('=== 前端诊断 ===');

// 1. 检查所有JS文件加载
var scripts = document.querySelectorAll('script[src]');
log('1. JS文件加载:');
scripts.forEach(function(s) {
  var name = s.src.split('/').pop();
  log('  ' + name + ': ' + (s.complete ? 'loaded' : 'loading...'));
});

// 2. 检查全局函数注册
log('2. 全局函数检查:');
var fns = ['showKnowledge', 'showResult', 'navigateTo', 'saveHistory', 
           'copyResult', 'calcSpurGear', 'calcSprocket', 'calcVBelt', 
           'calcCoupGear', 'calcHydPipe', 'calcStrengthSection',
           'calcStrengthColumn', 'calcCamProfile', 'calcFit', 
           'calcBlanking', 'calcMotorSpeed', '___', 'translatePage', 'setLang'];
fns.forEach(function(fn) {
  var ok = typeof window[fn] === 'function';
  if (!ok) log('  ❌ ' + fn + ' NOT registered');
});

// 3. 检查面板div是否存在
log('3. 面板DOM检查:');
var panels = {
  'gear-basic': '齿轮基本参数', 'gear-mesh': '齿轮啮合', 'gear-motor': '电机选型',
  'spring-compression': '压缩弹簧', 'thread-metric': '公制螺纹',
  'chain-sprocket': '链轮参数', 'belt-vbelt': '三角皮带',
  'cam-profile': '凸轮轮廓', 'tolerance-fit': '公差配合',
  'press-blanking': '冲裁力', 'hydraulic-pipe': '管路压损',
  'coup-gear': '齿式联轴器', 'motor-speed': '同步转速',
  'strength-section': '截面惯性矩', 'strength-column': '立柱稳定',
};
for (var id in panels) {
  var el = document.getElementById('panel-' + id);
  var nav = document.querySelector('.nav-item[data-id="' + id + '"]');
  if (!el && !nav) log('  ❌ ' + panels[id] + ': 面板和导航都不存在');
  else if (!el) log('  ❌ ' + panels[id] + ': 面板div不存在');
  else if (!nav) log('  ❌ ' + panels[id] + ': 导航项不存在');
}

// 4. 检查当前激活面板
var active = document.querySelector('.calculator-panel.active');
log('4. 激活面板: ' + (active ? active.id : 'NONE'));

// 5. 返回报告
return report;
})();
