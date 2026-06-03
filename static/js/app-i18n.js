/**
 * 机械计算 — 知识点弹窗 / 公式示例 / SVG图示 / 语言切换
 * 全局可访问，最后加载确保覆盖所有定义
 */

// ============ 知识点数据 (27项) ============
window.WIKI_KNOWLEDGE = {
  '截面惯性矩': {formula:'I = ∫y²dA', desc:'截面抵抗弯曲的能力', note:'矩形I=bh³/12, 圆I=πd⁴/64, 空心管I=π(D⁴-d⁴)/64', url:'https://baike.baidu.com/item/%E6%88%AA%E9%9D%A2%E6%83%AF%E6%80%A7%E7%9F%A9'},
  '压杆稳定': {formula:'Pcr = π²EI/(μL)²', desc:'细长压杆失稳临界载荷', note:'μ: 两端铰支=1.0, 两端固定=0.5, 一端固定一端铰支=0.7, 一端固定一端自由=2.0', url:'https://baike.baidu.com/item/%E5%8E%8B%E6%9D%86%E7%A8%B3%E5%AE%9A'},
  '焊缝强度': {formula:'τ = F/(0.707·K·l·n)', desc:'角焊缝喉部剪切强度校核', note:'Q235焊条E43: [τ]=120MPa; Q345焊条E50: [τ]=150MPa', url:'https://baike.baidu.com/item/%E7%84%8A%E7%BC%9D'},
  '键强度': {formula:'τ=2T/(dbl), σp=4T/(dhl)', desc:'平键剪切+挤压双重校核', note:'许用挤压[σp]: 钢120~150MPa, 铸铁70~80MPa', url:'https://baike.baidu.com/item/%E9%94%AE%E8%BF%9E%E6%8E%A5'},
  '销强度': {formula:'τ = 4F/(nπd²)', desc:'圆柱销承受横向剪切', note:'45钢[τ]=80~120MPa', url:'https://baike.baidu.com/item/%E9%94%80%E8%BF%9E%E6%8E%A5'},
  '过盈配合': {formula:'p = δ/(d·(C₁/E₁+C₂/E₂))', desc:'弹性变形产生接触压力传递扭矩', note:'热装: 钢件每100°C约膨胀0.12%', url:'https://baike.baidu.com/item/%E8%BF%87%E7%9B%88%E9%85%8D%E5%90%88'},
  '压入力': {formula:'F = f·π·d·L·p', desc:'压装克服摩擦力', note:'润滑f≈0.10~0.15, 干摩擦f≈0.15~0.25', url:'https://baike.baidu.com/item/%E5%8E%8B%E8%A3%85'},
  '齿轮传动': {formula:'d=mz, da=d+2m, df=d-2.5m', desc:'标准直齿圆柱齿轮参数关系', note:'例: m=3,z=20 → d=60, da=66, df=52.5mm', url:'https://baike.baidu.com/item/%E9%BD%BF%E8%BD%AE'},
  '弹簧': {formula:'k=Gd⁴/(8Dm³n), τ=8KFD/(πd³)', desc:'圆柱螺旋弹簧刚度和应力校核', note:'G=79000MPa(弹簧钢), K为曲度系数', url:'https://baike.baidu.com/item/%E5%BC%B9%E7%B0%A7'},
  '螺纹': {formula:'d₂=d-0.6495P, d₁=d-1.0825P', desc:'公制螺纹基本尺寸 ISO 68', note:'例: M12×1.75 → d₂=10.863, d₁=10.106mm', url:'https://baike.baidu.com/item/%E6%99%AE%E9%80%9A%E8%9E%BA%E7%BA%B9'},
  '三角皮带': {formula:'P = z·P₀·Kα·KL', desc:'三角皮带传动功率与根数', note:'小带轮包角应≥120°, 带速5~25m/s最佳', url:'https://baike.baidu.com/item/%E4%B8%89%E8%A7%92%E5%B8%A6'},
  '同步带': {formula:'d=z·Pb/π', desc:'同步带轮分度圆直径', note:'例: L型Pb=9.525,z=18 → d=54.57mm', url:'https://baike.baidu.com/item/%E5%90%8C%E6%AD%A5%E5%B8%A6'},
  '凸轮': {formula:'s=h(θ/β-sin(2πθ/β)/(2π))', desc:'正弦加速度凸轮—无冲击高速', note:'Cv=2.0, Ca=6.28(正弦); Cv=1.57, Ca=4.93(余弦)', url:'https://baike.baidu.com/item/%E5%87%B8%E8%BD%AE%E6%9C%BA%E6%9E%84'},
  '公差配合': {formula:'ES/EI(孔), es/ei(轴)查标准', desc:'基孔制H/基轴制h配合', note:'H7/g6间隙配合, H7/k6过渡, H7/s6过盈', url:'https://baike.baidu.com/item/%E5%85%AC%E5%B7%AE%E9%85%8D%E5%90%88'},
  '冲裁力': {formula:'F=K·L·t·τ', desc:'平刃口冲裁力 K=1.3', note:'例: L=200mm,t=2mm,τ=350 → F=182kN≈18.6吨', url:'https://baike.baidu.com/item/%E5%86%B2%E8%A3%81'},
  '液压管路': {formula:'Δp=λ·L/d·ρv²/2', desc:'沿程压力损失', note:'层流λ=64/Re, 紊流λ=0.3164/Re⁰·²⁵', url:'https://baike.baidu.com/item/%E6%B2%BF%E7%A8%8B%E9%98%BB%E5%8A%9B'},
  '液压冲击': {formula:'Δp=αρ(v₁-v₂)', desc:'阀门突然关闭产生的压力冲击', note:'直接冲击 > 间接冲击, 可损坏管路', url:'https://baike.baidu.com/item/%E6%B0%B4%E9%94%A4%E6%95%88%E5%BA%94'},
  '运动学': {formula:'v=v₀+at, s=v₀t+½at², v²=v₀²+2as', desc:'匀变速直线运动三大公式', note:'自由落体: v₀=0,a=9.81,t=5s → v=49m/s,s=122.6m', url:'https://baike.baidu.com/item/%E5%8C%80%E5%8F%98%E9%80%9F%E7%9B%B4%E7%BA%BF%E8%BF%90%E5%8A%A8'},
  '转动': {formula:'ω=ω₀+αt, θ=ω₀t+½αt²', desc:'匀角速转动', note:'n(rpm) = ω×60/(2π)', url:'https://baike.baidu.com/item/%E8%A7%92%E9%80%9F%E5%BA%A6'},
  '离心力': {formula:'F=mω²r=mv²/r', desc:'旋转体离心力', note:'例: m=5kg,r=0.5m,n=300rpm → F=2467N≈50g', url:'https://baike.baidu.com/item/%E7%A6%BB%E5%BF%83%E5%8A%9B'},
  '动量': {formula:'p=mv, Ek=½mv²', desc:'动量与动能', note:'动量守恒: m₁v₁+m₂v₂ = m₁v₁′+m₂v₂′', url:'https://baike.baidu.com/item/%E5%8A%A8%E9%87%8F'},
  '功率': {formula:'P=Fv(直线), P=Tω=T·2πn/60(旋转)', desc:'功率计算', note:'例: T=50N·m,n=1000rpm → P=5.236kW', url:'https://baike.baidu.com/item/%E5%8A%9F%E7%8E%87'},
  '振动': {formula:'ωn=√(k/m), fn=ωn/(2π)', desc:'弹簧质量系统固有频率', note:'例: k=1000N/m,m=5kg → fn=2.25Hz', url:'https://baike.baidu.com/item/%E5%9B%BA%E6%9C%89%E9%A2%91%E7%8E%87'},
  '伯努利': {formula:'p₁+½ρv₁²+ρgh₁ = p₂+½ρv₂²+ρgh₂', desc:'理想流体能量守恒', note:'例: p₁=2bar, v₁=2m/s, v₂=4m/s → p₂=1.74bar', url:'https://baike.baidu.com/item/%E4%BC%AF%E5%8A%AA%E5%88%A9%E5%8E%9F%E7%90%86'},
  '热膨胀': {formula:'ΔL=α·L₀·ΔT', desc:'线膨胀量', note:'钢α=1.2×10⁻⁵, 铝α=2.4×10⁻⁵', url:'https://baike.baidu.com/item/%E7%83%AD%E8%86%A8%E8%83%80'},
  '行星轮系': {formula:'n_sun+α·n_ring-(1+α)·n_carrier=0', desc:'α=z_ring/z_sun', note:'固定齿圈: n_c/n_s=1/(1+α)', url:'https://baike.baidu.com/item/%E8%A1%8C%E6%98%9F%E9%BD%BF%E8%BD%AE'},
  '螺旋传动': {formula:'η=tan(λ)/tan(λ+ρ), λ=atan(P/πd)', desc:'丝杆效率与自锁', note:'λ<ρ时自锁', url:'https://baike.baidu.com/item/%E8%9E%BA%E6%97%8B%E4%BC%A0%E5%8A%A8'},
};

