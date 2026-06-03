/**
 * 机械计算 - 扩展模块（带传动/凸轮/分割器/公差/冲压 + 图表/历史/导出）
 */

// ============ 导航项扩展 ============
// 将通过 init 后的钩子动态追加

const EXTRA_NAV_ITEMS = [
  { category: '带传动', items: [
    { id: 'belt-vbelt', label: '🔗 三角皮带计算', panel: 'belt-vbelt' },
    { id: 'belt-sync', label: '🔗 同步带计算', panel: 'belt-sync' },
  ]},
  { category: '凸轮/分割器', items: [
    { id: 'cam-profile', label: '🎯 凸轮轮廓计算', panel: 'cam-profile' },
    { id: 'cam-indexer', label: '🎯 分割器选型', panel: 'cam-indexer' },
    { id: 'cam-divider', label: '🎯 分度盘计算', panel: 'cam-divider' },
  ]},
  { category: '公差配合', items: [
    { id: 'tolerance-fit', label: '📐 公差配合计算', panel: 'tolerance-fit' },
    { id: 'tolerance-shaft', label: '📐 轴公差计算', panel: 'tolerance-shaft' },
    { id: 'tolerance-hole', label: '📐 孔公差计算', panel: 'tolerance-hole' },
  ]},
  { category: '冲压钣金', items: [
    { id: 'press-blanking', label: '✂️ 冲裁力计算', panel: 'press-blanking' },
    { id: 'press-vbend', label: '✂️ V型弯曲力', panel: 'press-vbend' },
    { id: 'press-ubend', label: '✂️ U型弯曲力', panel: 'press-ubend' },
    { id: 'press-emboss', label: '✂️ 压印力计算', panel: 'press-emboss' },
    { id: 'press-shear', label: '✂️ 剪切力计算', panel: 'press-shear' },
  ]},
  { category: '工具', items: [
    { id: 'tool-history', label: '📜 计算历史', panel: 'tool-history' },
  ]},
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
];

// ============ 扩展面板HTML ============

