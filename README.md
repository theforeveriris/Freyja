# Freyja - 跨性别群体声音分析 Telegram Bot

> 基于 Python 的跨性别群体声音收集与分析工具，通过 Telegram Bot 交互，提供专业的音频参数分析和性别特征评估。

## ✨ 功能特性

### 🎵 音频分析
- **基频分析 (F0)**：均值、中位数、范围、标准差、Jitter
- **共振峰分析**：F1/F2/F3 频率、共振峰比、轨迹追踪
- **频谱分析**：质心、滚降、带宽、通量
- **能量分析**：RMS、动态范围、能量包络
- **音质分析**：Shimmer、HNR、APQ、过零率
- **韵律分析**：语速、停顿、语调特征

### 🧭 性别特征评估
- 五维加权评分系统（基频 40% / 共振峰 25% / 音色 15% / 韵律 10% / 音质 10%）
- 音高分布统计（男性区 / 女性区 / 超出区百分比）
- 雷达图可视化展示

### 📊 可视化图表
- 波形图 / 语谱图 / 梅尔频谱图
- 基频轮廓图 / 基频分布直方图
- 共振峰轨迹图 / 共振峰散点图
- 能量包络图 / 频谱质心时变图
- MFCC 热力图 / 性别特征雷达图

### ⚙️ 灵活设置
- 采样率可调（默认 32kHz）
- 基频算法选择（PyIN / 自相关）
- 性别权重自定义
- 图表主题切换（深色 / 浅色 / 蓝色）
- 隐私设置（是否保存音频、自动删除）

## 📋 命令列表

| 命令 | 说明 |
|------|------|
| `/start` | 开始使用，欢迎消息 |
| `/help` | 查看帮助文档 |
| `/analyze` | 回复语音消息进行基础分析 |
| `/expert [id]` | 专业分析菜单，查看详细参数和图表 |
| `/settings` | 进入设置菜单 |
| `/history` | 查看历史分析记录列表 |
| `/view <id>` | 查看单条记录详情 |
| `/delete <id>` | 删除指定分析记录 |
| `/deleteall` | 删除所有记录（需确认） |

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Termux 环境（可选，也可在任意 Linux/Windows/Mac 环境运行）
- Telegram 账号

### 1. 申请 Telegram Bot

#### 步骤一：创建 Bot
1. 在 Telegram 中搜索 **@BotFather**
2. 发送 `/newbot` 命令
3. 按照提示输入 Bot 名称（显示名称，可以是任意名字）
4. 输入 Bot 用户名（必须以 `bot` 结尾，例如 `FreyjaVoiceBot`）
5. 成功后，BotFather 会给你一个 **Token**，格式类似：`123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`

#### 步骤二：配置 Bot（可选但推荐）
1. 向 @BotFather 发送 `/setdescription`
2. 选择你的 Bot，然后输入描述文字
3. 发送 `/setabouttext` 设置关于信息
4. 发送 `/setuserpic` 设置 Bot 头像
5. 发送 `/setcommands` 设置命令菜单，粘贴以下内容：

```
start - 开始使用
help - 查看帮助
analyze - 分析语音（回复语音消息使用）
expert - 专业分析菜单
settings - 设置菜单
history - 历史记录
view - 查看详情
delete - 删除记录
deleteall - 删除所有记录
```

### 2. 安装运行

#### 方式一：Termux 环境

```bash
# 安装必要的包
pkg update && pkg upgrade
pkg install python git fftw libsndfile

# 克隆仓库
git clone https://github.com/theforeveriris/Freyja.git
cd Freyja

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置 Bot Token
echo "TELEGRAM_BOT_TOKEN=你的BotToken" > .env

# 运行
python main.py
```

#### 方式二：普通 Linux/Windows/Mac

```bash
# 克隆仓库
git clone https://github.com/theforeveriris/Freyja.git
cd Freyja

# 安装依赖
 

# 配置 Bot Token
# Linux/Mac:
echo "TELEGRAM_BOT_TOKEN=你的BotToken" > .env
# Windows (PowerShell):
# echo TELEGRAM_BOT_TOKEN=你的BotToken | Out-File -Encoding utf8 .env

# 运行
python main.py
```

### 3. 后台运行（Termux）

```bash
# 安装 tmux
pkg install tmux

# 创建会话
tmux new -s freyja

# 运行 Bot
cd ~/Freyja
source venv/bin/activate
python main.py

# 按 Ctrl+B 然后按 D 分离会话
# 重新连接：tmux attach -t freyja
```

## 📖 使用指南

### 基础分析
1. 打开 Telegram，找到你的 Bot
2. 发送一条语音消息（建议 10-60 秒，最长 2 分钟）
3. 回复这条语音消息，输入 `/analyze`
4. 等待分析完成，查看基础报告

### 专业分析
1. 完成基础分析后，发送 `/expert`
2. 选择要查看的详细项目：
   - 🎵 基频详细分析
   - 🎤 共振峰详细分析
   - 🌈 频谱特征分析
   - 🔊 能量与响度分析
   - ✨ 音质与稳定性
   - 🗣️ 语言节奏与语调
   - 🧭 性别特征深度分析
   - 🖼️ 全部可视化图表

### 调整设置
发送 `/settings` 进入设置菜单，可以调整：
- **音频设置**：采样率、声道、VAD 灵敏度、音量归一化、最大时长
- **分析设置**：基频算法、基频范围、帧长、跳数、共振峰数量
- **性别设置**：各维度权重、男/女基频范围、基线性别
- **图表设置**：主题、DPI、是否显示网格、频谱最大频率
- **隐私设置**：是否保存音频、完成时通知、自动删除天数

## 📁 项目结构

```
Freyja/
├── main.py                    # 主入口文件
├── config.py                  # 配置文件
├── requirements.txt           # 依赖列表
├── .env                       # 环境变量（需自行创建）
└── src/
    ├── bot.py                 # Telegram Bot 主逻辑
    ├── database.py            # 数据库模型与操作
    ├── utils.py               # 工具函数
    ├── visualizer.py          # 可视化图表生成
    ├── audio/                 # 音频分析模块
    │   ├── preprocessor.py    # 音频预处理
    │   ├── pitch_tracker.py   # 基频跟踪
    │   ├── formant_analyzer.py# 共振峰分析
    │   ├── spectrum_analyzer.py# 频谱分析
    │   ├── energy_analyzer.py # 能量分析
    │   ├── quality_analyzer.py# 音质分析
    │   ├── prosody_analyzer.py# 韵律分析
    │   └── gender_classifier.py# 性别分类
    └── handlers/              # Telegram 命令处理器
        ├── start.py           # 开始/帮助命令
        ├── analyze.py         # 分析命令
        ├── expert.py          # 专业分析命令
        ├── settings.py        # 设置命令
        ├── history.py         # 历史记录命令
        ├── delete.py          # 删除命令
        └── profile.py         # 个人资料命令
```

## ⚠️ 注意事项

1. **隐私声明**：本项目仅供学习研究使用，所有音频数据默认存储在本地，不会上传到任何服务器
2. **数据安全**：请妥善保管 `.env` 文件，不要泄露 Bot Token
3. **使用限制**：请遵守 Telegram 服务条款，不要滥用 Bot 功能
4. **结果仅供参考**：性别特征评估基于统计学模型，结果仅供参考，不作为医学诊断依据

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
