/**
 * 机械设计常用计算表 - 前端交互
 */

// ============ 导航定义 ============

const NAV_ITEMS = [
  { category: '材料数据', items: [
    { id: 'material-search', label: '🔍 材料查询', panel: 'material-search' },
  ]},
  { category: '齿轮传动', items: [
    { id: 'gear-basic', label: '⚙ 齿轮基本参数', panel: 'gear-basic' },
    { id: 'gear-mesh', label: '⚙ 齿轮啮合计算', panel: 'gear-mesh' },
    { id: 'gear-motor', label: '🔌 电机选型计算', panel: 'gear-motor' },
    { id: 'gear-rack', label: '齿条传动计算', panel: 'gear-rack' },
  ]},
  { category: '弹簧', items: [
    { id: 'spring-compression', label: '〰️ 压缩弹簧计算', panel: 'spring-compression' },
  ]},
  { category: '螺纹/紧固', items: [
    { id: 'thread-metric', label: '🔩 公制螺纹计算', panel: 'thread-metric' },
    { id: 'thread-tapdrill', label: '🔩 攻丝底孔计算', panel: 'thread-tapdrill' },
    { id: 'thread-bolt', label: '🔩 螺栓扭矩计算', panel: 'thread-bolt' },
  ]},
  { category: '链传动', items: [
    { id: 'chain-sprocket', label: '⛓ 链轮参数', panel: 'chain-sprocket' },
    { id: 'chain-length', label: '⛓ 链条长度计算', panel: 'chain-length' },
    { id: 'chain-conveyor', label: '⛓ 输送链张力', panel: 'chain-conveyor' },
  ]},
];

// ============ 计算器面板HTML生成 ============

