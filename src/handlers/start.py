from telegram import Update
from telegram.ext import ContextTypes
from src.database import get_or_create_user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    
    get_or_create_user(db, user.id, user.username, user.first_name)
    
    welcome_message = """
 **欢迎使用跨性别群体声音分析助手** 

我可以帮你分析语音的各种参数，包括：
- 基频与音高 (F0)
- 共振峰与音色 (F1/F2/F3)
- 频谱特征与能量
- 音质与稳定性指标
- 性别特征综合评估

 **使用方法**：
1. 发送语音消息（最长 2 分钟）
2. 回复该语音并发送 `/analyze` 进行简洁分析
3. 使用 `/expert` 获取专业分析和图表
4. 使用 `/settings` 调整分析参数

 **常用命令**：
`/help` - 显示帮助信息
`/history` - 查看历史分析记录
`/profile` - 查看个人档案
`/settings` - 调整设置

开始发送语音吧！
"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = """
 **命令帮助**

**基础命令**
`/start` - 启动机器人，显示欢迎信息
`/help` - 显示本帮助信息

**分析命令**
`/analyze` - 分析语音（回复语音消息使用）
`/expert` - 专业分析菜单（回复语音或记录使用）
`/history` - 查看历史分析记录
`/view <id>` - 查看指定记录的详细报告
`/compare <id1> <id2>` - 对比两次分析结果

**管理命令**
`/profile` - 查看个人档案和声音趋势
`/delete <id>` - 删除指定分析记录
`/delete_all` - 清空所有分析记录
`/settings` - 调整分析参数设置
`/reset_settings` - 重置所有设置为默认值

**使用示例**：
- 发送语音 → 回复 `/analyze` → 获取分析报告
- 发送 `/history` → 查看历史记录列表
- 发送 `/settings` → 进入设置菜单
"""
    
    await update.message.reply_text(help_message, parse_mode='Markdown')
