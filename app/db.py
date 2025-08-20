import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None

async def init_db_pool(dsn: str, min_size: int = 1, max_size: int = 10):
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
    return _pool

def get_db_pool():
    if _pool is None:
        raise RuntimeError('DB pool not initialized')
    return _pool

async def close_db_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