const PANEL_TEMPLATES = {
  'gear-basic': `
    <div class="panel-header">
      <h2>⚙ 直齿圆柱齿轮基本参数计算</h2>
      <p>计算分度圆、齿顶圆、齿根圆、齿厚等基本参数</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>模数 m</label>
          <input type="number" id="gb-module" step="0.1" value="3">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>齿数 z</label>
          <input type="number" id="gb-teeth" step="1" value="20">
          <div class="unit">—</div>
        </div>
        <div class="form-group">
          <label>压力角 α</label>
          <input type="number" id="gb-alpha" step="0.5" value="20">
          <div class="unit">°</div>
        </div>
        <div class="form-group">
          <label>变位系数 x</label>
          <input type="number" id="gb-x" step="0.1" value="0">
          <div class="unit">—</div>
        </div>
      </div>
      <button class="btn-calc" onclick="calcGearBasic()">计算</button>
    </div>
    <div id="result-gear-basic" class="calc-result" style="display:none"></div>
  `,

  'gear-mesh': `
    <div class="panel-header">
      <h2>⚙ 齿轮啮合计算</h2>
      <p>计算一对齿轮啮合的中心距、传动比</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>模数 m</label>
          <input type="number" id="gm-module" step="0.1" value="3">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>小齿轮齿数 z₁</label>
          <input type="number" id="gm-z1" step="1" value="20">
        </div>
        <div class="form-group">
          <label>大齿轮齿数 z₂</label>
          <input type="number" id="gm-z2" step="1" value="60">
        </div>
        <div class="form-group">
          <label>压力角</label>
          <input type="number" id="gm-alpha" step="0.5" value="20">
          <div class="unit">°</div>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>变位系数 x₁</label>
          <input type="number" id="gm-x1" step="0.1" value="0">
        </div>
        <div class="form-group">
          <label>变位系数 x₂</label>
          <input type="number" id="gm-x2" step="0.1" value="0">
        </div>
      </div>
      <button class="btn-calc" onclick="calcGearMesh()">计算</button>
    </div>
    <div id="result-gear-mesh" class="calc-result" style="display:none"></div>
  `,

  'gear-motor': `
    <div class="panel-header">
      <h2>🔌 齿轮传动电机选型</h2>
      <p>根据功率、转速、传动比计算输出扭矩和转速</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>所需功率 P</label>
          <input type="number" id="gmotor-power" step="0.1" value="1.5">
          <div class="unit">kW</div>
        </div>
        <div class="form-group">
          <label>输入转速 n₁</label>
          <input type="number" id="gmotor-speed" step="1" value="1450">
          <div class="unit">rpm</div>
        </div>
        <div class="form-group">
          <label>传动比 i</label>
          <input type="number" id="gmotor-ratio" step="0.1" value="3">
        </div>
        <div class="form-group">
          <label>传动效率 η</label>
          <input type="number" id="gmotor-eff" step="0.01" value="0.95">
        </div>
      </div>
      <button class="btn-calc" onclick="calcGearMotor()">计算</button>
    </div>
    <div id="result-gear-motor" class="calc-result" style="display:none"></div>
  `,

  'gear-rack': `
    <div class="panel-header">
      <h2>齿条传动计算</h2>
      <p>齿轮齿条传动 — 每转进给量、扭矩、功率</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>模数 m</label>
          <input type="number" id="gr-module" step="0.5" value="2">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>齿轮齿数 z</label>
          <input type="number" id="gr-teeth" step="1" value="20">
        </div>
        <div class="form-group">
          <label>驱动力 F</label>
          <input type="number" id="gr-force" step="10" value="500">
          <div class="unit">N</div>
        </div>
        <div class="form-group">
          <label>移动速度 v</label>
          <input type="number" id="gr-speed" step="0.1" value="0.5">
          <div class="unit">m/s</div>
        </div>
      </div>
      <button class="btn-calc" onclick="calcRack()">计算</button>
    </div>
    <div id="result-gear-rack" class="calc-result" style="display:none"></div>
  `,

  'spring-compression': `
    <div class="panel-header">
      <h2>〰️ 圆柱螺旋压缩弹簧计算</h2>
      <p>计算弹簧刚度、应力校核、变形量</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>线径 d</label>
          <input type="number" id="sp-wire" step="0.1" value="4">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>中径 Dm</label>
          <input type="number" id="sp-mean" step="0.1" value="30">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>有效圈数 n</label>
          <input type="number" id="sp-coils" step="0.5" value="8">
        </div>
        <div class="form-group">
          <label>材料</label>
          <select id="sp-material">
            <option value="弹簧钢">弹簧钢 (60Si2Mn)</option>
            <option value="不锈钢">不锈钢 (1Cr18Ni9)</option>
            <option value="铜合金">铜合金</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>工作载荷 F（可选）</label>
          <input type="number" id="sp-force" step="10" value="200">
          <div class="unit">N</div>
        </div>
      </div>
      <button class="btn-calc" onclick="calcSpring()">计算</button>
    </div>
    <div id="result-spring-compression" class="calc-result" style="display:none"></div>
  `,

  'thread-metric': `
    <div class="panel-header">
      <h2>🔩 公制螺纹基本尺寸计算</h2>
      <p>计算螺纹中径、小径、牙高等 (ISO 68 标准)</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>公称直径 D</label>
          <input type="number" id="th-diam" step="0.5" value="12">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>螺距 P</label>
          <input type="number" id="th-pitch" step="0.05" value="1.75">
          <div class="unit">mm（留空自动推断标准螺距）</div>
        </div>
      </div>
      <button class="btn-calc" onclick="calcThread()">计算</button>
    </div>
    <div id="result-thread-metric" class="calc-result" style="display:none"></div>
  `,

  'thread-tapdrill': `
    <div class="panel-header">
      <h2>🔩 攻丝底孔直径计算</h2>
      <p>根据螺纹规格计算推荐的钻头直径（按材料分类）</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>螺纹规格</label>
          <input type="text" id="td-spec" value="M8">
          <div class="unit">如 M6, M8x1, M12x1.5</div>
        </div>
      </div>
      <button class="btn-calc" onclick="calcTapDrill()">计算</button>
    </div>
    <div id="result-thread-tapdrill" class="calc-result" style="display:none"></div>
  `,

  'thread-bolt': `
    <div class="panel-header">
      <h2>🔩 螺栓预紧力与扭矩计算</h2>
      <p>根据螺栓直径和性能等级计算推荐拧紧扭矩</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>螺栓直径</label>
          <input type="number" id="bt-diam" step="1" value="12">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>性能等级</label>
          <select id="bt-grade">
            <option value="4.6">4.6</option>
            <option value="4.8">4.8</option>
            <option value="5.6">5.6</option>
            <option value="5.8">5.8</option>
            <option value="8.8" selected>8.8</option>
            <option value="9.8">9.8</option>
            <option value="10.9">10.9</option>
            <option value="12.9">12.9</option>
          </select>
        </div>
      </div>
      <button class="btn-calc" onclick="calcBolt()">计算</button>
    </div>
    <div id="result-thread-bolt" class="calc-result" style="display:none"></div>
  `,

  'chain-sprocket': `
    <div class="panel-header">
      <h2>⛓ 滚子链链轮参数计算</h2>
      <p>计算链轮分度圆、齿顶圆、齿根圆直径</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>节距 p</label>
          <input type="number" id="cs-pitch" step="0.1" value="12.7">
          <div class="unit">mm（08A=12.7, 10A=15.875）</div>
        </div>
        <div class="form-group">
          <label>齿数 z</label>
          <input type="number" id="cs-teeth" step="1" value="19">
        </div>
      </div>
      <button class="btn-calc" onclick="calcSprocket()">计算</button>
    </div>
    <div id="result-chain-sprocket" class="calc-result" style="display:none"></div>
  `,

  'chain-length': `
    <div class="panel-header">
      <h2>⛓ 链条长度计算</h2>
      <p>计算所需链条节数和长度</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>节距 p</label>
          <input type="number" id="cl-pitch" step="0.1" value="12.7">
          <div class="unit">mm</div>
        </div>
        <div class="form-group">
          <label>小链轮齿数 z₁</label>
          <input type="number" id="cl-z1" step="1" value="17">
        </div>
        <div class="form-group">
          <label>大链轮齿数 z₂</label>
          <input type="number" id="cl-z2" step="1" value="51">
        </div>
        <div class="form-group">
          <label>中心距 a</label>
          <input type="number" id="cl-center" step="10" value="500">
          <div class="unit">mm</div>
        </div>
      </div>
      <button class="btn-calc" onclick="calcChainLength()">计算</button>
    </div>
    <div id="result-chain-length" class="calc-result" style="display:none"></div>
  `,

  'chain-conveyor': `
    <div class="panel-header">
      <h2>⛓ 输送链张力计算</h2>
      <p>倍速链/输送链的摩擦力和所需功率</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group">
          <label>输送物总质量</label>
          <input type="number" id="cc-mass" step="10" value="100">
          <div class="unit">kg</div>
        </div>
        <div class="form-group">
          <label>输送速度</label>
          <input type="number" id="cc-speed" step="0.1" value="0.5">
          <div class="unit">m/s</div>
        </div>
        <div class="form-group">
          <label>输送长度</label>
          <input type="number" id="cc-length" step="1" value="5">
          <div class="unit">m</div>
        </div>
        <div class="form-group">
          <label>摩擦系数</label>
          <input type="number" id="cc-friction" step="0.01" value="0.15">
        </div>
      </div>
      <button class="btn-calc" onclick="calcConveyor()">计算</button>
    </div>
    <div id="result-chain-conveyor" class="calc-result" style="display:none"></div>
  `,

  'material-search': `
    <div class="panel-header">
      <h2>📦 工程材料查询</h2>
      <p>搜索常用工程材料的弹性模量、密度、泊松比等属性</p>
    </div>
    <div class="calc-form">
      <div class="form-row">
        <div class="form-group" style="flex:3">
          <label>搜索材料名称</label>
          <input type="text" id="mat-query" placeholder="输入材料名称关键词..." onkeyup="if(event.key==='Enter')searchMaterial()">
        </div>
        <div class="form-group" style="flex:1">
          <label>&nbsp;</label>
          <button class="btn-calc" onclick="searchMaterial()" style="margin-top:0">搜索</button>
        </div>
      </div>
    </div>
    <div id="result-material-search" class="calc-result" style="display:none"></div>
  `,
};

