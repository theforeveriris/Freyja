from telegram import Update
from telegram.ext import ContextTypes
import asyncio


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    current_task = context.user_data.get('current_task')
    if current_task and not current_task.done():
        current_task.cancel()
        context.user_data['cancelled'] = True
        await update.message.reply_text("已取消当前正在运行的任务！")
    else:
        await update.message.reply_text("当前没有正在运行的任务。")


async def run_analysis_task(update_obj, context, coro_func, *args):
    user_id = update_obj.from_user.id if hasattr(update_obj, 'from_user') else update_obj.effective_user.id

    task = asyncio.create_task(coro_func(*args))
    context.user_data['current_task'] = task
    context.user_data['cancelled'] = False

    try:
        result = await task
        return result
    except asyncio.CancelledError:
        return None
    finally:
        context.user_data.pop('current_task', None)