const EXTRA_PANELS = {

  // ----- 三角皮带 -----
  'belt-vbelt': `
    <div class="panel-header"><h2>🔗 三角皮带传动计算</h2><p>计算皮带长度、根数、包角、带速</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>带型</label>
          <select id="bv-section"><option>A</option><option>B</option><option>C</option><option>D</option><option selected>SPA</option><option>SPB</option><option>SPC</option><option>Z</option></select></div>
        <div class="form-group"><label>功率 P</label><input type="number" id="bv-power" step="0.1" value="3"><div class="unit">kW</div></div>
        <div class="form-group"><label>小带轮转速 n</label><input type="number" id="bv-speed" value="1440"><div class="unit">rpm</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>传动比 i</label><input type="number" id="bv-ratio" step="0.1" value="2.5"><div class="unit">—</div></div>
        <div class="form-group"><label>中心距 C</label><input type="number" id="bv-center" value="400"><div class="unit">mm</div></div>
      </div>
      <button class="btn-calc" onclick="calcVbelt()">计算</button>
    </div>
    <div class="calc-result" id="result-belt-vbelt"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 同步带 -----
  'belt-sync': `
    <div class="panel-header"><h2>🔗 同步带传动计算</h2><p>周节制同步带选型与参数计算</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>带型</label>
          <select id="bs-type"><option>MXL</option><option>XL</option><option selected>L</option><option>H</option><option>XH</option><option>XXH</option></select></div>
        <div class="form-group"><label>功率 P</label><input type="number" id="bs-power" step="0.1" value="0.75"><div class="unit">kW</div></div>
        <div class="form-group"><label>转速 n</label><input type="number" id="bs-speed" value="1000"><div class="unit">rpm</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>传动比 i</label><input type="number" id="bs-ratio" step="0.1" value="2"><div class="unit">—</div></div>
        <div class="form-group"><label>小带轮齿数 z₁</label><input type="number" id="bs-z1" placeholder="自动推荐"><div class="unit">—</div></div>
        <div class="form-group"><label>中心距 C</label><input type="number" id="bs-center" placeholder="可选"><div class="unit">mm</div></div>
      </div>
      <button class="btn-calc" onclick="calcSyncBelt()">计算</button>
    </div>
    <div class="calc-result" id="result-belt-sync"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 凸轮轮廓 -----
  'cam-profile': `
    <div class="panel-header"><h2>🎯 凸轮轮廓曲线计算</h2><p>对心直动从动件凸轮，支持多种运动规律</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>基圆半径 r₀</label><input type="number" id="cp-base" step="1" value="50"><div class="unit">mm</div></div>
        <div class="form-group"><label>升程 h</label><input type="number" id="cp-stroke" step="1" value="30"><div class="unit">mm</div></div>
        <div class="form-group"><label>推程角 β</label><input type="number" id="cp-angle" step="1" value="120"><div class="unit">°</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>运动规律</label>
          <select id="cp-motion">
            <option value="sine">正弦加速度 — 高速轻载</option>
            <option value="cosine">余弦加速度 — 中高速</option>
            <option value="uniform">等速 — 低速</option>
            <option value="modified_trapezoid">修正梯形 — 高速</option>
          </select></div>
        <div class="form-group"><label>取点数</label><input type="number" id="cp-points" value="36" step="1"><div class="unit">—</div></div>
      </div>
      <button class="btn-calc" onclick="calcCamProfile()">计算并绘图</button>
    </div>
    <div class="calc-result" id="result-cam-profile"><h3>📊 运动分析</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
    <div class="calc-result" style="margin-top:12px">
      <h3>📈 凸轮轮廓</h3>
      <canvas id="chart-cam-profile" style="width:100%;height:350px"></canvas>
    </div>
  `,

  // ----- 分割器选型 -----
  'cam-indexer': `
    <div class="panel-header"><h2>🎯 凸轮分割器选型计算</h2><p>计算入力/出力扭矩、分割时间、功率</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>负载扭矩 T<sub>L</sub></label><input type="number" id="ci-torque" step="1" value="50"><div class="unit">N·m</div></div>
        <div class="form-group"><label>工位数</label><input type="number" id="ci-stations" value="4" step="1"><div class="unit">—</div></div>
        <div class="form-group"><label>入力轴转速</label><input type="number" id="ci-rpm" value="60"><div class="unit">rpm</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>动程角</label><input type="number" id="ci-index" value="120" step="1"><div class="unit">°</div></div>
        <div class="form-group"><label>静止角</label><input type="number" id="ci-dwell" value="240" step="1"><div class="unit">°</div></div>
        <div class="form-group"><label>安全系数</label><input type="number" id="ci-safety" value="1.5" step="0.1"><div class="unit">—</div></div>
      </div>
      <button class="btn-calc" onclick="calcIndexer()">计算</button>
    </div>
    <div class="calc-result" id="result-cam-indexer"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 分度盘 -----
  'cam-divider': `
    <div class="panel-header"><h2>🎯 分度盘通用选型计算</h2><p>计算转动惯量、角加速度、惯性扭矩</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>分度角</label><input type="number" id="cd-pitch" value="90" step="1"><div class="unit">°</div></div>
        <div class="form-group"><label>转盘直径</label><input type="number" id="cd-diam" value="600"><div class="unit">mm</div></div>
        <div class="form-group"><label>负载总质量</label><input type="number" id="cd-mass" value="50"><div class="unit">kg</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>入力轴转速</label><input type="number" id="cd-rpm" value="60"><div class="unit">rpm</div></div>
      </div>
      <button class="btn-calc" onclick="calcDivider()">计算</button>
    </div>
    <div class="calc-result" id="result-cam-divider"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 公差配合 -----
  'tolerance-fit': `
    <div class="panel-header"><h2>📐 公差配合计算</h2><p>孔轴配合计算，判断间隙/过渡/过盈配合</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>公称尺寸 D</label><input type="number" id="tf-nominal" value="50" step="1"><div class="unit">mm</div></div>
        <div class="form-group"><label>孔公差带</label><input type="text" id="tf-hole" value="H7"><div class="unit">如 H7, H8, G6</div></div>
        <div class="form-group"><label>轴公差带</label><input type="text" id="tf-shaft" value="g6"><div class="unit">如 h6, g6, f7</div></div>
      </div>
      <div class="form-row">
        <div class="form-group" style="flex:2">
          <label>常用推荐配合</label>
          <div id="tf-recos"></div>
        </div>
      </div>
      <button class="btn-calc" onclick="calcFit()">计算配合</button>
    </div>
    <div class="calc-result" id="result-tolerance-fit"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 轴公差 -----
  'tolerance-shaft': `
    <div class="panel-header"><h2>📐 轴公差计算</h2><p>轴的基本偏差与IT公差等级计算</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>公称尺寸 d</label><input type="number" id="ts-nominal" value="50" step="1"><div class="unit">mm</div></div>
        <div class="form-group"><label>公差带代号</label><input type="text" id="ts-spec" value="h7"><div class="unit">如 h7, g6, f8</div></div>
      </div>
      <button class="btn-calc" onclick="calcShaftTol()">计算</button>
    </div>
    <div class="calc-result" id="result-tolerance-shaft"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 孔公差 -----
  'tolerance-hole': `
    <div class="panel-header"><h2>📐 孔公差计算</h2><p>孔的基本偏差与IT公差等级计算</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>公称尺寸 D</label><input type="number" id="th-nominal" value="50" step="1"><div class="unit">mm</div></div>
        <div class="form-group"><label>公差带代号</label><input type="text" id="th-spec" value="H7"><div class="unit">如 H7, G6, F8</div></div>
      </div>
      <button class="btn-calc" onclick="calcHoleTol()">计算</button>
    </div>
    <div class="calc-result" id="result-tolerance-hole"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 冲裁力 -----
  'press-blanking': `
    <div class="panel-header"><h2>✂️ 冲裁力计算</h2><p>F = K · L · t · τ — 含冲裁、卸料/推料/顶件力</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>冲裁周长 L</label><input type="number" id="pb-perimeter" value="200" step="1"><div class="unit">mm</div></div>
        <div class="form-group"><label>材料厚度 t</label><input type="number" id="pb-thickness" value="2" step="0.1"><div class="unit">mm</div></div>
        <div class="form-group"><label>抗剪强度 τ</label><input type="number" id="pb-shear" value="350" step="1"><div class="unit">MPa</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>材料类型</label>
          <select id="pb-material">
            <option value="steel">钢</option><option value="aluminum">铝</option><option value="copper">铜</option>
          </select></div>
      </div>
      <button class="btn-calc" onclick="calcBlanking()">计算</button>
    </div>
    <div class="calc-result" id="result-press-blanking"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- V型弯曲 -----
  'press-vbend': `
    <div class="panel-header"><h2>✂️ V型弯曲力计算</h2><p>F = k · b · t² · σ<sub>b</sub> / w</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>弯曲件宽度 b</label><input type="number" id="pv-width" value="100"><div class="unit">mm</div></div>
        <div class="form-group"><label>材料厚度 t</label><input type="number" id="pv-thick" value="1.5" step="0.1"><div class="unit">mm</div></div>
        <div class="form-group"><label>抗拉强度 σ<sub>b</sub></label><input type="number" id="pv-tensile" value="400"><div class="unit">MPa</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>凹模开口 w</label><input type="number" id="pv-die" value="12"><div class="unit">mm</div></div>
      </div>
      <button class="btn-calc" onclick="calcVBend()">计算</button>
    </div>
    <div class="calc-result" id="result-press-vbend"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- U型弯曲 -----
  'press-ubend': `
    <div class="panel-header"><h2>✂️ U型弯曲力计算</h2><p>U型弯曲力约为V型的2倍</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>弯曲件宽度 b</label><input type="number" id="pu-width" value="100"><div class="unit">mm</div></div>
        <div class="form-group"><label>材料厚度 t</label><input type="number" id="pu-thick" value="1.5" step="0.1"><div class="unit">mm</div></div>
        <div class="form-group"><label>抗拉强度 σ<sub>b</sub></label><input type="number" id="pu-tensile" value="400"><div class="unit">MPa</div></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>凹模开口 w</label><input type="number" id="pu-die" value="12"><div class="unit">mm</div></div>
      </div>
      <button class="btn-calc" onclick="calcUBend()">计算</button>
    </div>
    <div class="calc-result" id="result-press-ubend"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 压印 -----
  'press-emboss': `
    <div class="panel-header"><h2>✂️ 压印成型力计算</h2><p>F ≈ A · σ<sub>b</sub></p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>压印面积 A</label><input type="number" id="pe-area" value="300"><div class="unit">mm²</div></div>
        <div class="form-group"><label>抗拉强度 σ<sub>b</sub></label><input type="number" id="pe-tensile" value="400"><div class="unit">MPa</div></div>
      </div>
      <button class="btn-calc" onclick="calcEmboss()">计算</button>
    </div>
    <div class="calc-result" id="result-press-emboss"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 剪切力 -----
  'press-shear': `
    <div class="panel-header"><h2>✂️ 剪切力计算</h2><p>F = A · τ</p></div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group"><label>剪切面积 A</label><input type="number" id="ps-area" value="500"><div class="unit">mm²</div></div>
        <div class="form-group"><label>抗剪强度 τ</label><input type="number" id="ps-shear" value="350"><div class="unit">MPa</div></div>
      </div>
      <button class="btn-calc" onclick="calcPressShear()">计算</button>
    </div>
    <div class="calc-result" id="result-press-shear"><h3>📊 计算结果</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">点击"计算"查看结果</p></div>
  `,

  // ----- 计算历史 -----
  'tool-history': `
    <div class="panel-header"><h2>📜 计算历史记录</h2><p>自动保存最近20条计算记录</p></div>
    <div style="margin-bottom:12px">
      <button class="btn-calc" onclick="clearHistory()" style="background:var(--error)">清除历史</button>
      <button class="btn-calc" onclick="exportHistoryCSV()" style="background:var(--accent)">导出CSV</button>
    </div>
    <div class="calc-result" id="result-tool-history"><h3>📋 历史列表</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">暂无记录</p></div>
  `,
};

// ============ 扩展面板注册 ============

// 在 DOMContentLoaded 后追加导航和面板
(function extendApp() {
  const origInit = window.init || (() => {});
  const origRenderPanels = window.renderPanels || (() => {});

  // 追加导航项
  const origNav = window.NAV_ITEMS || [];
  // 在最后插入
  window.__extraNavAdded = false;
  
  const origDomReady = document.addEventListener;
  document.addEventListener('DOMContentLoaded', function onReady() {
    document.removeEventListener('DOMContentLoaded', onReady);
    
    // 追加导航
    const ul = document.getElementById('nav-list');
    if (ul) {
      EXTRA_NAV_ITEMS.forEach(group => {
        const li = document.createElement('li');
        li.className = 'nav-category';
        li.textContent = group.category;
        ul.appendChild(li);
        group.items.forEach(item => {
          const li2 = document.createElement('li');
          li2.className = 'nav-item';
          li2.dataset.id = item.id;
          li2.textContent = item.label;
          li2.onclick = () => window.navigateTo(item.id);
          ul.appendChild(li2);
        });
      });
    }
    
    // 注册面板
    const container = document.getElementById('calculator-panels');
    if (container) {
      Object.entries(EXTRA_PANELS).forEach(([id, html]) => {
        const div = document.createElement('div');
        div.className = 'calculator-panel';
        div.id = `panel-${id}`;
        div.innerHTML = html;
        container.appendChild(div);
      });
    }

    // 加载推荐配合
    loadFitRecos();

    // 加载历史
    renderHistory();
  });
})();

// ============ 计算函数 ============

function displayResult(panelId, data) {
  const container = document.getElementById(`result-${panelId}`);
  if (!container) return;
  
  if (data.error) {
    container.innerHTML = `<div class="result-error">❌ ${data.error}</div>`;
    return;
  }
  
  let html = '<h3>📊 计算结果</h3><table class="result-table">';
  
  const skipKeys = ['error', 'hole_info', 'shaft_info', 'stripping', 'stress_check', 'deflection', 'analysis', 'points', 'note', 'formula', 'fit_description'];
  
  for (const [key, val] of Object.entries(data)) {
    if (skipKeys.includes(key)) continue;
    if (typeof val === 'object') continue;
    const label = key
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^(.)/, c => c.toUpperCase());
    const display = typeof val === 'number' ? val.toLocaleString('zh-CN', {maximumFractionDigits: 4}) : val;
    html += `<tr><td>${label}</td><td class="value-num">${display}</td></tr>`;
  }
  
  html += '</table>';
  
  // 嵌套对象
  if (data.stripping) {
    html += '<h4 style="margin-top:12px;font-size:14px;color:var(--text-muted)">卸料/推料/顶件力</h4><table class="result-table">';
    for (const [k, v] of Object.entries(data.stripping)) {
      if (typeof v === 'object') continue;
      html += `<tr><td>${k.replace(/_/g, ' ').replace(/^(.)/, c => c.toUpperCase())}</td><td class="value-num">${typeof v === 'number' ? v.toFixed(2) : v}</td></tr>`;
    }
    html += '</table>';
  }
  
  if (data.stress_check) {
    const sc = data.stress_check;
    const safe = sc.is_safe ? '<span class="result-success">✅ 安全</span>' : '<span style="color:var(--error);background:#fef2f2;padding:4px 10px;border-radius:4px">⚠️ 超应力</span>';
    html += `<h4 style="margin-top:12px;font-size:14px;color:var(--text-muted)">应力校核 ${safe}</h4><table class="result-table">`;
    html += `<tr><td>最大切应力</td><td class="value-num">${sc.max_shear_stress_mpa} MPa</td></tr>`;
    html += `<tr><td>许用应力</td><td class="value-num">${sc.allowable_stress_mpa} MPa</td></tr>`;
    html += `<tr><td>安全系数</td><td class="value-num">${sc.safety_factor}</td></tr>`;
    html += `</table>`;
  }
  
  if (data.deflection) {
    html += `<h4 style="margin-top:12px;font-size:14px;color:var(--text-muted)">变形量</h4><table class="result-table">`;
    html += `<tr><td>变形量 f</td><td class="value-num">${data.deflection.deflection_mm} mm</td></tr>`;
    html += `</table>`;
  }
  
  if (data.note) {
    html += `<p style="margin-top:8px;font-size:12px;color:var(--text-muted)">💡 ${data.note}</p>`;
  }
  
  // 导出按钮
  html += `<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">`;
  html += `<button class="btn-calc" onclick="exportResultPDF('result-${panelId}')" style="font-size:12px;padding:6px 16px;background:var(--accent)">📄 导出PDF</button>`;
  html += `<button class="btn-calc" onclick="copyResult('result-${panelId}')" style="font-size:12px;padding:6px 16px;background:var(--text-muted)">📋 复制结果</button>`;
  html += `</div>`;

  container.innerHTML = html;
  
  // 保存历史
  saveHistory(panelId, data);
}

