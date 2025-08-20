# app/main.py
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from app.config import settings
from app.db import init_db_pool, close_db_pool
from app.handlers import members_root, streak_cmd, members_add, members_remove, on_message
from .handlers import set_date_cmd

async def main() -> None:
    await init_db_pool(settings.DATABASE_URL)

    app = ApplicationBuilder().token(settings.BOT_TOKEN).build()

    app.add_handler(CommandHandler('members', members_root))
    app.add_handler(CommandHandler('streak', streak_cmd))
    app.add_handler(CommandHandler('members_add', members_add))
    app.add_handler(CommandHandler('members_remove', members_remove))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), on_message))

    app.add_handler(CommandHandler("setdate", set_date_cmd))

    stop_event = asyncio.Event()

    async def _shutdown():
        stop_event.set()

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        # Ожидание прерывания (Ctrl+C) — корректная замена отсутствующей app.idle()
        await stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            await app.updater.stop()
        except Exception:
            pass
        try:
            await app.stop()
        except Exception:
            pass
        await close_db_pool()

if __name__ == '__main__':
    asyncio.run(main())
