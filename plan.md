# 跨性别群体声音收集分析系统 - 项目计划书

## 一、项目概述

### 1.1 项目背景
本项目旨在为跨性别群体提供一个便捷的声音分析与记录工具，通过 Telegram Bot 作为交互界面，用户可以随时上传语音并获得详细的声音参数分析报告。

### 1.2 核心功能
- **语音上传与分析**：用户通过 Telegram 发送语音消息，系统自动下载并分析
- **多维度音频参数提取**：基频、共振峰、频谱、能量、音质等多类参数
- **可视化图表生成**：语谱图、基频轮廓图、共振峰轨迹图等
- **历史数据追踪**：记录历次录音及分析结果，支持对比
- **性别特征评估**：基于多参数综合评估声音性别特征

### 1.3 运行平台
- 目标环境：Android Termux (Python 环境)
- 通信接口：Telegram Bot API
- 无需传统前端，纯命令交互

---

## 二、系统架构

```
┌─────────────────┐     Telegram      ┌──────────────────┐
│   Telegram User │ ◄───────────────► │   Telegram Bot   │
│   (发送语音/命令) │                   │   (Python 实现)   │
└─────────────────┘                   └────────┬─────────┘
                                                │
                                                ▼
                                    ┌────────────────────┐
                                    │   音频分析引擎      │
                                    │   (核心处理器)      │
                                    ├────────────────────┤
                                    │  - 音频预处理       │
                                    │  - 参数提取         │
                                    │  - 图表生成         │
                                    │  - 报告生成         │
                                    └────────┬───────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
          ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
          │   SQLite 数据库  │      │   文件存储       │      │   图表输出      │
          │  (用户数据/历史)  │      │  (音频/图表缓存) │      │   (临时文件)    │
          └─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## 三、功能模块设计

### 3.1 Telegram Bot 交互模块

#### 3.1.1 命令系统
| 命令 | 功能 | 示例 |
|------|------|------|
| `/start` | 启动机器人，显示欢迎信息和帮助 | `/start` |
| `/help` | 显示所有可用命令及说明 | `/help` |
| `/analyze` | 分析用户回复的语音消息 | 回复语音输入 `/analyze` |
| `/history` | 查看历史分析记录 | `/history` |
| `/compare <id1> <id2>` | 对比两次分析结果 | `/compare 001 003` |
| `/profile` | 查看用户档案和声音特征趋势 | `/profile` |
| `/settings` | 修改分析参数设置 | `/settings` |
| `/export <id>` | 导出指定分析的详细报告 | `/export 005` |

#### 3.1.2 交互流程
1. 用户发送语音消息 → Bot 提示使用 `/analyze` 命令
2. 用户回复该语音并发送 `/analyze` → Bot 开始处理
3. 分析完成后 → Bot 发送文字报告 + 图表图片
4. 图表以图片形式发送，关键数据以 Markdown 格式呈现

### 3.2 音频分析引擎模块

#### 3.2.1 核心依赖库
```python
librosa          # 音频分析核心库
numpy            # 数值计算
scipy             # 信号处理
soundfile         # 音频文件读写
matplotlib        # 图表生成
sqlalchemy        # 数据库 ORM
python-telegram-bot  # Telegram Bot API
```

#### 3.2.2 音频参数提取模块

**基础音频预处理**
- 格式转换 (ogg/mp3/opus → wav)
- 重采样 (统一为 16kHz)
- 降噪处理 (可选)
- 端点检测 (VAD)

**1. 基频与音高分析**
| 参数 | 说明 | 算法 |
|------|------|------|
| 基频 F0 | 声带振动频率 |praatpy / librosa.piptrack |
| 基频范围 | 最小/最大/平均 | 统计 F0 序列 |
| 基频标准差 | 音高稳定性 | np.std(F0) |
| Jitter | 相邻周期基频变化率 | 公式计算 |
| 音高轮廓 | 句子层面音高曲线 | 平滑插值绘制 |

**2. 共振峰与音色分析**
| 参数 | 说明 | 算法 |
|------|------|------|
| F1/F2/F3 | 前三共振峰 | LPC 分析 + 峰值提取 |
| F2-F1 间距 | 声音亮度指标 | F2 - F1 |
| 共振峰频率比 | 各共振峰相对关系 | F2/F1, F3/F2 |
| 频谱质心 | 音色明亮度 | librosa.feature.spectral_centroid |
| 频谱滚降 | 高频衰减点 | librosa.feature.spectral_rolloff |
| 频谱通量 | 帧间频谱变化 | librosa.onset.spectral_flux |

**3. 能量与响度分析**
| 参数 | 说明 | 算法 |
|------|------|------|
| RMS 能量 | 整体响度 | librosa.feature.rms |
| 峰值振幅 | 最大瞬时能量 | np.max(np.abs(y)) |
| 动态范围 | 最大/最小能量比 | 20*log10(max/min) |
| 能量包络 | 响度时变曲线 | Hilbert 变换或平滑 |
| 能量变化率 | 发音力度变化 | 一阶差分统计 |

**4. 音质与稳定性分析**
| 参数 | 说明 | 算法 |
|------|------|------|
| Shimmer | 振幅微扰 | 相邻周期振幅变化率 |
| HNR | 谐噪比 | 谐波/噪声能量比值 |
| APQ | 非周期性指标 | 周期成分占比 |
| 过零率 | 波形穿越零轴频率 | librosa.feature.zero_crossing_rate |
| 自相关峰值 | 周期性强度 | np.correlate 峰值检测 |

**5. 发声模式分析**
| 参数 | 说明 | 算法 |
|------|------|------|
| Voice Onset Time | 辅音到声带振动间隔 | 短时能量检测 |
| Open Quotient | 声门开放周期占比 | 声门模型估算 |
| Breathiness | 气息声程度 | 高频噪声能量比 |
| 硬/软起音 | 声带闭合方式 | 起始瞬态分析 |

**6. 语言节奏与语调分析**
| 参数 | 说明 | 算法 |
|------|------|------|
| 语速 | 每秒音节数 | 能量峰值检测 + 滑动窗口 |
| 音节时长分布 | 各音节持续时间 | onset detection |
| 停顿模式 | 停顿位置和时长 | 能量阈值检测 |
| 语调范围 | 语句内音高变化幅度 | F0 max - F0 min |
| 语调模式 | 升/降/平/曲折调 | F0 趋势分析 |

**7. 性别特征综合指标**
| 参数 | 说明 |
|------|------|
| 基频性别指数 | F0 在男女典型分布中的位置 (0-1, 0=男, 1=女) |
| 共振峰性别指数 | 综合 F1/F2/F3 的性别判别 |
| 整体性别感知评分 | 多参数综合评估 (0-100) |
| 训练进度对比 | 与历史录音的参数变化曲线 |

#### 3.2.3 可视化图表模块

**必生成图表**
| 图表名 | 内容 | 用途 |
|--------|------|------|
| 语谱图 | 时间-频率-能量三维图 | 频谱概览 |
| 基频轮廓图 | F0 随时间变化曲线 | 音高分析 |
| 共振峰轨迹图 | F1/F2/F3 时变曲线 | 音色分析 |
| 能量包络图 | RMS 能量时变曲线 | 响度分析 |
| 频谱质心图 | 质心频率时变曲线 | 明亮度分析 |

**可选图表**
- LPC 频谱包络
- 倒频谱图
- 梅尔频谱图
- MFCC 系数图

### 3.3 数据存储模块

#### 3.3.1 SQLite 数据库设计

```sql
-- 用户表
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings TEXT  -- JSON 格式存储用户设置
);

