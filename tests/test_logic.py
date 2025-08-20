from datetime import date, timedelta
from app.logic import compute_next_state

def test_start_new():
    res = compute_next_state(None, [1,2], [1,2], date(2025,1,1))
    assert res['action']=='started' and res['streak']==1

def test_increment():
    state = {'streak':1, 'max_streak':1, 'status':'active', 'last_active_date': date(2025,1,1)}
    res = compute_next_state(state, [1,2], [1,2], date(2025,1,2))
    assert res['action']=='increment' and res['streak']==2

def test_short_freeze():
    state = {'streak':3, 'max_streak':3, 'status':'active', 'last_active_date': date(2025,1,1)}
    res = compute_next_state(state, [1,2], [1,2], date(2025,1,3))  # skip 1 day -> freeze short
    assert res['action']=='frozen' and res['type']=='short' and res['thaw_required']==3

def test_long_freeze():
    state = {'streak':5, 'max_streak':5, 'status':'active', 'last_active_date': date(2025,1,1)}
    res = compute_next_state(state, [1,2], [1,2], date(2025,1,4))  # skip 2 days -> long
    assert res['action']=='frozen' and res['type']=='long' and res['thaw_required']==7