// ============ showKnowledge 全局函数 ============
window.showKnowledge = function(topic) {
  var k = window.WIKI_KNOWLEDGE[topic];
  if (!k) { alert('\ud83d\udcd6 ' + topic + '\n\n暂无详细知识条目'); return; }
  var o = document.createElement('div');
  o.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center';
  o.onclick = function(e) { if (e.target === o) o.remove(); };
  o.innerHTML = '<div style="background:white;border-radius:12px;padding:24px;max-width:500px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.2)">' +
    '<h3 style="margin-bottom:12px;color:#2563eb">\ud83d\udcd6 ' + topic + '</h3>' +
    '<div style="background:#f0f9ff;padding:10px 14px;border-radius:6px;margin-bottom:10px"><strong>公式:</strong> <code>' + k.formula + '</code></div>' +
    '<p style="margin-bottom:8px;color:#475569">' + k.desc + '</p>' + 
    (k.note ? '<p style="margin-bottom:12px;color:#64748b;font-size:13px;background:#f8fafc;padding:8px 12px;border-radius:4px">\ud83d\udca1 ' + k.note + '</p>' : '') +
    (k.url ? '<a href="' + k.url + '" target="_blank" style="color:#2563eb;font-size:13px">\ud83d\udd17 百度百科 →</a>' : '') +
    '<button onclick="this.parentElement.parentElement.remove()" style="display:block;margin-top:16px;padding:8px 24px;background:#2563eb;color:white;border:none;border-radius:6px;cursor:pointer">关闭</button></div>';
  document.body.appendChild(o);
};


