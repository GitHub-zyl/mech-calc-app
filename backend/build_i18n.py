# -*- coding: utf-8 -*-
"""Build i18n JSON data file"""
import json

data = {}

# UI text
data['计算'] = {'en': 'Calculate', 'ja': '計算'}
data['计算结果'] = {'en': 'Result', 'ja': '計算結果'}
data['公式示例'] = {'en': 'Formula Example', 'ja': '計算例'}
data['知识'] = {'en': 'Knowledge', 'ja': '知識'}
data['复制'] = {'en': 'Copy', 'ja': 'コピー'}
data['公式'] = {'en': 'Formula', 'ja': '計算式'}
data['参数'] = {'en': 'Parameters', 'ja': 'パラメータ'}
data['关闭'] = {'en': 'Close', 'ja': '閉じる'}
data['暂无知识'] = {'en': 'No knowledge available', 'ja': '知識がありません'}
data['欢迎使用机械设计常用计算表'] = {'en': 'Welcome to Mechanical Design Calculator', 'ja': '機械設計計算表へようこそ'}
data['填写参数后点击计算'] = {'en': 'Fill parameters and calculate', 'ja': 'パラメータを入力して計算'}
data['计算历史'] = {'en': 'Calculation History', 'ja': '計算履歴'}
data['清除历史'] = {'en': 'Clear History', 'ja': '履歴消去'}
data['导出CSV'] = {'en': 'Export CSV', 'ja': 'CSV出力'}
data['基于《机械设计常用计算表.xlsx》'] = {'en': 'Based on Mechanical Design Calculator.xlsx', 'ja': '機械設計計算表.xlsxに基づく'}

# Module categories
data['材料数据'] = {'en': 'Materials', 'ja': '材料データ'}
data['齿轮传动'] = {'en': 'Gear Drive', 'ja': '歯車伝動'}
data['弹簧'] = {'en': 'Spring', 'ja': 'ばね'}
data['螺纹/紧固'] = {'en': 'Thread / Fastener', 'ja': 'ねじ/締結'}
data['链传动'] = {'en': 'Chain Drive', 'ja': 'チェーン伝動'}
data['带传动'] = {'en': 'Belt Drive', 'ja': 'ベルト伝動'}
data['凸轮/分割器'] = {'en': 'Cam / Indexer', 'ja': 'カム/割り出し'}
data['公差配合'] = {'en': 'Tolerance / Fit', 'ja': '公差/はめあい'}
data['冲压钣金'] = {'en': 'Stamping / Sheet Metal', 'ja': 'プレス/板金'}
data['液压系统'] = {'en': 'Hydraulic System', 'ja': '油圧システム'}
data['联轴器/密封'] = {'en': 'Coupling / Seal', 'ja': '継手/シール'}
data['电机常识'] = {'en': 'Motor Knowledge', 'ja': 'モーター知識'}
data['材料力学'] = {'en': 'Strength of Materials', 'ja': '材料力学'}
data['工具'] = {'en': 'Tools', 'ja': 'ツール'}
data['运动学'] = {'en': 'Kinematics', 'ja': '運動学'}
data['转动'] = {'en': 'Rotation', 'ja': '回転'}
data['振动'] = {'en': 'Vibration', 'ja': '振動'}
data['热传导'] = {'en': 'Heat Transfer', 'ja': '熱伝導'}
data['流体'] = {'en': 'Fluid Mechanics', 'ja': '流体力学'}
data['轮系'] = {'en': 'Gear Trains', 'ja': '歯車列'}
data['飞轮/制动'] = {'en': 'Flywheel / Brake', 'ja': 'フライホイール/ブレーキ'}