-- 分析记录表
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    audio_path TEXT,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration FLOAT,  -- 音频时长(秒)
    -- 核心参数快照
    f0_mean REAL,
    f0_min REAL,
    f0_max REAL,
    f0_std REAL,
    jitter REAL,
    shimmer REAL,
    hnr REAL,
    f1_mean REAL,
    f2_mean REAL,
    f3_mean REAL,
    spectral_centroid_mean REAL,
    rms_mean REAL,
    gender_score REAL,  -- 性别评分 0-100
    -- JSON 存储完整参数
    full_params TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 图表文件表
CREATE TABLE charts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER,
    chart_type TEXT,  -- spectrogram, pitch_contour, formants, etc.
    file_path TEXT,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

#### 3.3.2 文件存储结构
```
/workspace/
├── data/
│   ├── audio/          # 原始音频文件
│   │   └── {user_id}/
│   │       └── {analysis_id}.wav
│   ├── charts/         # 生成的图表
│   │   └── {user_id}/
│   │       └── {analysis_id}_{chart_type}.png
│   └── database/
│       └── voice_analysis.db
├── src/
│   ├── bot.py              # Telegram Bot 入口
│   ├── audio_processor.py  # 音频处理主模块
│   ├── pitch_tracker.py    # 基频跟踪
│   ├── formant_analyzer.py # 共振峰分析
│   ├── spectrum_analyzer.py# 频谱分析
│   ├── energy_analyzer.py  # 能量分析
│   ├── quality_analyzer.py # 音质分析
│   ├── prosody_analyzer.py # 韵律分析
│   ├── gender_classifier.py# 性别特征评估
│   ├── visualizer.py       # 图表生成
│   ├── database.py         # 数据库操作
│   └── utils.py            # 工具函数
├── config.py            # 配置文件
├── requirements.txt     # 依赖列表
└── plan.md              # 本计划书
```