// ============ 公式示例 ============
// 在计算结果后自动追加公式示例
window.FORMULA_EXAMPLES = {
  'gear-basic': {formula:'d=mz=3×20=60mm, da=d+2m=60+6=66mm, df=d-2.5m=60-7.5=52.5mm', params:'m=3, z=20, α=20°'},
  'gear-mesh': {formula:'a=m(z1+z2)/2=3(20+60)/2=120mm, i=z2/z1=60/20=3', params:'m=3, z1=20, z2=60'},
  'gear-motor': {formula:'T=9550×P/n=9550×2.2/1450=14.49N·m, T₂=T×i×η=14.49×5×0.95=68.83N·m', params:'P=2.2kW, n=1450rpm, i=5'},
  'spring-compression': {formula:'C=Dm/d=30/4=7.5, k=Gd⁴/(8Dm³n)=79000×4⁴/(8×30³×10)=9.36N/mm', params:'d=4mm, Dm=30mm, n=10, G=79000MPa'},
  'thread-metric': {formula:'d₂=d-0.6495P=12-0.6495×1.75=10.863mm, d₁=d-1.0825P=10.106mm', params:'M12×1.75'},
  'thread-bolt': {formula:'Fp=0.6×σs×As=0.6×640×84.3/1000=32.36kN, T=0.2×Fp×d=0.2×32.36×12=77.66N·m', params:'M12, 8.8级'},
  'chain-sprocket': {formula:'d=P/sin(π/z)=12.7/sin(π/17)=69.116mm', params:'P=12.7mm, z=17'},
  'chain-length': {formula:'Lp=2a/P+(z1+z2)/2+(z2-z1)²/(4π²a/P)=104.43→106节', params:'P=12.7, z1=17, z2=34, a=500mm'},
  'belt-vbelt': {formula:'v=π·d1·n/60000=π×75×1440/60000=5.65m/s, α=180-60(d2-d1)/a=163°', params:'A型, P=3kW, n=1440, i=2.5'},
  'press-blanking': {formula:'F=K·L·t·τ=1.3×200×2×350=182000N=182kN≈18.55吨', params:'L=200mm, t=2mm, τ=350MPa'},
  'press-vbend': {formula:'F=k·b·t²·σb/w=1.33×100×1.5²×400/12=9975N≈1.02吨', params:'b=100mm, t=1.5mm, σb=400MPa, w=12mm'},
  'tolerance-fit': {formula:'φ50H7: ES=+25μm, EI=0; φ50g6: es=-9μm, ei=-25μm; Xmax=ES-ei=50μm', params:'φ50 H7/g6'},
  'motor-speed': {formula:'n=60f/p=60×50/2=1500rpm(4极), 额定≈1455rpm', params:'4极, 50Hz'},
  'motor-torque': {formula:'T=9550×P/n=9550×5.5/1455=36.1N·m, I≈P×2=11A(380V)', params:'5.5kW, 4极, 380V'},
  'hydraulic-pipe': {formula:'v=Q/A=70/60000/(π×0.015²/4)=6.6m/s, Re=vd/ν=6.6×0.015/46e-6=2152(层流)', params:'Q=70L/min, d=15mm, L=2m'},
  'hydraulic-shock': {formula:'a=√(K/ρ)=√(1.4e9/870)=1268m/s, Δp=ρ·a·Δv=870×1268×4=44.1bar', params:'v1=4m/s, v2=0, L=10m'},
  'cam-profile': {formula:'s=h(θ/β-sin(2πθ/β)/(2π))，正弦加速度无冲击', params:'rb=50mm, h=30mm, β=120°'},
  'strength-section': {formula:'矩形: I=bh³/12=50×100³/12=4166667mm⁴, W=bh²/6=83333mm³', params:'b=50mm, h=100mm'},
  'strength-column': {formula:'λ=L/i=2000/40.8=49, Pcr=π²EI/(μL)²=π²×206000×5e6/(1×2000)²=2.54e6N', params:'F=50kN, L=2m, I=5e6mm⁴, μ=1'},
  'strength-weld': {formula:'咒缝喉部=0.707×K=0.707×6=4.24mm, τ=F/(0.707Kl·n)=30000/(4.24×100×2)=35.4MPa', params:'F=30kN, K=6mm, l=100mm, n=2'},
  'strength-key': {formula:'τ=2T/(dbl)=2×500000/(40×12×40)=52.1MPa, σp=4T/(dhl)=4×500000/(40×8×40)=156MPa', params:'T=500N·m, d=40mm, b=12, h=8, L=40'},
  'strength-pin': {formula:'τ=4F/(nπd²)=4×10000/(π×10²)=127.3MPa', params:'F=10kN, d=10mm, n=1'},
  'strength-interference': {formula:'q=δ/(d·((1-ν)/E+(D²+d²)/(E(D²-d²))))', params:'d=50mm, δ=30μm, D₂=100mm'},
};