# Calculator names
data['材料查询'] = {'en': 'Material Search', 'ja': '材料検索'}
data['齿轮基本参数'] = {'en': 'Gear Parameters', 'ja': '歯車基本パラメータ'}
data['齿轮啮合计算'] = {'en': 'Gear Mesh', 'ja': '歯車かみ合い計算'}
data['电机选型计算'] = {'en': 'Motor Selection', 'ja': 'モーター選定'}
data['齿条传动计算'] = {'en': 'Rack & Pinion', 'ja': 'ラック＆ピニオン'}
data['压缩弹簧计算'] = {'en': 'Compression Spring', 'ja': '圧縮ばね'}
data['公制螺纹计算'] = {'en': 'Metric Thread', 'ja': 'メートルねじ'}
data['攻丝底孔'] = {'en': 'Tap Drill', 'ja': 'タップ下穴'}
data['螺栓扭矩计算'] = {'en': 'Bolt Torque', 'ja': 'ボルトトルク'}
data['链轮参数'] = {'en': 'Sprocket Parameters', 'ja': 'スプロケットパラメータ'}
data['链条长度计算'] = {'en': 'Chain Length', 'ja': 'チェーン長さ計算'}
data['输送链张力'] = {'en': 'Conveyor Tension', 'ja': 'コンベヤ張力'}
data['三角皮带计算'] = {'en': 'V-Belt Drive', 'ja': 'Vベルト伝動'}
data['同步带计算'] = {'en': 'Timing Belt', 'ja': 'タイミングベルト'}
data['HTD圆弧齿'] = {'en': 'HTD Timing Belt', 'ja': 'HTDタイミングベルト'}
data['凸轮轮廓计算'] = {'en': 'Cam Profile', 'ja': 'カム輪郭計算'}
data['分割器选型'] = {'en': 'Indexer Selection', 'ja': '割り出し装置選定'}
data['分度盘计算'] = {'en': 'Indexing Plate', 'ja': '割り出し盤計算'}
data['冲裁力计算'] = {'en': 'Blanking Force', 'ja': '抜き力計算'}
data['V型弯曲力'] = {'en': 'V-Bending Force', 'ja': 'V曲げ力'}
data['U型弯曲力'] = {'en': 'U-Bending Force', 'ja': 'U曲げ力'}
data['剪切力计算'] = {'en': 'Shear Force', 'ja': 'せん断力'}
data['压印力计算'] = {'en': 'Embossing Force', 'ja': 'エンボス力'}
data['公差配合计算'] = {'en': 'Fit Tolerance', 'ja': 'はめあい公差'}
data['轴公差计算'] = {'en': 'Shaft Tolerance', 'ja': '軸公差'}
data['孔公差计算'] = {'en': 'Hole Tolerance', 'ja': '穴公差'}
data['管路压损'] = {'en': 'Pipe Pressure Loss', 'ja': '配管圧力損失'}
data['液压冲击'] = {'en': 'Hydraulic Shock', 'ja': '油圧衝撃'}
data['蓄能器选型'] = {'en': 'Accumulator', 'ja': 'アキュムレータ'}
data['油箱热平衡'] = {'en': 'Tank Heat Balance', 'ja': 'タンク熱平衡'}
data['齿式联轴器'] = {'en': 'Gear Coupling', 'ja': '歯車継手'}
data['万向联轴器'] = {'en': 'Universal Joint', 'ja': 'ユニバーサルジョイント'}
data['O型圈沟槽'] = {'en': 'O-Ring Groove', 'ja': 'Oリング溝'}
data['同步转速'] = {'en': 'Synchronous Speed', 'ja': '同期速度'}
data['扭矩/电流'] = {'en': 'Torque & Current', 'ja': 'トルク/電流'}
data['电机常识速查'] = {'en': 'Motor Knowledge', 'ja': 'モーター知識'}
data['截面惯性矩'] = {'en': 'Section Properties', 'ja': '断面特性'}
data['立柱稳定性'] = {'en': 'Column Stability', 'ja': '柱の安定'}
data['焊缝强度'] = {'en': 'Weld Strength', 'ja': '溶接強度'}
data['键强度校核'] = {'en': 'Key Strength', 'ja': 'キー強度'}
data['销强度校核'] = {'en': 'Pin Strength', 'ja': 'ピン強度'}
data['过盈配合'] = {'en': 'Interference Fit', 'ja': 'しまりばめ'}
data['压入力'] = {'en': 'Press Fit Force', 'ja': '圧入力'}
data['单位换算'] = {'en': 'Unit Converter', 'ja': '単位換算'}
data['离心力'] = {'en': 'Centrifugal Force', 'ja': '遠心力'}
data['动量/能量'] = {'en': 'Momentum / Energy', 'ja': '運動量/エネルギー'}
data['螺旋传动'] = {'en': 'Lead Screw', 'ja': 'ねじ送り'}
data['行星轮系'] = {'en': 'Planetary Gear', 'ja': '遊星歯車'}
data['飞轮储能'] = {'en': 'Flywheel Energy', 'ja': 'フライホイール'}
data['理想气体'] = {'en': 'Ideal Gas', 'ja': '理想気体'}
data['伯努利'] = {'en': 'Bernoulli Eq.', 'ja': 'ベルヌーイ'}
data['热膨胀'] = {'en': 'Thermal Expansion', 'ja': '熱膨張'}
data['弹簧质量振动'] = {'en': 'Spring-Mass Vibration', 'ja': 'ばね-質量振動'}
data['扭振/临界转速'] = {'en': 'Torsional Vibration', 'ja': 'ねじり振動'}