// ============ 各计算器Logic ============

async function calcVbelt() {
  const d = {
    section: document.getElementById('bv-section').value,
    power: parseFloat(document.getElementById('bv-power').value),
    speed: parseFloat(document.getElementById('bv-speed').value),
    ratio: parseFloat(document.getElementById('bv-ratio').value),
    center_distance: parseFloat(document.getElementById('bv-center').value),
  };
  const r = await apiPost('/api/calculate/belt/vbelt', d);
  displayResult('belt-vbelt', r);
}

async function calcSyncBelt() {
  const d = {
    belt_type: document.getElementById('bs-type').value,
    power: parseFloat(document.getElementById('bs-power').value),
    speed: parseFloat(document.getElementById('bs-speed').value),
    ratio: parseFloat(document.getElementById('bs-ratio').value),
    teeth_small: parseFloat(document.getElementById('bs-z1').value) || null,
    center_distance: parseFloat(document.getElementById('bs-center').value) || null,
  };
  const r = await apiPost('/api/calculate/belt/synchronous', d);
  displayResult('belt-sync', r);
}

async function calcCamProfile() {
  const d = {
    base_radius: parseFloat(document.getElementById('cp-base').value),
    stroke: parseFloat(document.getElementById('cp-stroke').value),
    angle: parseFloat(document.getElementById('cp-angle').value),
    motion_type: document.getElementById('cp-motion').value,
    points: parseInt(document.getElementById('cp-points').value) || 36,
  };
  const r = await apiPost('/api/calculate/cam/profile', d);
  
  // 显示分析结果
  const resultDiv = document.getElementById('result-cam-profile');
  if (r.analysis) {
    let html = '<h3>📊 运动分析</h3><table class="result-table">';
    html += `<tr><td>运动规律</td><td>${r.analysis.motion_desc}</td></tr>`;
    html += `<tr><td>最大速度</td><td class="value-num">${r.analysis.max_velocity.toFixed(3)}</td></tr>`;
    html += `<tr><td>最大加速度</td><td class="value-num">${r.analysis.max_acceleration.toFixed(3)}</td></tr>`;
    html += `<tr><td>Cv 系数</td><td class="value-num">${r.analysis.cv_factor}</td></tr>`;
    html += `<tr><td>Ca 系数</td><td class="value-num">${r.analysis.ca_factor}</td></tr>`;
    html += '</table>';
    resultDiv.innerHTML = html;
  }

  // 画凸轮轮廓图
  const points = r.points || [];
  if (points.length > 0 && typeof Chart !== 'undefined') {
    const ctx = document.getElementById('chart-cam-profile').getContext('2d');
    if (window._camChart) window._camChart.destroy();
    
    // 位移曲线
    window._camChart = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [
          {
            label: '凸轮轮廓 (X-Y)',
            data: points.map(p => ({x: p.x_mm, y: p.y_mm})),
            backgroundColor: 'rgba(37,99,235,0.7)',
            borderColor: 'rgba(37,99,235,0.4)',
            pointRadius: 3,
            showLine: true,
            tension: 0.3,
          },
          {
            label: '基圆',
            data: Array.from({length: 37}, (_, i) => {
              const theta = 2 * Math.PI * i / 36;
              const rb = parseFloat(document.getElementById('cp-base').value) || 50;
              return {x: rb * Math.cos(theta), y: rb * Math.sin(theta)};
            }),
            backgroundColor: 'rgba(220,38,38,0.3)',
            borderColor: 'rgba(220,38,38,0.5)',
            pointRadius: 2,
            showLine: true,
            borderDash: [5, 5],
            fill: false,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { title: { display: true, text: 'X (mm)' } },
          y: { title: { display: true, text: 'Y (mm)' } },
        },
        plugins: {
          legend: { position: 'top' },
        }
      }
    });
  }
}