// ============ SVG图示 ============
window.SVG_DIAGRAMS = {
  'gear-basic': '<svg width="200" height="120" viewBox="0 0 200 120"><circle cx="80" cy="60" r="40" fill="none" stroke="#2563eb" stroke-width="2"/><circle cx="80" cy="60" r="36" fill="none" stroke="#2563eb" stroke-width="1" stroke-dasharray="3,3"/><circle cx="80" cy="60" r="4" fill="#2563eb"/><line x1="80" y1="60" x2="120" y2="60" stroke="#dc2626" stroke-width="1.5"/><text x="90" y="55" fill="#dc2626" font-size="10">r</text><text x="10" y="20" fill="#2563eb" font-size="11">齿轮纵向示意</text><text x="10" y="35" fill="#64748b" font-size="9">d=mz, da=d+2m, df=d-2.5m</text><path d="M130 30 Q150 60 130 90" fill="none" stroke="#64748b" stroke-width="1" stroke-dasharray="2,2"/></svg>',

  'spring-compression': '<svg width="200" height="120" viewBox="0 0 200 120"><line x1="50" y1="30" x2="50" y2="90" stroke="#64748b" stroke-width="1.5"/><line x1="150" y1="30" x2="150" y2="90" stroke="#64748b" stroke-width="1.5"/><path d="M50 30 Q70 35 60 45 Q50 55 70 60 Q90 65 80 75 Q70 85 90 90" fill="none" stroke="#2563eb" stroke-width="2"/><line x1="50" y1="30" x2="150" y2="30" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/><text x="55" y="20" fill="#dc2626" font-size="9">L₀</text><line x1="90" y1="90" x2="150" y2="90" stroke="#22c55e" stroke-width="1" stroke-dasharray="3,3"/><text x="100" y="108" fill="#22c55e" font-size="9">L₁(压缩后)</text><text x="10" y="15" fill="#2563eb" font-size="11">缩历管等春</text></svg>',

  'cam-profile': '<svg width="200" height="120" viewBox="0 0 200 120"><circle cx="100" cy="60" r="30" fill="#e0e7ff" stroke="#2563eb" stroke-width="1" stroke-dasharray="3,3"/><circle cx="100" cy="60" r="3" fill="#2563eb"/><text x="100" y="105" fill="#2563eb" font-size="9">基圆 rb</text><path d="M100 60 L130 30 L160 35 L175 55 L180 75 L170 90 L155 95" fill="none" stroke="#dc2626" stroke-width="2"/><text x="10" y="20" fill="#64748b" font-size="11">凸轮轮廓线</text></svg>',

  'beam-bending': '<svg width="200" height="100" viewBox="0 0 200 100"><rect x="30" y="70" width="140" height="6" fill="#2563eb" rx="2"/><polygon points="30,76 25,90 35,90" fill="#64748b"/><polygon points="170,76 165,90 175,90" fill="#64748b"/><path d="M55 70 Q100 40 145 70" fill="none" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="4,3"/><line x1="100" y1="70" x2="100" y2="50" stroke="#dc2626" stroke-width="1.5"/><text x="95" y="48" fill="#dc2626" font-size="9">F</text><text x="10" y="20" fill="#64748b" font-size="11">精曲楷線</text><text x="10" y="35" fill="#64748b" font-size="9">δ=FL³/(48EI)</text></svg>',
};

