from typing import Optional, List, Dict
from datetime import date

def compute_next_state(state: Optional[Dict], member_ids: List[int], marks_today: List[int], today: date) -> Dict:
    if not member_ids:
        return {'action': 'no_members'}

    if set(member_ids) != set(marks_today):
        return {'action': 'incomplete'}

    # No previous state
    if state is None:
        streak = 1
        return {'action': 'started', 'streak': streak, 'max_streak': streak}

    streak = state.get('streak', 0) or 0
    max_streak = state.get('max_streak', 0) or 0
    status = state.get('status', 'inactive')
    last_active_date = state.get('last_active_date')  # date or None
    frozen_type = state.get('frozen_type')
    thaw_required = state.get('thaw_required', 0) or 0
    thaw_count = state.get('thaw_count', 0) or 0
    pre_freeze_streak = state.get('pre_freeze_streak', 0) or 0

    if status == 'frozen':
        thaw_count += 1
        if thaw_count >= thaw_required:
            # thaw completed
            return {'action': 'thawed', 'streak': pre_freeze_streak, 'max_streak': max(max_streak, pre_freeze_streak)}
        return {'action': 'thaw_progress', 'thaw_count': thaw_count, 'thaw_required': thaw_required}

    if last_active_date is None:
        streak = 1
        max_streak = max(max_streak, streak)
        return {'action': 'started', 'streak': streak, 'max_streak': max_streak}

    delta_days = (today - last_active_date).days
    if delta_days == 0:
        return {'action': 'already_counted'}
    if delta_days == 1:
        streak += 1
        max_streak = max(max_streak, streak)
        return {'action': 'increment', 'streak': streak, 'max_streak': max_streak}
    skip_days = delta_days - 1
    if skip_days == 1:
        return {'action': 'frozen', 'type': 'short', 'thaw_required': 3, 'pre_freeze_streak': streak}
    if skip_days >= 2:
        if skip_days >= 30:
            return {'action': 'reset'}
        return {'action': 'frozen', 'type': 'long', 'thaw_required': 7, 'pre_freeze_streak': streak}
    return {'action': 'noop'}
