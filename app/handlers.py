import asyncio
from datetime import datetime, date
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from .db import get_db_pool
from .utils import mention_html, get_today, set_fake_today
from .logic import compute_next_state

TZ = ZoneInfo('Europe/Moscow')

async def members_root(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return
    args = context.args
    if not args:
        return await members_list(update, context)
    sub = args[0].lower()
    if sub in ('add', 'добавить'):
        return await members_add(update, context)
    if sub in ('remove', 'удалить', 'rm'):
        return await members_remove(update, context)
    return

async def members_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None or update.effective_user is None:
        return
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO members(chat_id,user_id,username,first_name)
               VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING""",
            update.effective_chat.id,
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name
        )
    await update.message.reply_text(
        f"{mention_html(update.effective_user.id, update.effective_user.first_name)} добавлен",
        parse_mode='HTML'
    )

async def members_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None or update.effective_user is None:
        return
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM members WHERE chat_id=$1 AND user_id=$2",
            update.effective_chat.id,
            update.effective_user.id
        )
    await update.message.reply_text(
        f"{mention_html(update.effective_user.id, update.effective_user.first_name)} удалён",
        parse_mode='HTML'
    )

async def members_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, username, first_name FROM members WHERE chat_id=$1 ORDER BY added_at",
            update.effective_chat.id
        )
    if not rows:
        await update.message.reply_text('Список участников пуст')
        return
    mentions = [mention_html(r['user_id'], r['first_name'] or r['username'] or str(r['user_id'])) for r in rows]
    await update.message.reply_text('Участники:\n' + '\n'.join(mentions), parse_mode='HTML')

async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM chat_state WHERE chat_id=$1", update.effective_chat.id)
    if not row:
        text = 'Неактивен\nТекущая серия: 0 дней\nМаксимальная серия: 0 дней'
        await update.message.reply_text(text)
        return
    status = row['status']
    streak = row['streak'] or 0
    max_s = row['max_streak'] or 0
    from .utils import status_text
    s = status_text(status, streak)
    await update.message.reply_text(f"{s}\nТекущая серия: {streak} дней\nМаксимальная серия: {max_s} дней")

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None or update.effective_user is None or update.message is None:
        return
    if update.effective_user.is_bot:
        return
    text = update.message.text or ''
    if text.startswith('/'):
        return
    pool = get_db_pool()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    today = get_today()
    async with pool.acquire() as conn:
        members = await conn.fetch(
            "SELECT user_id, first_name FROM members WHERE chat_id=$1 ORDER BY added_at",
            chat_id
        )
        if not members:
            return
        member_ids = [r['user_id'] for r in members]
        if user_id not in member_ids:
            return
        await conn.execute(
            "INSERT INTO daily_marks(chat_id, mark_date, user_id) VALUES($1,$2,$3) ON CONFLICT DO NOTHING",
            chat_id, today, user_id
        )
        marks = await conn.fetch(
            "SELECT user_id FROM daily_marks WHERE chat_id=$1 AND mark_date=$2",
            chat_id, today
        )
        marked = [r['user_id'] for r in marks]
        remaining = [mid for mid in member_ids if mid not in marked]
        if remaining:
            id_to_name = {r['user_id']: r['first_name'] or str(r['user_id']) for r in members}
            rem_mentions = ' '.join(mention_html(rid, id_to_name.get(rid, '')) for rid in remaining[:5])
            if len(remaining) > 5:
                rem_mentions += f' и ещё {len(remaining)-5} участников'
            await update.message.reply_text(
                f"{mention_html(user_id, update.effective_user.first_name)} отметился, ждём ещё: {rem_mentions}",
                parse_mode='HTML'
            )
            return

        row = await conn.fetchrow("SELECT * FROM chat_state WHERE chat_id=$1", chat_id)
        state = dict(row) if row else None
        if state and state.get('last_active_date') is not None:
            state['last_active_date'] = state['last_active_date']

        result = compute_next_state(state, member_ids, marked, today)
        action = result.get('action')

        if action in ('increment', 'started'):
            streak = result.get('streak')
            max_s = result.get('max_streak', streak)
            await conn.execute(
                """INSERT INTO chat_state(chat_id, streak, max_streak, status, last_active_date)
                   VALUES($1,$2,$3,$4,$5)
                   ON CONFLICT(chat_id) DO UPDATE
                   SET streak=EXCLUDED.streak,
                       max_streak=EXCLUDED.max_streak,
                       status='active',
                       last_active_date=EXCLUDED.last_active_date""",
                chat_id, streak, max_s, 'active', today
            )
            await update.message.reply_text(
                f"Поздравляем!\nСерия из {streak} дней продолжается!",
                parse_mode='HTML'
            )
            return

        if action == 'thaw_progress':
            thaw_count = result.get('thaw_count')
            thaw_required = result.get('thaw_required')
            await conn.execute(
                "UPDATE chat_state SET thaw_count=$2 WHERE chat_id=$1",
                chat_id, thaw_count
            )
            await update.message.reply_text(
                f"Идёт разморозка: {thaw_count}/{thaw_required}",
                parse_mode='HTML'
            )
            return

        if action == 'thawed':
            streak = result.get('streak')
            await conn.execute(
                """UPDATE chat_state
                   SET streak=$2,
                       max_streak=$3,
                       status='active',
                       last_active_date=$4,
                       frozen_type=NULL,
                       thaw_required=0,
                       thaw_count=0,
                       pre_freeze_streak=0
                   WHERE chat_id=$1""",
                chat_id, streak, result.get('max_streak', streak), today
            )
            await update.message.reply_text(
                f"Огонёк разморожен. Серия восстановлена: {streak} дней",
                parse_mode='HTML'
            )
            return

        if action == 'frozen':
            tr = result.get('thaw_required')
            ftype = result.get('type')
            pre = result.get('pre_freeze_streak', 0)
            await conn.execute(
                """INSERT INTO chat_state(chat_id, status, frozen_type, thaw_required, thaw_count, pre_freeze_streak)
                   VALUES($1,$2,$3,$4,$5,$6)
                   ON CONFLICT(chat_id) DO UPDATE
                   SET status='frozen',
                       frozen_type=EXCLUDED.frozen_type,
                       thaw_required=EXCLUDED.thaw_required,
                       thaw_count=0,
                       pre_freeze_streak=EXCLUDED.pre_freeze_streak""",
                chat_id, 'frozen', ftype, tr, 0, pre
            )
            await update.message.reply_text(
                f"Огонёк заморожен. Для разморозки нужно {tr} подряд дней",
                parse_mode='HTML'
            )
            return

        if action == 'reset':
            await conn.execute(
                """INSERT INTO chat_state(chat_id, status, streak, max_streak, thaw_required, thaw_count, frozen_type, pre_freeze_streak)
                   VALUES($1,$2,0,0,0,0,NULL,0)
                   ON CONFLICT(chat_id) DO UPDATE
                   SET status='reset',
                       streak=0,
                       thaw_required=0,
                       thaw_count=0,
                       frozen_type=NULL,
                       pre_freeze_streak=0""",
                chat_id, 'reset'
            )
            await update.message.reply_text(
                "Огонёк потух и сброшен",
                parse_mode='HTML'
            )
            return


from telegram import ChatMember, ChatMemberAdministrator, ChatMemberOwner

async def set_date_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None or update.effective_user is None or update.message is None:
        return

    # Проверка прав: владелец или админ чата
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if not isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
        await update.message.reply_text("⛔ Эта команда доступна только администратору")
        return

    if not context.args:
        set_fake_today(None)
        await update.message.reply_text("📅 Дата сброшена — теперь используется реальная")
        return

    try:
        new_date = date.fromisoformat(context.args[0])
    except Exception:
        await update.message.reply_text("⚠️ Формат даты: YYYY-MM-DD")
        return

    set_fake_today(new_date)
    await update.message.reply_text(f"✅ Установлена тестовая дата: {new_date}")