// 绘制SVG图示
window.drawDiagram = function(containerId, diagramKey) {
  var svg = window.SVG_DIAGRAMS[diagramKey];
  if (!svg) return;
  var el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = svg;
};

// ============ 公式示例注入 + SVG图示绘制 ============
// 在showResult后自动追加公式示例和SVG图示
document.addEventListener('DOMContentLoaded', function() {
  // 在showResult函数执行后追加公式示例
  var origShowResult = window.showResult;
  if (typeof origShowResult === 'function') {
    window.showResult = function(panelId, data) {
      origShowResult(panelId, data);
      
      var container = document.getElementById('result-' + panelId);
      if (!container) return;
      
      // 追加公式示例
      var example = window.FORMULA_EXAMPLES && window.FORMULA_EXAMPLES[panelId];
      if (example) {
        var exDiv = document.createElement('div');
        exDiv.style.cssText = 'margin-top:12px;padding:12px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;font-size:13px';
        exDiv.innerHTML = '<strong>\ud83d\udca1 ' + window.___('公式示例', 'zh') + '</strong><br>' +
          '<code style="color:#166534">' + example.formula + '</code><br>' +
          '<span style="color:#64748b;font-size:12px">' + window.___('参数', 'zh') + ': ' + example.params + '</span>';
        container.appendChild(exDiv);
      }
      
      // 绘制SVG图示
      var diagrams = window.SVG_DIAGRAMS;
      if (diagrams && diagrams[panelId]) {
        var svgDiv = document.createElement('div');
        svgDiv.style.cssText = 'margin-top:12px;text-align:center;background:#f8fafc;border-radius:6px;padding:8px';
        svgDiv.innerHTML = diagrams[panelId];
        container.appendChild(svgDiv);
      }
    };
  }
});