async function calcIndexer() {
  const d = {
    load_torque: parseFloat(document.getElementById('ci-torque').value),
    stations: parseInt(document.getElementById('ci-stations').value) || 4,
    rpm: parseFloat(document.getElementById('ci-rpm').value),
    index_angle: parseFloat(document.getElementById('ci-index').value),
    dwell_angle: parseFloat(document.getElementById('ci-dwell').value),
    safety: parseFloat(document.getElementById('ci-safety').value) || 1.5,
  };
  const r = await apiPost('/api/calculate/cam/indexer', d);
  displayResult('cam-indexer', r);
}

async function calcDivider() {
  const d = {
    pitch_angle: parseFloat(document.getElementById('cd-pitch').value),
    table_diameter: parseFloat(document.getElementById('cd-diam').value),
    mass: parseFloat(document.getElementById('cd-mass').value),
    rpm: parseFloat(document.getElementById('cd-rpm').value),
  };
  const r = await apiPost('/api/calculate/cam/divider', d);
  displayResult('cam-divider', r);
}

async function calcFit() {
  const d = {
    nominal: parseFloat(document.getElementById('tf-nominal').value),
    hole_spec: document.getElementById('tf-hole').value.trim(),
    shaft_spec: document.getElementById('tf-shaft').value.trim(),
  };
  const r = await apiPost('/api/calculate/tolerance/fit', d);
  
  const container = document.getElementById('result-tolerance-fit');
  if (r.error) { container.innerHTML = `<div class="result-error">❌ ${r.error}</div>`; return; }
  
  let html = `<h3>📐 配合计算结果</h3>`;
  html += `<p style="font-size:16px;font-weight:600;margin:8px 0">φ${d.nominal} ${d.hole_spec}/${d.shaft_spec} = <span style="color:var(--primary)">${r.fit_type}</span></p>`;
  html += `<table class="result-table">`;
  html += `<tr><td>配合类型</td><td class="value-num">${r.fit_type}</td></tr>`;
  html += `<tr><td>最大间隙</td><td class="value-num">${r.max_clearance_um} μm</td></tr>`;
  html += `<tr><td>最小间隙</td><td class="value-num">${r.min_clearance_um} μm</td></tr>`;
  html += `<tr><td>最大过盈</td><td class="value-num">${r.max_interference_um} μm</td></tr>`;
  html += `<tr><td>配合公差</td><td class="value-num">${r.tolerance_um} μm</td></tr>`;
  html += `</table>`;
  
  // 孔轴详细信息
  html += '<div style="display:flex;gap:16px;margin-top:12px">';
  html += '<div style="flex:1;background:#f0f9ff;padding:12px;border-radius:6px"><h4 style="font-size:13px;margin-bottom:6px">🔵 孔 ' + r.hole_info.spec + '</h4>';
  html += `<table class="result-table" style="font-size:12px">`;
  html += `<tr><td>上偏差 ES</td><td>+${r.hole_info.upper_dev_um} μm</td></tr>`;
  html += `<tr><td>下偏差 EI</td><td>${r.hole_info.lower_dev_um >= 0 ? '+' : ''}${r.hole_info.lower_dev_um} μm</td></tr>`;
  html += `<tr><td>尺寸范围</td><td>${r.hole_info.min_size_mm} ~ ${r.hole_info.max_size_mm} mm</td></tr>`;
  html += `</table></div>`;
  html += '<div style="flex:1;background:#fef2f2;padding:12px;border-radius:6px"><h4 style="font-size:13px;margin-bottom:6px">🔴 轴 ' + r.shaft_info.spec + '</h4>';
  html += `<table class="result-table" style="font-size:12px">`;
  html += `<tr><td>上偏差 es</td><td>${r.shaft_info.upper_dev_um}</td></tr>`;
  html += `<tr><td>下偏差 ei</td><td>${r.shaft_info.lower_dev_um}</td></tr>`;
  html += `<tr><td>尺寸范围</td><td>${r.shaft_info.min_size_mm} ~ ${r.shaft_info.max_size_mm} mm</td></tr>`;
  html += `</table></div></div>`;

  // 公差带示意图 (简单ASCII)
  const totalSpan = Math.abs(r.hole_info.upper_dev_um - r.shaft_info.lower_dev_um) || 1;
  const zeroPos = Math.abs(r.shaft_info.lower_dev_um) / totalSpan;
  const hStart = Math.min(r.hole_info.lower_dev_um, r.shaft_info.lower_dev_um);
  const hEnd = Math.max(r.hole_info.upper_dev_um, r.shaft_info.upper_dev_um);
  
  container.innerHTML = html;
}

