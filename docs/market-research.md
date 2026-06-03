# 主流机械设计计算软件市场调研

> 调研日期: 2026-06-03
> 目的: 借鉴主流产品功能特点,作为本工具功能扩展与分类体系设计的参考

---

## 一、调研对象概览

| 软件 | 厂商/类型 | 形态 | 核心定位 |
|------|----------|------|----------|
| **MDESIGN** | 德国 Tedata (1983) | 桌面/教学版 | 50+ 机器原件计算 + FKM 强度评估 + CAD 集成 |
| **eAssistant** | 德国 eAssistant | Web 端 | DIN/ISO/VDI/ANSI/AGMA 标准计算 + CAD 插件 |
| **机械工程师助手** | 国内 (V30.apk) | 安卓移动端 | 13 大分类、70+ 计算、单位换算 |
| **百思技术手册** | 国内 (v1.0.1.0) | Windows 桌面 | 7 类标准件选型 + 错误案例库 + 资料库 |
| **华望 M-Design** | 国内华望 (2026) | MBSE 平台 | AI 建模 + SysML + 多学科仿真 |

---

## 二、核心功能对比

### 2.1 计算模块覆盖度

| 维度 | MDESIGN | eAssistant | 机械工程师助手 | 百思 | **本工具 (现状)** |
|------|---------|-----------|-------------|------|-----------------|
| 齿轮/蜗杆 | ✅ 多类 | ✅ 多类 | ✅ | ✅ | ✅ 已有 |
| 螺栓/紧固 | ✅ VDI 2230 | ✅ Eurocode 3 | ✅ 8 场景 | ✅ | ✅ 已有 |
| 轴/轴承 | ✅ DIN 743 | ✅ 多类 | ✅ | ✅ | ✅ 已有 |
| 焊接 | ✅ FKM | ✅ | ❌ | ❌ | ✅ 已有 |
| 液压/气动 | ✅ espresso | ✅ | ✅ | ✅ | ✅ 已有 |
| 弹簧/阻尼 | ✅ | ✅ | ✅ | ❌ | ✅ 已有 |
| 容器/法兰 | ✅ AD 2000 | ❌ | ❌ | ❌ | ❌ |
| 公差/配合 | ✅ | ✅ | ✅ | ❌ | ✅ 已有 |
| 强度评估 (FKM) | ✅ | 部分 | ❌ | ❌ | ✅ 疲劳 |
| 3D 辅助/CAD 集成 | ✅ STEP | ✅ SOLIDWORKS | ❌ | ❌ | ❌ |
| AI 助手 | ✅ aiven (2026) | ✅ | ❌ | ❌ | ❌ |

### 2.2 核心数据资源

- **MDESIGN**: 综合材料数据库 (含 FKM)、制造商目录 (Teckentrup/Heico/NSK 等)
- **机械工程师助手**: 1200+ 金属/非金属材料物理/力学/热学/工艺参数
- **百思**: 1000+ 错误案例库 (设计禁忌)

### 2.3 文档与可追溯性

- **MDESIGN doc** (2026 替换 PDF): 集成注释、多语言、自动生成
- **eAssistant**: 自动报告 + CAD 双向同步 + STEP 导出
- **机械工程师助手**: GB/T 19001 工艺文档,公式带标准条款号 (如 GB/T 3480-2013)

### 2.4 单位与多语言

- 全部支持多单位制 (公制/英制/美制/德制)
- MDESIGN 2024 起多语言同文档
- eAssistant 支持 DIN/ISO/AGMA 标准术语切换

### 2.5 知识图谱

- 机械工程师助手: 13 大分类对应《机械设计手册》(第五版) 90%+ 高频章节
  1. 常用几何计算
  2. 机械传动设计
  3. 轴系结构校核
  4. 紧固件选型
  5. 公差与配合查询
  6. 材料力学参数库
  7. 热处理规范
  8. 弹簧设计
  9. 轴承寿命计算
  10. 齿轮参数计算
  11. 液压与气动元件选型
  12. 管道流体计算
  13. 单位制式智能换算

---

## 三、借鉴要点 (本工具可吸收)

### 3.1 分类体系 (P0)

参考《机械设计手册》(第五版) 目录重构模块组织:

| 新分类 (13 大类) | 对应本工具现有模块 |
|-----------------|------------------|
| 1. 常用几何与数学 | (mechanics 力学) |
| 2. 机械传动设计 | gear, worm, belt, chain, cam |
| 3. 轴系结构与强度 | shaft, bearing, bearing_full, beam |
| 4. 紧固件与连接 | thread, weld, strength.adhesive/rivet/pressfit |
| 5. 公差配合与形位 | tolerance |
| 6. 工程材料参数 | materials, steel_grades, aluminum_grades, plastics |
| 7. 表面与热处理 | surface, fatigue |
| 8. 弹簧设计 | spring |
| 9. 流体传动 (液压/气动) | hydraulic, pneumatic |
| 10. 冲压与塑性成形 | press |
| 11. 制动器与离合器 | brake, coupling |
| 12. 力学与振动 | mechanics (linear/rotational/vibration) |
| 13. 单位制与换算 | units |

### 3.2 标准件库 (P0, 现有数据已覆盖)

- 已存在: bearings_deep_groove (153 行), bearings_thrust (153 行), oring_groove (多)
- 待激活: threads_metric (1600+ 行), threads_imperial (148 行)
- 待暴露: steel_grades, aluminum_grades, plastics

### 3.3 计算历史 (P1, 全新)

参考 eAssistant 的"项目式"管理,本工具采用轻量 SQLite 存储:

- 表结构: id / timestamp / module / inputs(JSON) / outputs(JSON) / duration_ms
- API: POST /api/history, GET /api/history, DELETE /api/history/{id}
- 前端: "历史"侧边栏,可重放、导出 CSV

### 3.4 公式查询 (P1, 全新, **不写新公式**)

- 静态索引: 扫描 calculations/*.py, 提取 docstring 中的公式 (LaTeX) 与参数说明
- 数据源: 现有 24 个模块的 docstring (不写新公式)
- API: GET /api/formulas?module=gear&keyword=分度圆
- 前端: "公式"标签页 + 全文搜索

### 3.5 物理常数 (P1, 现有数据)

- 现有 utils.units.PHYSICAL_CONSTANTS 已包含
- API: GET /api/units/constants (已有), 扩展分类浏览
- 前端: "常数"标签页, 按类别展开

### 3.6 错误预警 (P2, 借鉴百思)

- 静态规则: 输入越界 (模数=0, 齿数<2) → 提示
- 标准符合性: 螺栓等级 vs 抗拉强度匹配提示
- 复用现有 safe_float + 各函数内的 if 校验即可,不写新业务规则

### 3.7 AI 助手 (P2 远期)

- MDESIGN aiven (2026 上线) 与 eAssistant AI 都已落地
- 本工具 P2 阶段可考虑: 简单输入意图识别 → 路由到对应 API

---

## 四、本工具差异化定位

| 维度 | 本工具优势 | 借鉴方向 |
|------|----------|----------|
| **离线/单机** | 打包 EXE,无需网络 | 机械工程师助手 (离线优先) |
| **覆盖度** | 24 个模块,常规计算较全 | 对齐 MDESIGN 子集 |
| **i18n** | 已有中/英/日 | 对齐 MDESIGN doc 多语言 |
| **轻量部署** | Flask + PyInstaller | 比 MDESIGN 启动快 10x |
| **可扩展** | 现有 24 模块,易增删 | 模块化对齐 MDESIGN |

---

## 五、本计划直接采纳

1. **Phase 1 重构**: 引入 Blueprint,拆 app.py;前端用 Alpine.js 模块化
2. **Phase 2 扩展**:
   - 分类体系对齐《机械设计手册》13 大类
   - 公式查询 (扫现有 docstring,不写新公式)
   - 常数查询 (用现有 PHYSICAL_CONSTANTS)
   - 计算历史 (SQLite 存储,新增不删旧)
   - 标准件库激活 (threads_metric 等已在 JSON 中)
3. **测试**: pytest 单元 + 集成 + locust 压测
4. **不写公式与数据** 原则: 所有计算/常数/材料来自现有模块和 JSON

---

## 参考链接

- MDESIGN: <https://www.mdesign.de/software/>
- eAssistant: <https://www.eassistant.eu/en/index.html>
- 机械攻城狮 Skill: <https://skillhub.cloud.tencent.com/skills/mechanical-design-toolkit>
- 机械工程师助手介绍: <https://m.duote.com/soft/4982.html>
- 百思技术手册: <http://zdhfa.com/>
- 华望 M-Design 2026: <https://blog.csdn.net/HZHW_MBSE/article/details/145636013>