// ============ 初始化 ============

function init() {
  renderNav();
  renderPanels();
  // 默认选中第一个导航
  const first = NAV_ITEMS[0]?.items[0];
  if (first) navigateTo(first.id);
}

function renderNav() {
  const ul = document.getElementById('nav-list');
  ul.innerHTML = '';
  NAV_ITEMS.forEach(group => {
    const li = document.createElement('li');
    li.className = 'nav-category';
    li.textContent = group.category;
    ul.appendChild(li);
    group.items.forEach(item => {
      const li2 = document.createElement('li');
      li2.className = 'nav-item';
      li2.dataset.id = item.id;
      li2.textContent = item.label;
      li2.onclick = () => navigateTo(item.id);
      ul.appendChild(li2);
    });
  });
}

function renderPanels() {
  const container = document.getElementById('calculator-panels');
  container.innerHTML = '';
  Object.entries(PANEL_TEMPLATES).forEach(([id, html]) => {
    const div = document.createElement('div');
    div.className = 'calculator-panel';
    div.id = `panel-${id}`;
    div.innerHTML = html;
    container.appendChild(div);
  });
}

function navigateTo(id) {
  // 更新导航高亮
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const navItem = document.querySelector(`.nav-item[data-id="${id}"]`);
  if (navItem) navItem.classList.add('active');

  // 找面板
  const item = findNavItem(id);
  if (!item) return;
  const panelId = item.panel;

  // 切换面板
  document.querySelectorAll('.calculator-panel').forEach(el => el.classList.remove('active'));
  const panel = document.getElementById(`panel-${panelId}`);
  if (panel) panel.classList.add('active');

  // 隐藏欢迎页
  document.getElementById('welcome').style.display = 'none';
}