async function calcShaftTol() {
  const d = {
    nominal: parseFloat(document.getElementById('ts-nominal').value),
    spec: document.getElementById('ts-spec').value.trim(),
  };
  const r = await apiPost('/api/calculate/tolerance/shaft', d);
  displayResult('tolerance-shaft', r);
}

async function calcHoleTol() {
  const d = {
    nominal: parseFloat(document.getElementById('th-nominal').value),
    spec: document.getElementById('th-spec').value.trim(),
  };
  const r = await apiPost('/api/calculate/tolerance/hole', d);
  displayResult('tolerance-hole', r);
}

async function calcBlanking() {
  const d = {
    perimeter: parseFloat(document.getElementById('pb-perimeter').value),
    thickness: parseFloat(document.getElementById('pb-thickness').value),
    shear_strength: parseFloat(document.getElementById('pb-shear').value),
    material_type: document.getElementById('pb-material').value,
  };
  const r = await apiPost('/api/calculate/press/blanking', d);
  
  const container = document.getElementById('result-press-blanking');
  if (r.error) { container.innerHTML = `<div class="result-error">❌ ${r.error}</div>`; return; }
  
  let html = '<h3>✂️ 冲压力计算</h3><table class="result-table">';
  html += `<tr><td>冲裁力</td><td class="value-num">${r.blanking_force_kN} kN (${r.blanking_force_ton} 吨)</td></tr>`;
  html += `<tr><td>卸料力</td><td class="value-num">${r.stripping.stripping_force_kN} kN</td></tr>`;
  html += `<tr><td>推料力</td><td class="value-num">${r.stripping.ejecting_force_kN} kN</td></tr>`;
  html += `<tr><td>顶件力</td><td class="value-num">${r.stripping.pushing_force_kN} kN</td></tr>`;
  html += `<tr><td style="font-weight:700">总压力</td><td class="value-num" style="font-weight:700;color:var(--error)">${r.stripping.total_force_kN} kN (${r.stripping.total_force_ton} 吨)</td></tr>`;
  html += '</table>';
  container.innerHTML = html;
}

