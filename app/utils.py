def mention_html(user_id: int, name: str) -> str:
    safe = (name or '').replace('<','').replace('>','')
    return f'<a href="tg://user?id={user_id}">{safe}</a>'

def status_text(status: str, streak: int) -> str:
    if status == 'frozen':
        return 'Заморожен 🧊'
    elif status == 'reset':
        return 'Потух 💔'
    else:
        if streak < 1:
            return "Неактивен 🥺"
        elif 0 < streak < 7:
            return "Искра ✨"
        elif streak < 15:
            return "Огонёчек 🔅"
        elif streak < 30:
            return "Малыш 🔥"
        elif streak < 60:
            return "Растущий 🌱"
        elif streak < 90:
            return "Пылающий 🔥🔥"
        elif streak < 180:
            return "Феникс 🐣"
        else:
            return "Солнце ☀️"

# utils.py
from datetime import date, datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Europe/Moscow")
_force_today: date | None = None

def set_fake_today(d: date | None):
    global _force_today
    _force_today = d

def get_today():
    if _force_today:
        return _force_today
    return datetime.now(_TZ).date()