---

## 四、Telegram Bot 交互设计

### 4.1 消息模板

**欢迎消息**
```
欢迎使用跨性别群体声音分析助手！

我可以帮你分析语音的各种参数，包括：
🎵 基频与音高
🎤 共振峰与音色
📊 频谱与能量
🗣️ 音质与发声模式
📈 性别特征评估

发送语音消息，然后回复 /analyze 即可开始分析。
```

**分析结果消息**
```
✅ 分析完成！

📊 基本信息
├ 时长: 3.2 秒
├ 采样率: 16000 Hz

🎵 基频分析 (F0)
├ 平均基频: 185 Hz
├ 基频范围: 162 - 218 Hz
├ 标准差: 12.3 Hz
└ Jitter: 0.82%

🎤 共振峰分析
├ F1: 520 Hz | F2: 1480 Hz | F3: 2850 Hz
├ F2-F1: 960 Hz (明亮)
└ 性别指数: 0.72

📈 性别特征
└ 综合评分: 78/100 (偏女性化)
```

**图表发送**
- 语谱图、基频轮廓图等以图片形式发送
- 使用 `sendPhoto` 方法

### 4.2 状态管理
```
用户状态:
- IDLE: 等待输入
- AUDIO_RECEIVED: 收到语音，待分析
- ANALYZING: 分析中
- RESULTS_READY: 结果就绪
```

---

## 五、技术实现要点

### 5.1 Termux 环境适配
```bash
# Termux 依赖安装
pkg update && pkg install python libportaudio
pip install -r requirements.txt

# Telegram Bot Token 通过环境变量配置
export TELEGRAM_BOT_TOKEN="your_token_here"
```

### 5.2 音频处理流程
```
1. 接收语音文件 (Telegram 服务器)
2. 下载到本地 /data/audio/{user_id}/
3. 使用 librosa.load() 加载音频
4. 统一重采样为 16kHz
5. 执行各项参数提取
6. 生成图表保存到 /data/charts/
7. 构造消息回复用户
```

### 5.3 图表生成策略
- 使用 matplotlib 生成图表
- DPI 设置为 150 保证清晰度
- 配色使用暗色主题便于查看
- 图片格式为 PNG

---

## 六、开发阶段划分

### Phase 1: 基础框架 (第1-2周)
- [ ] 项目结构搭建
- [ ] Telegram Bot 基础框架
- [ ] 数据库模型建立
- [ ] 音频文件接收与保存

### Phase 2: 核心分析模块 (第3-5周)
- [ ] 基频跟踪实现
- [ ] 共振峰分析实现
- [ ] 频谱分析实现
- [ ] 能量分析实现
- [ ] 音质参数实现

### Phase 3: 高级功能 (第6-7周)
- [ ] 韵律分析模块
- [ ] 性别特征评估
- [ ] 可视化图表生成
- [ ] 历史记录与对比

### Phase 4: 优化与测试 (第8周)
- [ ] 参数调优
- [ ] 错误处理完善
- [ ] 用户体验优化
- [ ] 文档编写

---

## 七、风险评估与备选方案

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| Termux 性能有限 | 分析速度慢 | 减少分析参数，限制音频时长 |
| 移动端网络不稳定 | 语音上传失败 | 增加重试机制 |
| 音频质量差异大 | 分析结果不准 | 增加音频质量检测 |
| 性别评估准确性 | 结果偏差 | 明确告知为参考指标 |

---

## 八、讨论要点

1. **音频时长限制**：是否限制单次分析时长（如60秒）？
2. **数据隐私**：是否需要端到端加密或数据本地化存储？
3. **性别评估算法**：采用规则判断还是机器学习模型？
4. **图表详细程度**：所有图表全部生成还是用户可选？
5. **历史数据容量**：是否限制用户存储的录音数量？

---

*计划书版本: 1.0*
*创建日期: 2026-06-25*