async function calcVBend() {
  const d = {
    width: parseFloat(document.getElementById('pv-width').value),
    thickness: parseFloat(document.getElementById('pv-thick').value),
    tensile_strength: parseFloat(document.getElementById('pv-tensile').value),
    die_opening: parseFloat(document.getElementById('pv-die').value),
  };
  const r = await apiPost('/api/calculate/press/vbend', d);
  displayResult('press-vbend', r);
}

async function calcUBend() {
  const d = {
    width: parseFloat(document.getElementById('pu-width').value),
    thickness: parseFloat(document.getElementById('pu-thick').value),
    tensile_strength: parseFloat(document.getElementById('pu-tensile').value),
    die_opening: parseFloat(document.getElementById('pu-die').value),
  };
  const r = await apiPost('/api/calculate/press/ubend', d);
  displayResult('press-ubend', r);
}

async function calcEmboss() {
  const d = {
    area: parseFloat(document.getElementById('pe-area').value),
    tensile_strength: parseFloat(document.getElementById('pe-tensile').value),
  };
  const r = await apiPost('/api/calculate/press/embossing', d);
  displayResult('press-emboss', r);
}

async function calcPressShear() {
  const d = {
    area: parseFloat(document.getElementById('ps-area').value),
    shear_strength: parseFloat(document.getElementById('ps-shear').value),
  };
  const r = await apiPost('/api/calculate/press/shear', d);
  displayResult('press-shear', r);
}