function findNavItem(id) {
  for (const group of NAV_ITEMS) {
    const found = group.items.find(i => i.id === id);
    if (found) return found;
  }
  return null;
}

// ============ 导航搜索 ============

function filterNav() {
  const q = document.getElementById('nav-filter').value.toLowerCase();
  document.querySelectorAll('.nav-item').forEach(el => {
    const label = el.textContent.toLowerCase();
    el.style.display = label.includes(q) ? '' : 'none';
  });
  document.querySelectorAll('.nav-category').forEach(el => {
    const next = el.nextElementSibling;
    const hasVisible = next && next.classList.contains('nav-item') && next.style.display !== 'none';
    el.style.display = hasVisible ? '' : 'none';
  });
}

// ============ 工具函数 ============

function buildResultTable(data, title) {
  if (!data || data.error) {
    return `<div class="result-error">${data?.error || '计算错误'}</div>`;
  }
  let html = `<h3>${title}</h3><table class="result-table">`;
  for (const [key, val] of Object.entries(data)) {
    const label = key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
    let value = val;
    if (typeof val === 'number') {
      value = `<span class="value-num">${val.toFixed(4).replace(/\.?0+$/, '')}</span>`;
    } else if (val === true) {
      value = '<span class="result-success">✓ 合格</span>';
    } else if (val === false) {
      value = '<span class="result-error">✗ 不合格</span>';
    }
    html += `<tr><td>${label}</td><td>${value}</td></tr>`;
  }
  html += '</table>';
  return html;
}

