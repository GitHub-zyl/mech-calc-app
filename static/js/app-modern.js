/**
 * app-modern.js - 现代化 Alpine.js 机械计算前端
 *
 * 设计要点:
 * 1. 数据驱动: CALCULATORS 注册表描述每个计算器的字段/端点/方法
 * 2. 单一入口: 全部计算通过 calcApi() 走统一 API (后端 v2)
 * 3. 历史记录: 本地内存 + (Phase 2) localStorage 持久化
 * 4. 分类树: 由 /api/meta/categories 提供
 *
 * 使用:
 *   <div x-data="mechApp()" x-init="init()">...</div>
 */
function mechApp() {
  return {
    // ===== 状态 =====
    categories: [],
    activeCategory: null,
    activeCalc: null,
    search: '',
    form: {},
    result: null,
    lastError: '',
    loading: false,
    history: [],

    // ===== 生命周期 =====
    async init() {
      try {
        const r = await fetch('/api/meta/categories');
        const j = await r.json();
        this.categories = j.data || [];
      } catch (e) {
        this.lastError = '加载分类树失败: ' + e.message;
      }
    },

    // ===== 计算方法 =====
    filteredCategories() {
      if (!this.search) return this.categories;
      const q = this.search.toLowerCase();
      return this.categories.filter(c =>
        c.name_zh.toLowerCase().includes(q) ||
        c.name_en.toLowerCase().includes(q) ||
        (c.id || '').toLowerCase().includes(q)
      );
    },

    currentCategoryName() {
      const c = this.categories.find(x => x.id === this.activeCategory);
      return c ? c.name_zh : '';
    },

    calculatorsInCategory() {
      return (CALCULATORS[this.activeCategory] || []).filter(c => {
        if (!this.search) return true;
        const q = this.search.toLowerCase();
        return c.title.toLowerCase().includes(q) ||
               (c.description || '').toLowerCase().includes(q);
      });
    },

    currentCalc() {
      if (!this.activeCalc) return null;
      for (const list of Object.values(CALCULATORS)) {
        const c = list.find(x => x.id === this.activeCalc);
        if (c) return c;
      }
      return null;
    },

    // ===== 计算 =====
    async runCalc() {
      const calc = this.currentCalc();
      if (!calc) return;
      this.loading = true;
      this.lastError = '';
      this.result = null;
      try {
        // 收集有效输入
        const payload = {};
        for (const f of calc.fields || []) {
          const v = this.form[f.name];
          if (v !== '' && v !== null && v !== undefined) payload[f.name] = v;
        }
        const r = await fetch(calc.endpoint, {
          method: calc.method || 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const j = await r.json();
        if (j.status === 'error') {
          this.lastError = j.message || '请求失败';
        } else {
          this.result = j.data;
        }
        // 记录历史
        this.history.push({
          ts: Date.now(),
          calc: calc.title,
          endpoint: calc.endpoint,
          input: payload,
          result: this.result,
        });
      } catch (e) {
        this.lastError = '网络错误: ' + e.message;
      } finally {
        this.loading = false;
      }
    },
  };
}


// ============================================================
// 计算器注册表
// ============================================================
//
// 每条配置:
//   id:       唯一标识
//   title:    显示名称
//   description: 简短描述
//   endpoint: API 路径 (相对 v2 后端)
//   method:   HTTP 方法 (默认 POST)
//   fields:   表单字段列表 { name, label, type?, step? }
//
// 添加新计算器: 只需在对应分类下追加一项, 无需改 HTML 或 JS 逻辑.
// ============================================================
const CALCULATORS = {
  geometry: [
    { id: 'circle-area', title: '圆面积', description: 'A = π·D²/4',
      endpoint: '/api/calc/geometry/circle-area',
      fields: [{ name: 'd_mm', label: '直径 D (mm)' }] },
  ],
  transmission: [
    { id: 'gear-spur', title: '直齿轮参数', description: '由模数/齿数计算齿轮几何尺寸',
      endpoint: '/api/calc/gear/spur',
      fields: [
        { name: 'module', label: '模数 m' },
        { name: 'teeth', label: '齿数 z' },
        { name: 'pressure_angle', label: '压力角 α (°)', step: 'any' },
        { name: 'modification_coefficient', label: '变位系数 x', step: 'any' },
      ] },
    { id: 'gear-mesh', title: '齿轮副啮合', description: '中心距/啮合角/重合度等',
      endpoint: '/api/calc/gear/mesh',
      fields: [
        { name: 'module', label: '模数 m' },
        { name: 'teeth1', label: '小齿轮齿数 z₁' },
        { name: 'teeth2', label: '大齿轮齿数 z₂' },
      ] },
    { id: 'gear-motor', title: '齿轮减速机选型', description: '由功率/转速/传动比选减速机',
      endpoint: '/api/calc/gear/motor',
      fields: [
        { name: 'power_kw', label: '功率 P (kW)' },
        { name: 'n1_rpm', label: '输入转速 n₁ (rpm)' },
        { name: 'ratio', label: '传动比 i' },
      ] },
    { id: 'belt-vbelt', title: 'V 带传动', description: 'V 带选型与功率校核',
      endpoint: '/api/calc/belt/vbelt',
      fields: [
        { name: 'power_kw', label: '功率 P (kW)' },
        { name: 'n1_rpm', label: '小带轮转速 n₁' },
        { name: 'd1_mm', label: '小带轮直径 d₁ (mm)' },
        { name: 'ratio', label: '传动比 i' },
      ] },
    { id: 'chain-sprocket', title: '链轮参数', description: '链轮齿数/分度圆/中心距',
      endpoint: '/api/calc/chain/sprocket',
      fields: [
        { name: 'teeth', label: '齿数 z' },
        { name: 'pitch_mm', label: '节距 p (mm)' },
      ] },
  ],
  shaft_system: [
    { id: 'shaft-torsion', title: '轴扭转强度', description: '由扭矩计算轴径',
      endpoint: '/api/calc/shaft/torsion',
      fields: [
        { name: 'T_Nmm', label: '扭矩 T (N·mm)' },
        { name: 'tau_allow_mpa', label: '许用切应力 [τ] (MPa)' },
      ] },
    { id: 'bearing-life', title: '轴承寿命', description: 'L10h 寿命计算',
      endpoint: '/api/calc/bearing/life',
      fields: [
        { name: 'C_kN', label: '额定动载荷 C (kN)' },
        { name: 'P_kN', label: '当量动载荷 P (kN)' },
        { name: 'n_rpm', label: '转速 n (rpm)' },
      ] },
  ],
  fasteners: [
    { id: 'thread-metric', title: '公制螺纹', description: 'M 螺纹几何参数',
      endpoint: '/api/calc/thread/metric',
      fields: [
        { name: 'nominal_d', label: '公称直径 d (mm)' },
        { name: 'pitch', label: '螺距 P (mm)', step: 'any' },
      ] },
    { id: 'thread-preload', title: '螺栓预紧力', description: '由性能等级查预紧力',
      endpoint: '/api/calc/thread/preload',
      fields: [
        { name: 'd_mm', label: '螺纹公称直径 d (mm)' },
        { name: 'grade', label: '性能等级 (如 8.8)' },
      ] },
  ],
  tolerance: [
    { id: 'tolerance-shaft', title: '轴公差', description: '由基本偏差代号查上下偏差',
      endpoint: '/api/calc/tolerance/shaft',
      fields: [
        { name: 'nominal_mm', label: '基本尺寸 (mm)' },
        { name: 'tolerance_spec', label: '公差代号 (如 h6)' },
      ] },
    { id: 'tolerance-hole', title: '孔公差', description: '由基本偏差代号查上下偏差',
      endpoint: '/api/calc/tolerance/hole',
      fields: [
        { name: 'nominal_mm', label: '基本尺寸 (mm)' },
        { name: 'tolerance_spec', label: '公差代号 (如 H7)' },
      ] },
    { id: 'tolerance-fit', title: '配合公差', description: '由孔轴公差代号查配合性质',
      endpoint: '/api/calc/tolerance/fit',
      fields: [
        { name: 'nominal_mm', label: '基本尺寸 (mm)' },
        { name: 'hole_spec', label: '孔公差代号 (如 H7)' },
        { name: 'shaft_spec', label: '轴公差代号 (如 g6)' },
      ] },
  ],
  materials: [
    { id: 'material-search', title: '材料查询', description: '搜索工程材料',
      endpoint: '/api/data/materials',
      method: 'GET',
      fields: [{ name: 'q', label: '搜索关键词' }] },
  ],
  surface: [
    { id: 'surface-ra-rz', title: 'Ra→Rz 换算', description: '粗糙度参数换算',
      endpoint: '/api/calc/surface/ra-to-rz',
      fields: [{ name: 'Ra_um', label: 'Ra (μm)' }] },
  ],
  springs: [
    { id: 'spring-compression', title: '压缩弹簧', description: '刚度/旋绕比/应力校核',
      endpoint: '/api/calc/spring/compression',
      fields: [
        { name: 'wire_diameter', label: '线径 d (mm)' },
        { name: 'mean_diameter', label: '中径 Dm (mm)' },
        { name: 'coils', label: '有效圈数 n' },
        { name: 'G', label: '切变模量 G (MPa)' },
      ] },
  ],
  fluid: [
    { id: 'pneumatic-force', title: '气缸力', description: 'F = p·A',
      endpoint: '/api/calc/pneumatic/force',
      fields: [
        { name: 'pressure_mpa', label: '工作压力 p (MPa)' },
        { name: 'bore_mm', label: '缸径 D (mm)' },
        { name: 'rod_mm', label: '杆径 d (mm)' },
      ] },
    { id: 'hydraulic-pipe-loss', title: '液压管损', description: '沿程压力损失',
      endpoint: '/api/calc/hydraulic/pipe-pressure-loss',
      fields: [
        { name: 'flow_lpm', label: '流量 Q (L/min)' },
        { name: 'inner_diam_mm', label: '内径 d (mm)' },
        { name: 'length_m', label: '管长 L (m)' },
      ] },
  ],
  press: [
    { id: 'press-blanking', title: '冲裁力', description: 'F = K·L·t·τ',
      endpoint: '/api/calc/press/blanking',
      fields: [
        { name: 'perimeter_mm', label: '冲裁周边 L (mm)' },
        { name: 'thickness_mm', label: '材料厚度 t (mm)' },
        { name: 'shear_strength_mpa', label: '抗剪强度 τ (MPa)' },
      ] },
  ],
  brake: [
    { id: 'brake-disc', title: '盘式制动', description: '制动力矩/反推摩擦系数',
      endpoint: '/api/calc/brake/disc',
      fields: [
        { name: 'T_Nm', label: '制动力矩 T (N·m)' },
        { name: 'outer_radius_mm', label: '外半径 R_o (mm)' },
        { name: 'inner_radius_mm', label: '内半径 R_i (mm)' },
        { name: 'pressure_mpa', label: '比压 p (MPa)' },
        { name: 'num_friction_surfaces', label: '摩擦面数 n' },
      ] },
  ],
  mechanics: [],
  units: [
    { id: 'units-convert', title: '单位换算', description: '任意单位间换算',
      endpoint: '/api/units/convert',
      fields: [
        { name: 'category', label: '类别 (如 length)' },
        { name: 'from', label: '原单位' },
        { name: 'to', label: '目标单位' },
        { name: 'value', label: '数值' },
      ] },
  ],
};
