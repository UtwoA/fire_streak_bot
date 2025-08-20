CREATE TABLE IF NOT EXISTS members (
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS daily_marks (
    chat_id BIGINT NOT NULL,
    mark_date DATE NOT NULL,
    user_id BIGINT NOT NULL,
    marked_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (chat_id, mark_date, user_id)
);

CREATE TABLE IF NOT EXISTS chat_state (
    chat_id BIGINT PRIMARY KEY,
    streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    status TEXT DEFAULT 'inactive',
    last_active_date DATE,
    frozen_type TEXT,
    thaw_required INTEGER DEFAULT 0,
    thaw_count INTEGER DEFAULT 0,
    pre_freeze_streak INTEGER DEFAULT 0
);