async function apiPost(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

async function apiGet(url) {
  const res = await fetch(url);
  return res.json();
}

// ============ 各计算器函数 ============

async function calcGearBasic() {
  const data = {
    module: parseFloat(document.getElementById('gb-module').value),
    teeth: parseFloat(document.getElementById('gb-teeth').value),
    pressure_angle: parseFloat(document.getElementById('gb-alpha').value),
    modification_coefficient: parseFloat(document.getElementById('gb-x').value),
  };
  const result = await apiPost('/api/calculate/gear/spur', data);
  document.getElementById('result-gear-basic').style.display = 'block';
  document.getElementById('result-gear-basic').innerHTML = buildResultTable(result, '📊 齿轮参数计算结果');
}

async function calcGearMesh() {
  const data = {
    module: parseFloat(document.getElementById('gm-module').value),
    teeth1: parseFloat(document.getElementById('gm-z1').value),
    teeth2: parseFloat(document.getElementById('gm-z2').value),
    pressure_angle: parseFloat(document.getElementById('gm-alpha').value),
    x1: parseFloat(document.getElementById('gm-x1').value),
    x2: parseFloat(document.getElementById('gm-x2').value),
  };
  const result = await apiPost('/api/calculate/gear/mesh', data);
  document.getElementById('result-gear-mesh').style.display = 'block';

  if (result.gear1 && result.gear2) {
    let html = '<h3>📊 齿轮啮合计算结果</h3>';
    html += '<table class="result-table">';
    html += `<tr><td>传动比 i</td><td>${result.transmission_ratio}</td></tr>`;
    html += `<tr><td>标准中心距 a</td><td>${result.center_distance} mm</td></tr>`;
    html += `<tr><td>实际中心距 a'</td><td>${result.actual_center_distance} mm</td></tr>`;
    html += `<tr><td>啮合角 α'</td><td>${result.working_pressure_angle_deg}°</td></tr>`;
    html += '</table>';
    html += '<h4 style="margin-top:12px;color:var(--text-muted)">小齿轮</h4>';
    html += buildResultTable(result.gear1, '');
    html += '<h4 style="margin-top:12px;color:var(--text-muted)">大齿轮</h4>';
    html += buildResultTable(result.gear2, '');
    document.getElementById('result-gear-mesh').innerHTML = html;
  } else {
    document.getElementById('result-gear-mesh').innerHTML = buildResultTable(result, '');
  }
}

async function calcGearMotor() {
  const data = {
    power: parseFloat(document.getElementById('gmotor-power').value),
    speed: parseFloat(document.getElementById('gmotor-speed').value),
    ratio: parseFloat(document.getElementById('gmotor-ratio').value),
    efficiency: parseFloat(document.getElementById('gmotor-eff').value),
  };
  const result = await apiPost('/api/calculate/gear/motor', data);
  document.getElementById('result-gear-motor').style.display = 'block';
  document.getElementById('result-gear-motor').innerHTML = buildResultTable(result, '📊 电机选型计算结果');
}

async function calcRack() {
  const data = {
    module: parseFloat(document.getElementById('gr-module').value),
    teeth: parseFloat(document.getElementById('gr-teeth').value),
    force: parseFloat(document.getElementById('gr-force').value),
    speed: parseFloat(document.getElementById('gr-speed').value),
  };
  const result = await apiPost('/api/calculate/gear/rack', data);
  document.getElementById('result-gear-rack').style.display = 'block';
  document.getElementById('result-gear-rack').innerHTML = buildResultTable(result, '📊 齿条传动计算结果');
}

async function calcSpring() {
  const data = {
    wire_diameter: parseFloat(document.getElementById('sp-wire').value),
    mean_diameter: parseFloat(document.getElementById('sp-mean').value),
    coils: parseFloat(document.getElementById('sp-coils').value),
    material: document.getElementById('sp-material').value,
    force: parseFloat(document.getElementById('sp-force').value) || null,
  };
  const result = await apiPost('/api/calculate/spring/compression', data);
  document.getElementById('result-spring-compression').style.display = 'block';

  if (result.stress_check) {
    let html = buildResultTable(result, '📊 弹簧参数');
    html += '<hr style="margin:12px 0;border:none;border-top:1px solid var(--border)">';
    html += buildResultTable(result.stress_check, '🔍 应力校核');
    if (result.deflection) {
      html += '<hr style="margin:12px 0;border:none;border-top:1px solid var(--border)">';
      html += buildResultTable(result.deflection, '📏 变形量');
    }
    document.getElementById('result-spring-compression').innerHTML = html;
  } else {
    document.getElementById('result-spring-compression').innerHTML = buildResultTable(result, '📊 弹簧参数');
  }
}

async function calcThread() {
  const data = {
    nominal_diameter: parseFloat(document.getElementById('th-diam').value),
    pitch: parseFloat(document.getElementById('th-pitch').value) || null,
  };
  const result = await apiPost('/api/calculate/thread/metric', data);
  document.getElementById('result-thread-metric').style.display = 'block';
  document.getElementById('result-thread-metric').innerHTML = buildResultTable(result, '📊 螺纹尺寸计算结果');
}

async function calcTapDrill() {
  const data = {
    thread_spec: document.getElementById('td-spec').value,
  };
  const result = await apiPost('/api/calculate/thread/tapdrill', data);
  document.getElementById('result-thread-tapdrill').style.display = 'block';
  document.getElementById('result-thread-tapdrill').innerHTML = buildResultTable(result, '📊 攻丝底孔直径');
}

async function calcBolt() {
  const data = {
    diameter: parseFloat(document.getElementById('bt-diam').value),
    grade: document.getElementById('bt-grade').value,
  };
  const result = await apiPost('/api/calculate/thread/bolt', data);
  document.getElementById('result-thread-bolt').style.display = 'block';
  document.getElementById('result-thread-bolt').innerHTML = buildResultTable(result, '📊 螺栓扭矩计算结果');
}

async function calcSprocket() {
  const data = {
    pitch: parseFloat(document.getElementById('cs-pitch').value),
    teeth: parseFloat(document.getElementById('cs-teeth').value),
  };
  const result = await apiPost('/api/calculate/chain/sprocket', data);
  document.getElementById('result-chain-sprocket').style.display = 'block';
  document.getElementById('result-chain-sprocket').innerHTML = buildResultTable(result, '📊 链轮参数计算结果');
}

async function calcChainLength() {
  const data = {
    pitch: parseFloat(document.getElementById('cl-pitch').value),
    teeth1: parseFloat(document.getElementById('cl-z1').value),
    teeth2: parseFloat(document.getElementById('cl-z2').value),
    center_distance: parseFloat(document.getElementById('cl-center').value),
  };
  const result = await apiPost('/api/calculate/chain/length', data);
  document.getElementById('result-chain-length').style.display = 'block';
  document.getElementById('result-chain-length').innerHTML = buildResultTable(result, '📊 链条长度计算结果');
}

async function calcConveyor() {
  const data = {
    mass: parseFloat(document.getElementById('cc-mass').value),
    speed: parseFloat(document.getElementById('cc-speed').value),
    length: parseFloat(document.getElementById('cc-length').value),
    friction: parseFloat(document.getElementById('cc-friction').value),
  };
  const result = await apiPost('/api/calculate/chain/conveyor', data);
  document.getElementById('result-chain-conveyor').style.display = 'block';
  document.getElementById('result-chain-conveyor').innerHTML = buildResultTable(result, '📊 输送链张力计算结果');
}

// ============ 材料搜索 ============

async function searchMaterial() {
  const q = document.getElementById('mat-query').value.trim();
  if (!q) return;
  
  const results = await apiGet(`/api/material/search?q=${encodeURIComponent(q)}`);
  const container = document.getElementById('result-material-search');
  container.style.display = 'block';
  
  if (results.length === 0) {
    container.innerHTML = `<div class="result-error">未找到匹配"${q}"的材料</div>`;
    return;
  }
  
  let html = `<h3>📦 找到 ${results.length} 种材料</h3>`;
  html += '<div class="material-table-wrap"><table class="material-table">';
  html += '<thead><tr><th>材料名称</th><th>弹性模量(GPa)</th><th>密度(kg/m³)</th><th>泊松比</th><th>抗拉(MPa)</th><th>屈服(MPa)</th></tr></thead><tbody>';
  
  results.forEach(m => {
    html += `<tr onclick="showMaterialDetail('${m.name}')" style="cursor:pointer">`;
    html += `<td>${m.name}</td>`;
    html += `<td>${m.elastic_modulus ? (m.elastic_modulus / 1e9).toFixed(1) : '-'}</td>`;
    html += `<td>${m.density || '-'}</td>`;
    html += `<td>${m.poisson_ratio || '-'}</td>`;
    html += `<td>${m.tensile_strength_mpa || '-'}</td>`;
    html += `<td>${m.yield_strength_mpa || '-'}</td>`;
    html += '</tr>';
  });
  
  html += '</tbody></table></div>';
  container.innerHTML = html;
}

async function showMaterialDetail(name) {
  const data = await apiGet(`/api/material/info?name=${encodeURIComponent(name)}`);
  if (data.error) return;
  
  const container = document.getElementById('result-material-search');
  let html = `<h3>📋 ${data.name} 详细属性</h3><table class="result-table">`;
  const fields = [
    ['弹性模量', data.elastic_modulus ? `${(data.elastic_modulus / 1e9).toFixed(1)} GPa` : '-'],
    ['泊松比', data.poisson_ratio ?? '-'],
    ['密度', data.density ? `${data.density} kg/m³` : '-'],
    ['抗剪模量', data.shear_modulus ? `${(data.shear_modulus / 1e9).toFixed(1)} GPa` : '-'],
    ['抗拉强度', data.tensile_strength_mpa ? `${data.tensile_strength_mpa} MPa` : '-'],
    ['屈服强度', data.yield_strength_mpa ? `${data.yield_strength_mpa} MPa` : '-'],
    ['热膨胀系数', data.thermal_expansion ?? '-'],
    ['比热容', data.specific_heat ? `${data.specific_heat} J/(kg·K)` : '-'],
    ['热导率', data.thermal_conductivity ? `${data.thermal_conductivity} W/(m·K)` : '-'],
  ];
  fields.forEach(([label, val]) => {
    html += `<tr><td>${label}</td><td>${val}</td></tr>`;
  });
  html += '</table>';
  html += '<button class="btn-calc" onclick="searchMaterial()" style="margin-top:12px">← 返回列表</button>';
  container.innerHTML = html;
}

// ============ 启动 ============
document.addEventListener('DOMContentLoaded', init);
