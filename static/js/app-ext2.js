/**
 * 机械计算 - 扩展模块2（液压/联轴器/O型圈/电机）
 */
(function() {
  // 追加导航项
  const NEW_NAV = [
    { category: '液压系统', items: [
      { id: 'hydraulic-pipe', label: '💧 管路压损计算', panel: 'hydraulic-pipe' },
      { id: 'hydraulic-shock', label: '💧 液压冲击计算', panel: 'hydraulic-shock' },
      { id: 'hydraulic-accumulator', label: '💧 蓄能器选型', panel: 'hydraulic-accumulator' },
      { id: 'hydraulic-tank', label: '💧 油箱热平衡', panel: 'hydraulic-tank' },
    ]},
    { category: '联轴器/密封', items: [
      { id: 'coup-gear', label: '🔧 齿式联轴器', panel: 'coup-gear' },
      { id: 'coup-universal', label: '🔧 万向联轴器', panel: 'coup-universal' },
      { id: 'coup-oring', label: '🔘 O型圈沟槽', panel: 'coup-oring' },
      { id: 'coup-htd', label: '🔗 HTD圆弧齿同步带', panel: 'coup-htd' },
    ]},
    { category: '电机常识', items: [
      { id: 'motor-speed', label: '⚡ 同步转速计算', panel: 'motor-speed' },
      { id: 'motor-torque', label: '⚡ 扭矩/电流估算', panel: 'motor-torque' },
      { id: 'motor-knowledge', label: '⚡ 电机常识速查', panel: 'motor-knowledge' },
    ]},
    { category: '材料力学', items: [
      { id: 'strength-section', label: '📐 截面惯性矩', panel: 'strength-section' },
      { id: 'strength-column', label: '🏛 立柱稳定性', panel: 'strength-column' },
      { id: 'strength-weld', label: '🔧 焊缝强度', panel: 'strength-weld' },
      { id: 'strength-key', label: '🔑 键强度校核', panel: 'strength-key' },
      { id: 'strength-pin', label: '📍 销强度校核', panel: 'strength-pin' },
      { id: 'strength-interference', label: '🔄 过盈配合计算', panel: 'strength-interference' },
      { id: 'strength-pressfit', label: '🔨 压入力计算', panel: 'strength-pressfit' },
    ]},
  ];

  // 面板模板
  const NEW_PANELS = {
    // ====== 液压 — 管路压损 ======
    'hydraulic-pipe': `
      <div class="panel-header"><h2>💧 管路压力损失计算</h2><p>沿程压力损失 Δp = λ·(L/d)·(ρv²/2)</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>流量 Q</label><input type="number" id="hp-flow" value="70"><div class="unit">L/min</div></div>
          <div class="form-group"><label>管内径 d</label><input type="number" id="hp-diam" value="15"><div class="unit">mm</div></div>
          <div class="form-group"><label>管长 L</label><input type="number" id="hp-len" value="2"><div class="unit">m</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>油液粘度 ν</label><input type="number" id="hp-vis" value="46"><div class="unit">cSt</div></div>
          <div class="form-group"><label>油液密度 ρ</label><input type="number" id="hp-dens" value="870"><div class="unit">kg/m³</div></div>
        </div>
        <button class="btn-calc" onclick="calcHydPipe()">计算</button>
      </div>
      <div class="calc-result" id="result-hydraulic-pipe"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 液压 — 冲击 ======
    'hydraulic-shock': `
      <div class="panel-header"><h2>💧 液压冲击计算</h2><p>直接/间接冲击压力校核</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>原流速 v₁</label><input type="number" id="hs-v1" value="4"><div class="unit">m/s</div></div>
          <div class="form-group"><label>变化后流速 v₂</label><input type="number" id="hs-v2" value="0"><div class="unit">m/s</div></div>
          <div class="form-group"><label>管长 L</label><input type="number" id="hs-len" value="10"><div class="unit">m</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>弹性模量 K</label><input type="number" id="hs-k" value="1400"><div class="unit">MPa</div></div>
          <div class="form-group"><label>管内径</label><input type="number" id="hs-d" value="20"><div class="unit">mm</div></div>
          <div class="form-group"><label>壁厚 δ</label><input type="number" id="hs-wall" value="2"><div class="unit">mm</div></div>
        </div>
        <button class="btn-calc" onclick="calcHydShock()">计算</button>
      </div>
      <div class="calc-result" id="result-hydraulic-shock"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 液压 — 蓄能器 ======
    'hydraulic-accumulator': `
      <div class="panel-header"><h2>💧 蓄能器有效容积计算</h2><p>等温/绝热工况有效容积</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>公称容积 V₀</label><input type="number" id="ha-vol" value="40"><div class="unit">L</div></div>
          <div class="form-group"><label>充气压力 p₀</label><input type="number" id="ha-p0" value="100"><div class="unit">bar</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>最低工作压力 p₁</label><input type="number" id="ha-p1" value="120"><div class="unit">bar</div></div>
          <div class="form-group"><label>最高工作压力 p₂</label><input type="number" id="ha-p2" value="200"><div class="unit">bar</div></div>
        </div>
        <button class="btn-calc" onclick="calcHydAccum()">计算</button>
      </div>
      <div class="calc-result" id="result-hydraulic-accumulator"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 液压 — 油箱热平衡 ======
    'hydraulic-tank': `
      <div class="panel-header"><h2>💧 油箱热平衡计算</h2><p>系统发热与自然散热平衡校核</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>发热功率 P</label><input type="number" id="ht-power" value="5"><div class="unit">kW</div></div>
          <div class="form-group"><label>油箱容积 V</label><input type="number" id="ht-vol" value="200"><div class="unit">L</div></div>
          <div class="form-group"><label>目标温升 ΔT</label><input type="number" id="ht-tr" value="30"><div class="unit">K</div></div>
        </div>
        <button class="btn-calc" onclick="calcHydTank()">计算</button>
      </div>
      <div class="calc-result" id="result-hydraulic-tank"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 齿式联轴器 ======
    'coup-gear': `
      <div class="panel-header"><h2>🔧 齿式联轴器选型</h2><p>扭矩校核与型号推荐 (CL系列)</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>功率 P</label><input type="number" id="cg-power" value="15"><div class="unit">kW</div></div>
          <div class="form-group"><label>转速 n</label><input type="number" id="cg-speed" value="1450"><div class="unit">rpm</div></div>
          <div class="form-group"><label>安全系数 K</label><input type="number" id="cg-safety" value="1.5" step="0.1"><div class="unit">—</div></div>
        </div>
        <button class="btn-calc" onclick="calcCoupGear()">计算</button>
      </div>
      <div class="calc-result" id="result-coup-gear"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 万向联轴器 ======
    'coup-universal': `
      <div class="panel-header"><h2>🔧 万向联轴器计算</h2><p>当量扭矩与速度波动</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>功率 P</label><input type="number" id="cu-power" value="5"><div class="unit">kW</div></div>
          <div class="form-group"><label>转速 n</label><input type="number" id="cu-speed" value="500"><div class="unit">rpm</div></div>
          <div class="form-group"><label>夹角 θ</label><input type="number" id="cu-angle" value="15"><div class="unit">°</div></div>
        </div>
        <button class="btn-calc" onclick="calcCoupUni()">计算</button>
      </div>
      <div class="calc-result" id="result-coup-universal"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== O型圈 ======
    'coup-oring': `
      <div class="panel-header"><h2>🔘 O型圈沟槽尺寸</h2><p>端面密封沟槽深度/宽度推荐</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>O型圈截面直径 d</label><input type="number" id="co-d" value="3.5" step="0.1"><div class="unit">mm</div></div>
        </div>
        <button class="btn-calc" onclick="calcOring()">计算</button>
      </div>
      <div class="calc-result" id="result-coup-oring"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== HTD圆弧齿同步带 ======
    'coup-htd': `
      <div class="panel-header"><h2>🔗 HTD圆弧齿同步带计算</h2><p>额定功率与带轮直径</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>带型</label>
            <select id="ch-type"><option>3M</option><option>5M</option><option selected>8M</option><option>14M</option><option>20M</option></select></div>
          <div class="form-group"><label>功率 P</label><input type="number" id="ch-power" value="2.2" step="0.1"><div class="unit">kW</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>转速 n</label><input type="number" id="ch-speed" value="1000"><div class="unit">rpm</div></div>
          <div class="form-group"><label>传动比 i</label><input type="number" id="ch-ratio" value="2.5" step="0.1"><div class="unit">—</div></div>
        </div>
        <button class="btn-calc" onclick="calcHtd()">计算</button>
      </div>
      <div class="calc-result" id="result-coup-htd"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 电机同步转速 ======
    'motor-speed': `
      <div class="panel-header"><h2>⚡ 电机同步转速计算</h2><p>n = 60f/p</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>极数</label>
            <select id="ms-poles"><option>2</option><option selected>4</option><option>6</option><option>8</option></select></div>
          <div class="form-group"><label>频率 f</label><input type="number" id="ms-freq" value="50"><div class="unit">Hz</div></div>
        </div>
        <button class="btn-calc" onclick="calcMotorSpeed()">计算</button>
      </div>
      <div class="calc-result" id="result-motor-speed"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 电机扭矩/电流 ======
    'motor-torque': `
      <div class="panel-header"><h2>⚡ 电机扭矩与电流估算</h2><p>T = 9550·P/n, I ≈ P×2</p></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>功率 P</label><input type="number" id="mt-power" value="5.5" step="0.1"><div class="unit">kW</div></div>
          <div class="form-group"><label>电压 U</label>
            <select id="mt-volt"><option selected>380</option><option>220</option></select><div class="unit">V</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>极数</label>
            <select id="mt-poles"><option>2</option><option selected>4</option><option>6</option><option>8</option></select></div>
          <div class="form-group"><label>频率</label><input type="number" id="mt-freq" value="50"><div class="unit">Hz</div></div>
        </div>
        <button class="btn-calc" onclick="calcMotorTorque()">计算</button>
      </div>
      <div class="calc-result" id="result-motor-torque"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,

    // ====== 电机常识 ======
    'motor-knowledge': `
      <div class="panel-header"><h2>⚡ 电机常识速查</h2><p>常用公式与估算方法</p></div>
      <div class="calc-result" id="result-motor-knowledge"><h3>📚 电机基础知识</h3><p>加载中...</p></div>`,
  };

  // ===== 注册到全局 =====
  // ===== 材料力学面板 =====
  const STRENGTH_PANELS = {
    'strength-section': `
      <div class="panel-header"><h2>📐 截面惯性矩计算</h2></div>
      <div class="calc-form">
        <div class="form-row"><div class="form-group"><label>截面形状</label>
          <select id="ss-shape" onchange="toggleSectionParams()">
            <option value="rect">矩形</option><option value="circle">实心圆</option>
            <option value="tube">空心圆管</option><option value="square_tube">方管</option>
            <option value="i_beam">工字钢</option><option value="t_section">T型</option></select></div></div>
        <div id="ss-params"><div class="form-row">
          <div class="form-group"><label>宽 b</label><input type="number" id="ss-b" value="50"><div class="unit">mm</div></div>
          <div class="form-group"><label>高 h</label><input type="number" id="ss-h" value="100"><div class="unit">mm</div></div>
        </div></div>
        <button class="btn-calc" onclick="calcStrengthSection()">计算</button>
        <button class="btn-calc" onclick="showKnowledge('截面惯性矩')" style="background:var(--accent);font-size:12px;padding:6px 14px;margin-left:8px">📖 知识</button>
      </div>
      <div class="calc-result" id="result-strength-section"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,
    'strength-column': `
      <div class="panel-header"><h2>🏛 立柱/压杆稳定性</h2></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>载荷 F</label><input type="number" id="sc-force" value="50000"><div class="unit">N</div></div>
          <div class="form-group"><label>杆长 L</label><input type="number" id="sc-len" value="2000"><div class="unit">mm</div></div>
          <div class="form-group"><label>E</label><input type="number" id="sc-e" value="206000"><div class="unit">MPa</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>面积 A</label><input type="number" id="sc-area" value="3000"><div class="unit">mm²</div></div>
          <div class="form-group"><label>惯性矩 I</label><input type="number" id="sc-i" value="5000000"><div class="unit">mm⁴</div></div>
          <div class="form-group"><label>μ</label><select id="sc-mu"><option value="0.5">0.5固-固</option><option value="0.7">0.7固-铰</option><option value="1" selected>1.0铰-铰</option><option value="2">2.0固-自</option></select></div>
        </div>
        <button class="btn-calc" onclick="calcStrengthColumn()">计算</button>
        <button class="btn-calc" onclick="showKnowledge('压杆稳定')" style="background:var(--accent);font-size:12px;padding:6px 14px;margin-left:8px">📖 知识</button>
      </div>
      <div class="calc-result" id="result-strength-column"><h3>📊 计算结果</h3><p class="text-muted">填写参数后点击计算</p></div>`,
    'strength-weld': `
      <div class="panel-header"><h2>🔧 角焊缝强度</h2></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>载荷 F</label><input type="number" id="sw-force" value="30000"><div class="unit">N</div></div>
          <div class="form-group"><label>焊脚 K</label><input type="number" id="sw-leg" value="6"><div class="unit">mm</div></div>
          <div class="form-group"><label>缝长 l</label><input type="number" id="sw-len" value="100"><div class="unit">mm</div></div>
          <div class="form-group"><label>数量 n</label><input type="number" id="sw-num" value="2"><div class="unit">—</div></div>
        </div>
        <button class="btn-calc" onclick="calcStrengthWeld()">计算</button>
        <button class="btn-calc" onclick="showKnowledge('焊缝强度')" style="background:var(--accent);font-size:12px;padding:6px 14px;margin-left:8px">📖 知识</button>
      </div>
      <div class="calc-result" id="result-strength-weld"><h3>📊 计算结果</h3></div>`,
    'strength-key': `
      <div class="panel-header"><h2>🔑 平键强度校核</h2></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>扭矩 T</label><input type="number" id="sk-torque" value="500"><div class="unit">N·m</div></div>
          <div class="form-group"><label>轴径 d</label><input type="number" id="sk-shaft" value="40"><div class="unit">mm</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>键宽 b</label><input type="number" id="sk-width" value="12"><div class="unit">mm</div></div>
          <div class="form-group"><label>键高 h</label><input type="number" id="sk-height" value="8"><div class="unit">mm</div></div>
          <div class="form-group"><label>键长 L</label><input type="number" id="sk-len" value="40"><div class="unit">mm</div></div>
        </div>
        <button class="btn-calc" onclick="calcStrengthKey()">计算</button>
        <button class="btn-calc" onclick="showKnowledge('键强度')" style="background:var(--accent);font-size:12px;padding:6px 14px;margin-left:8px">📖 知识</button>
      </div>
      <div class="calc-result" id="result-strength-key"><h3>📊 计算结果</h3></div>`,
    'strength-pin': `
      <div class="panel-header"><h2>📍 销剪切强度</h2></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>载荷 F</label><input type="number" id="sp-force" value="10000"><div class="unit">N</div></div>
          <div class="form-group"><label>直径 d</label><input type="number" id="sp-diam" value="10"><div class="unit">mm</div></div>
          <div class="form-group"><label>数量 n</label><input type="number" id="sp-num" value="1"><div class="unit">个</div></div>
        </div>
        <button class="btn-calc" onclick="calcStrengthPin()">计算</button>
        <button class="btn-calc" onclick="showKnowledge('销强度')" style="background:var(--accent);font-size:12px;padding:6px 14px;margin-left:8px">📖 知识</button>
      </div>
      <div class="calc-result" id="result-strength-pin"><h3>📊 计算结果</h3></div>`,
    'strength-interference': `
      <div class="panel-header"><h2>🔄 过盈配合计算</h2></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>配合直径 d</label><input type="number" id="si-shaft" value="50"><div class="unit">mm</div></div>
          <div class="form-group"><label>过盈量 δ</label><input type="number" id="si-int" value="30"><div class="unit">μm</div></div>
          <div class="form-group"><label>轮毂外径 D</label><input type="number" id="si-hub" value="100"><div class="unit">mm</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>配合长 L</label><input type="number" id="si-len" value="60"><div class="unit">mm</div></div>
          <div class="form-group"><label>摩擦系数 f</label><input type="number" id="si-fric" value="0.15" step="0.01"><div class="unit">—</div></div>
        </div>
        <button class="btn-calc" onclick="calcStrengthInterference()">计算</button>
        <button class="btn-calc" onclick="showKnowledge('过盈配合')" style="background:var(--accent);font-size:12px;padding:6px 14px;margin-left:8px">📖 知识</button>
      </div>
      <div class="calc-result" id="result-strength-interference"><h3>📊 计算结果</h3></div>`,
    'strength-pressfit': `
      <div class="panel-header"><h2>🔨 压入力计算</h2></div>
      <div class="calc-form">
        <div class="form-row">
          <div class="form-group"><label>轴径 d</label><input type="number" id="pf-shaft" value="50"><div class="unit">mm</div></div>
          <div class="form-group"><label>过盈量 δ</label><input type="number" id="pf-int" value="30"><div class="unit">μm</div></div>
          <div class="form-group"><label>轮毂外径 D</label><input type="number" id="pf-hub" value="100"><div class="unit">mm</div></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>配合长 L</label><input type="number" id="pf-len" value="60"><div class="unit">mm</div></div>
          <div class="form-group"><label>摩擦系数 f</label><input type="number" id="pf-fric" value="0.15" step="0.01"><div class="unit">—</div></div>
        </div>
        <button class="btn-calc" onclick="calcStrengthPressfit()">计算</button>
        <button class="btn-calc" onclick="showKnowledge('压入力')" style="background:var(--accent);font-size:12px;padding:6px 14px;margin-left:8px">📖 知识</button>
      </div>
      <div class="calc-result" id="result-strength-pressfit"><h3>📊 计算结果</h3></div>`,
  };
  Object.assign(NEW_PANELS, STRENGTH_PANELS);

  // (Wiki知识点和showKnowledge已移至app-i18n.js)
  //
  window.toggleSectionParams = function() {
    const v = document.getElementById('ss-shape').value;
    document.getElementById('ss-params').innerHTML = ({
      rect: '<div class=form-row><div class=form-group><label>宽 b</label><input type=number id=ss-b value=50><div class=unit>mm</div></div><div class=form-group><label>高 h</label><input type=number id=ss-h value=100><div class=unit>mm</div></div></div>',
      circle: '<div class=form-row><div class=form-group><label>直径 d</label><input type=number id=ss-d value=50><div class=unit>mm</div></div></div>',
      tube: '<div class=form-row><div class=form-group><label>外径 D</label><input type=number id=ss-D value=50><div class=unit>mm</div></div><div class=form-group><label>内径 d</label><input type=number id=ss-d2 value=40><div class=unit>mm</div></div></div>',
      square_tube: '<div class=form-row><div class=form-group><label>外 B</label><input type=number id=ss-B value=60><div class=unit>mm</div></div><div class=form-group><label>外 H</label><input type=number id=ss-H value=80><div class=unit>mm</div></div></div><div class=form-row><div class=form-group><label>内 b</label><input type=number id=ss-b2 value=50><div class=unit>mm</div></div><div class=form-group><label>内 h</label><input type=number id=ss-h2 value=70><div class=unit>mm</div></div></div>',
      i_beam: '<div class=form-row><div class=form-group><label>高 H</label><input type=number id=ss-H2 value=200><div class=unit>mm</div></div><div class=form-group><label>翼宽 B</label><input type=number id=ss-B2 value=100><div class=unit>mm</div></div></div><div class=form-row><div class=form-group><label>翼厚 t</label><input type=number id=ss-t value=10><div class=unit>mm</div></div><div class=form-group><label>腹厚 tw</label><input type=number id=ss-tw value=6><div class=unit>mm</div></div></div>',
      t_section: '<div class=form-row><div class=form-group><label>翼宽 B</label><input type=number id=ss-B3 value=100><div class=unit>mm</div></div><div class=form-group><label>高 H</label><input type=number id=ss-H3 value=150><div class=unit>mm</div></div></div><div class=form-row><div class=form-group><label>翼厚 t</label><input type=number id=ss-t2 value=12><div class=unit>mm</div></div><div class=form-group><label>腹厚 tw</label><input type=number id=ss-tw2 value=8><div class=unit>mm</div></div></div>',
    }[v] || '');
  };

  // ===== 材料力学计算函数 =====
  function showStrRes(id, data) {
    const el = document.getElementById('result-' + id);
    if (!el) return;
    if (data.error) { el.innerHTML = '<div class=result-error>' + data.error + '</div>'; return; }
    let h = '<h3>📊 计算结果</h3><table class=result-table>';
    for (const [k, v] of Object.entries(data)) if (typeof v !== 'object') h += '<tr><td>' + k.replace(/_/g,' ') + '</td><td class=value-num>' + v + '</td></tr>';
    h += '</table>';
    el.innerHTML = h;
  }

  function g(id) { return parseFloat(document.getElementById(id).value) || 0; }
  function gi(id) { return parseInt(document.getElementById(id).value) || 1; }
  window.calcStrengthSection = async function() {
    const shape = document.getElementById('ss-shape').value;
    const m = {rect:{b:'ss-b',h:'ss-h'},circle:{d:'ss-d'},tube:{D:'ss-D',d:'ss-d2'},
      square_tube:{B:'ss-B',H:'ss-H',b:'ss-b2',h:'ss-h2'},
      i_beam:{B:'ss-B2',H:'ss-H2',t:'ss-t',tw:'ss-tw'},
      t_section:{B:'ss-B3',H:'ss-H3',t:'ss-t2',tw:'ss-tw2'}};
    const p = {};
    for (const [k,id] of Object.entries(m[shape])) { const e = document.getElementById(id); if (e) p[k] = parseFloat(e.value) || 0; }
    const r = await apiPost('/api/calculate/strength/section', {shape, params: p});
    showStrRes('strength-section', r);
    saveHistory('strength-section', r);
  };
  window.calcStrengthColumn = async function() {
    const r = await apiPost('/api/calculate/strength/column', {force:g('sc-force'),area:g('sc-area'),elastic_modulus:g('sc-e'),length:g('sc-len'),inertia:g('sc-i'),mu:parseFloat(document.getElementById('sc-mu').value)});
    showStrRes('strength-column', r); saveHistory('strength-column', r);
  };
  window.calcStrengthWeld = async function() {
    const r = await apiPost('/api/calculate/strength/weld', {force:g('sw-force'),leg:g('sw-leg'),length:g('sw-len'),num:gi('sw-num')});
    showStrRes('strength-weld', r); saveHistory('strength-weld', r);
  };
  window.calcStrengthKey = async function() {
    const r = await apiPost('/api/calculate/strength/key', {torque:g('sk-torque'),shaft_diameter:g('sk-shaft'),width:g('sk-width'),height:g('sk-height'),length:g('sk-len')});
    showStrRes('strength-key', r); saveHistory('strength-key', r);
  };
  window.calcStrengthPin = async function() {
    const r = await apiPost('/api/calculate/strength/pin', {force:g('sp-force'),diameter:g('sp-diam'),num:gi('sp-num')});
    showStrRes('strength-pin', r); saveHistory('strength-pin', r);
  };
  window.calcStrengthInterference = async function() {
    const r = await apiPost('/api/calculate/strength/interference', {shaft_diameter:g('si-shaft'),interference:g('si-int'),hub_od:g('si-hub'),length:g('si-len'),friction:g('si-fric')});
    showStrRes('strength-interference', r); saveHistory('strength-interference', r);
  };
  window.calcStrengthPressfit = async function() {
    const r = await apiPost('/api/calculate/strength/pressfit', {shaft_diameter:g('pf-shaft'),interference:g('pf-int'),hub_od:g('pf-hub'),length:g('pf-len'),friction:g('pf-fric')});
    showStrRes('strength-pressfit', r); saveHistory('strength-pressfit', r);
  };

  window.EXTRA_NAV_ITEMS2 = NEW_NAV;
  window.EXTRA_PANELS2 = NEW_PANELS;
  // ===== 计算函数 =====
  async function apiPost(url, data) {
    const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
    return r.json();
  }

  function showResult(panelId, data) {
    const el = document.getElementById('result-' + panelId);
    if (!el) return;
    if (data.error) {
      el.innerHTML = `<div class="result-error">${data.error}</div>`;
      return;
    }
    let html = '<h3>📊 计算结果</h3><table class="result-table">';
    for (const [key, val] of Object.entries(data)) {
      if (typeof val === 'object' && val !== null) continue;
      const label = key.replace(/_/g,' ').replace(/([A-Z])/g,' $1').trim();
      html += `<tr><td>${label}</td><td class="value-num">${val}</td></tr>`;
    }
    html += '</table>';
    
    // 导出按钮
    html += `<div style="margin-top:12px;display:flex;gap:8px">
      <button class="btn-calc" onclick="copyResult('result-${panelId}')" style="font-size:12px;padding:6px 14px">📋 复制</button>
      <button class="btn-calc" onclick="exportResultPDF('result-${panelId}')" style="font-size:12px;padding:6px 14px">📄 PDF</button>
    </div>`;
    
    el.innerHTML = html;
  }

  // 液压 — 管路压损
  window.calcHydPipe = async function() {
    const d = {
      flow: parseFloat(document.getElementById('hp-flow').value),
      diameter: parseFloat(document.getElementById('hp-diam').value),
      length: parseFloat(document.getElementById('hp-len').value),
      viscosity: parseFloat(document.getElementById('hp-vis').value),
      density: parseFloat(document.getElementById('hp-dens').value),
    };
    const r = await apiPost('/api/calculate/hydraulic/pipe', d);
    showResult('hydraulic-pipe', r);
    saveHistory('hydraulic-pipe', r);
  };

  // 液压 — 冲击
  window.calcHydShock = async function() {
    const d = {
      v1: parseFloat(document.getElementById('hs-v1').value),
      v2: parseFloat(document.getElementById('hs-v2').value),
      pipe_length: parseFloat(document.getElementById('hs-len').value),
      bulk_modulus: parseFloat(document.getElementById('hs-k').value),
      pipe_diameter: parseFloat(document.getElementById('hs-d').value),
      wall_thickness: parseFloat(document.getElementById('hs-wall').value),
    };
    const r = await apiPost('/api/calculate/hydraulic/shock', d);
    showResult('hydraulic-shock', r);
    saveHistory('hydraulic-shock', r);
  };

  // 液压 — 蓄能器
  window.calcHydAccum = async function() {
    const d = {
      volume: parseFloat(document.getElementById('ha-vol').value),
      precharge_pressure: parseFloat(document.getElementById('ha-p0').value),
      min_pressure: parseFloat(document.getElementById('ha-p1').value),
      max_pressure: parseFloat(document.getElementById('ha-p2').value),
    };
    const r = await apiPost('/api/calculate/hydraulic/accumulator', d);
    showResult('hydraulic-accumulator', r);
    saveHistory('hydraulic-accumulator', r);
  };

  // 液压 — 油箱热平衡
  window.calcHydTank = async function() {
    const d = {
      power: parseFloat(document.getElementById('ht-power').value),
      volume: parseFloat(document.getElementById('ht-vol').value),
      temp_rise: parseFloat(document.getElementById('ht-tr').value),
    };
    const r = await apiPost('/api/calculate/hydraulic/tank', d);
    showResult('hydraulic-tank', r);
    saveHistory('hydraulic-tank', r);
  };

  // 齿式联轴器
  window.calcCoupGear = async function() {
    const d = {
      power: parseFloat(document.getElementById('cg-power').value),
      speed: parseFloat(document.getElementById('cg-speed').value),
      safety: parseFloat(document.getElementById('cg-safety').value),
    };
    const r = await apiPost('/api/calculate/coupling/gear', d);
    showResult('coup-gear', r);
    saveHistory('coup-gear', r);
  };

  // 万向联轴器
  window.calcCoupUni = async function() {
    const d = {
      power: parseFloat(document.getElementById('cu-power').value),
      speed: parseFloat(document.getElementById('cu-speed').value),
      angle: parseFloat(document.getElementById('cu-angle').value),
    };
    const r = await apiPost('/api/calculate/coupling/universal', d);
    showResult('coup-universal', r);
    saveHistory('coup-universal', r);
  };

  // O型圈
  window.calcOring = async function() {
    const d = { section_diameter: parseFloat(document.getElementById('co-d').value) };
    const r = await apiPost('/api/calculate/coupling/oring', d);
    showResult('coup-oring', r);
    saveHistory('coup-oring', r);
  };

  // HTD同步带
  window.calcHtd = async function() {
    const d = {
      belt_type: document.getElementById('ch-type').value,
      power: parseFloat(document.getElementById('ch-power').value),
      speed: parseFloat(document.getElementById('ch-speed').value),
      ratio: parseFloat(document.getElementById('ch-ratio').value),
    };
    const r = await apiPost('/api/calculate/coupling/htd', d);
    showResult('coup-htd', r);
    saveHistory('coup-htd', r);
  };

  // 电机同步转速
  window.calcMotorSpeed = async function() {
    const d = {
      poles: parseInt(document.getElementById('ms-poles').value),
      freq: parseFloat(document.getElementById('ms-freq').value),
    };
    const r = await apiPost('/api/calculate/motor/speed', d);
    const el = document.getElementById('result-motor-speed');
    if (r.error) { el.innerHTML = `<div class="result-error">${r.error}</div>`; return; }
    el.innerHTML = `<h3>⚡ 同步转速</h3><table class="result-table">
      <tr><td>极数</td><td>${r.poles}</td></tr>
      <tr><td>电源频率</td><td>${r.frequency_hz} Hz</td></tr>
      <tr><td>同步转速</td><td class="value-num">${r.sync_speed_rpm} rpm</td></tr>
      <tr><td>额定转速(约)</td><td class="value-num">${r.slip_speed_rpm} rpm</td></tr>
      <tr><td>公式</td><td>${r.formula}</td></tr>
    </table>`;
    saveHistory('motor-speed', r);
  };

  // 电机扭矩/电流
  window.calcMotorTorque = async function() {
    const power = parseFloat(document.getElementById('mt-power').value);
    const volt = parseInt(document.getElementById('mt-volt').value);
    const poles = parseInt(document.getElementById('mt-poles').value);
    const freq = parseFloat(document.getElementById('mt-freq').value);
    
    const [tq, cur] = await Promise.all([
      apiPost('/api/calculate/motor/torque', { power, poles, freq }),
      apiPost('/api/calculate/motor/current', { power, voltage: volt }),
    ]);
    
    const el = document.getElementById('result-motor-torque');
    el.innerHTML = `<h3>⚡ 扭矩与电流</h3><table class="result-table">
      <tr><td>功率</td><td>${tq.power_kw} kW</td></tr>
      <tr><td>额定转速</td><td class="value-num">${tq.speed_rpm} rpm</td></tr>
      <tr><td>额定扭矩</td><td class="value-num">${tq.torque_nm} N·m</td></tr>
      <tr><td>估算电流 (${volt}V)</td><td class="value-num">${cur.estimated_current_a} A</td></tr>
      <tr><td>扭矩公式</td><td>${tq.formula}</td></tr>
      <tr><td>电流公式</td><td>${cur.formula}</td></tr>
    </table>`;
    saveHistory('motor-torque', { power_kw: tq.power_kw, torque: tq.torque_nm, current: cur.estimated_current_a });
  };

  // ===== 电机常识速查 =====
  (async function loadMotorKnowledge() {
    try {
      const r = await fetch('/api/data/motor_knowledge').then(r => r.json());
      const el = document.getElementById('result-motor-knowledge');
      if (!el) return;
      let html = '<h3>📚 电机基础知识</h3>';
      for (const [topic, info] of Object.entries(r)) {
        html += `<div style="margin-bottom:16px;padding:12px;background:#f8fafc;border-radius:6px">`;
        html += `<h4 style="margin-bottom:6px;color:#2563eb">${topic}</h4>`;
        html += `<p style="font-size:13px;margin-bottom:4px"><code>${info.formula || ''}</code></p>`;
        html += `<p style="font-size:13px;color:#475569">${info.desc}</p>`;
        if (info.example) html += `<p style="font-size:12px;color:#64748b;margin-top:4px">📌 ${info.example}</p>`;
        if (info.table) {
          html += '<table class="result-table" style="margin-top:6px"><tr>';
          for (const [k,v] of Object.entries(info.table)) html += `<tr><td>${k}</td><td class="value-num">${v} rpm</td></tr>`;
          html += '</table>';
        }
        html += '</div>';
      }
      el.innerHTML = html;
    } catch(e) {}
  })();

  // ===== 注册（延迟执行，等app.js加载完） =====
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registerPanels);
  } else {
    registerPanels();
  }

  function registerPanels() {
    // 追加导航到侧边栏
    const ul = document.getElementById('nav-list');
    if (ul) {
      NEW_NAV.forEach(group => {
        if (extendsNavItem(ul, group)) return; // 避免重复
        const liCat = document.createElement('li');
        liCat.className = 'nav-category';
        liCat.textContent = group.category;
        ul.appendChild(liCat);
        group.items.forEach(item => {
          const liItem = document.createElement('li');
          liItem.className = 'nav-item';
          liItem.dataset.id = item.id;
          liItem.textContent = item.label;
          liItem.onclick = function() { window.navigateTo(item.id); };
          ul.appendChild(liItem);
        });
      });
    }
    
    // 创建缺失的面板div
    const container = document.getElementById('calculator-panels');
    if (container) {
      Object.entries(NEW_PANELS).forEach(([id, html]) => {
        if (!document.getElementById('panel-' + id)) {
          const div = document.createElement('div');
          div.className = 'calculator-panel';
          div.id = 'panel-' + id;
          div.innerHTML = html;
          container.appendChild(div);
        }
      });
    }
  }
  
  function extendsNavItem(ul, group) {
    var cats = ul.getElementsByClassName('nav-category');
    for (var i = 0; i < cats.length; i++) {
      if (cats[i].textContent === group.category) return true;
    }
    return false;
  }
})();