# Result field names
data['分度圆直径'] = {'en': 'Pitch Diameter', 'ja': 'ピッチ円直径'}
data['齿顶圆直径'] = {'en': 'Tip Diameter', 'ja': '歯先円直径'}
data['齿根圆直径'] = {'en': 'Root Diameter', 'ja': '歯底円直径'}
data['基圆直径'] = {'en': 'Base Circle Dia.', 'ja': '基礎円直径'}
data['齿顶高'] = {'en': 'Addendum', 'ja': '歯たけ'}
data['齿根高'] = {'en': 'Dedendum', 'ja': '歯末のたけ'}
data['全齿高'] = {'en': 'Whole Depth', 'ja': '全歯たけ'}
data['齿距'] = {'en': 'Circular Pitch', 'ja': 'ピッチ'}
data['齿厚'] = {'en': 'Tooth Thickness', 'ja': '歯厚'}
data['模数'] = {'en': 'Module', 'ja': 'モジュール'}
data['齿数'] = {'en': 'Teeth', 'ja': '歯数'}
data['变位系数'] = {'en': 'Mod. Coefficient', 'ja': '転位係数'}
data['传动比'] = {'en': 'Ratio', 'ja': '伝達比'}
data['输入扭矩'] = {'en': 'Input Torque', 'ja': '入力トルク'}
data['输出扭矩'] = {'en': 'Output Torque', 'ja': '出力トルク'}
data['刚度'] = {'en': 'Stiffness', 'ja': '剛性'}
data['最大切应力'] = {'en': 'Max Shear Stress', 'ja': '最大せん断応力'}
data['安全系数'] = {'en': 'Safety Factor', 'ja': '安全率'}
data['变形量'] = {'en': 'Deflection', 'ja': '変形量'}
data['中径'] = {'en': 'Pitch Diameter', 'ja': '有効径'}
data['小径'] = {'en': 'Minor Diameter', 'ja': '谷の径'}
data['螺距'] = {'en': 'Pitch', 'ja': 'ピッチ'}
data['预紧力'] = {'en': 'Preload', 'ja': '予締め力'}
data['拧紧扭矩'] = {'en': 'Tightening Torque', 'ja': '締付けトルク'}
data['弹性模量'] = {'en': 'Elastic Modulus', 'ja': '弾性係数'}
data['泊松比'] = {'en': "Poisson's Ratio", 'ja': 'ポアソン比'}
data['密度'] = {'en': 'Density', 'ja': '密度'}
data['抗拉强度'] = {'en': 'Tensile Strength', 'ja': '引張強さ'}
data['屈服强度'] = {'en': 'Yield Strength', 'ja': '降伏点'}
data['配合类型'] = {'en': 'Fit Type', 'ja': 'はめあい種類'}
data['最大间隙'] = {'en': 'Max Clearance', 'ja': '最大すきま'}
data['最小间隙'] = {'en': 'Min Clearance', 'ja': '最小すきま'}
data['最大过盈'] = {'en': 'Max Interference', 'ja': '最大しめしろ'}

with open('机械计算小程序/data/i18n_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'✅ {len(data)} translation entries saved')