// ============ 推荐配合 ============
async function loadFitRecos() {
  try {
    const r = await fetch('/api/data/fit_recommendations').then(r => r.json());
    const container = document.getElementById('tf-recos');
    if (!container) return;
    let html = '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">';
    r.forEach(f => {
      html += `<span onclick="quickFit('${f.fit}')" style="cursor:pointer;background:#f1f5f9;padding:2px 8px;border-radius:4px;font-size:12px;transition:all 0.15s" onmouseover="this.style.background='#e2e8f0'" onmouseout="this.style.background='#f1f5f9'">${f.fit}</span>`;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch(e) {}
}

function quickFit(spec) {
  const [hole, shaft] = spec.split('/');
  document.getElementById('tf-hole').value = hole;
  document.getElementById('tf-shaft').value = shaft;
  calcFit();
}

// ============ 计算历史 (localStorage) ============

const HISTORY_KEY = 'mech_calc_history';
const MAX_HISTORY = 20;

function saveHistory(panelId, data) {
  try {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    // 提取关键信息
    const entry = {
      id: Date.now(),
      time: new Date().toLocaleString('zh-CN'),
      panelId: panelId,
      summary: getCalcSummary(panelId),
      dataKeys: Object.keys(data).filter(k => typeof data[k] !== 'object').slice(0, 8),
    };
    history.unshift(entry);
    if (history.length > MAX_HISTORY) history.length = MAX_HISTORY;
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderHistory();
  } catch(e) {}
}

function getCalcSummary(panelId) {
  const labels = {
    'belt-vbelt': '三角皮带', 'belt-sync': '同步带',
    'cam-profile': '凸轮轮廓', 'cam-indexer': '分割器选型', 'cam-divider': '分度盘',
    'tolerance-fit': '公差配合', 'tolerance-shaft': '轴公差', 'tolerance-hole': '孔公差',
    'press-blanking': '冲裁力', 'press-vbend': 'V型弯曲', 'press-ubend': 'U型弯曲',
    'press-emboss': '压印力', 'press-shear': '剪切力',
    'gear-basic': '齿轮参数', 'gear-mesh': '齿轮啮合', 'gear-motor': '电机选型', 'gear-rack': '齿条',
    'spring-compression': '弹簧计算',
    'thread-metric': '螺纹计算', 'thread-tapdrill': '攻丝底孔', 'thread-bolt': '螺栓扭矩',
    'chain-sprocket': '链轮参数', 'chain-length': '链条长度', 'chain-conveyor': '输送链',
    'material-search': '材料查询',
  };
  return labels[panelId] || panelId;
}

function renderHistory() {
  const container = document.getElementById('result-tool-history');
  if (!container) return;
  
  try {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    if (history.length === 0) {
      container.innerHTML = '<h3>📋 历史列表</h3><p class="text-muted" style="color:var(--text-muted);font-size:13px">暂无记录</p>';
      return;
    }
    
    let html = `<h3>📋 历史列表 (${history.length})</h3><table class="material-table"><thead><tr><th>时间</th><th>计算内容</th><th>操作</th></tr></thead><tbody>`;
    history.forEach(h => {
      html += `<tr><td style="font-size:12px;color:var(--text-muted)">${h.time}</td>`;
      html += `<td>${h.summary}</td>`;
      html += `<td><button onclick="window.navigateTo('${h.panelId}')" style="border:none;background:var(--primary);color:white;padding:2px 10px;border-radius:4px;cursor:pointer;font-size:12px">打开</button> <button onclick="deleteHistory('${h.id}')" style="border:none;background:#f1f5f9;padding:2px 10px;border-radius:4px;cursor:pointer;font-size:12px">×</button></td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = '<h3>📋 历史列表</h3><p>加载失败</p>';
  }
}

function deleteHistory(id) {
  try {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    const filtered = history.filter(h => h.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
    renderHistory();
  } catch(e) {}
}

function clearHistory() {
  if (confirm('确定清除所有计算历史？')) {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
  }
}

function exportHistoryCSV() {
  try {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    let csv = '时间,计算内容\n';
    history.forEach(h => {
      csv += `${h.time},${h.summary}\n`;
    });
    downloadFile(csv, '计算历史.csv', 'text/csv;charset=utf-8');
  } catch(e) {}
}

// ============ 导出功能 ============

function downloadFile(content, filename, mimeType) {
  const blob = new Blob(['\uFEFF' + content], {type: mimeType});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function exportResultPDF(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  
  // 使用html2canvas打印为图片PDF (无需额外库)
  const content = el.innerText || el.textContent;
  const lines = content.split('\n').filter(l => l.trim());
  let text = '=== 机械设计常用计算表 ===\n';
  text += `导出时间: ${new Date().toLocaleString('zh-CN')}\n`;
  text += '='.repeat(40) + '\n\n';
  lines.forEach(l => { text += l + '\n'; });
  
  downloadFile(text, `机械计算_${Date.now()}.txt`, 'text/plain;charset=utf-8');
  alert('📄 已导出为文本文件（可导入Excel）');
}

function exportResultExcel(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  
  const text = el.innerText || el.textContent;
  const lines = text.split('\n').filter(l => l.trim());
  let csv = '项目,值\n';
  lines.forEach(l => {
    const parts = l.split(/\s{2,}/);
    if (parts.length >= 2) {
      csv += `${parts[0]},${parts.slice(1).join(' ')}\n`;
    }
  });
  downloadFile(csv, `机械计算_${Date.now()}.csv`, 'text/csv;charset=utf-8');
}

function copyResult(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    alert('📋 已复制到剪贴板');
  }).catch(() => {
    // fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    alert('📋 已复制到剪贴板');
  });
}

// ============ 工具函数 ============

async function apiPost(url, data) {
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data),
  });
  return r.json();
}

async function apiGet(url) {
  const r = await fetch(url);
  return r.json();
}
