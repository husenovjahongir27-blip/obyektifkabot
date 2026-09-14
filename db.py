# -*- coding: utf-8 -*-
"""
Supabase (Postgres) bilan ishlash uchun yordamchi modul.
Foydalanuvchilarni va ular yaratgan hujjatlarni saqlaydi.
"""

import os

import asyncpg

DATABASE_URL = os.environ.get("DATABASE_URL")

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, ssl="require")
    return _pool


async def init_db():
    """Jadvallarni (agar mavjud bo'lmasa) yaratadi. Bot ishga tushganda bir marta chaqiriladi."""
    if not DATABASE_URL:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id BIGINT PRIMARY KEY,
                username TEXT,
                first_seen TIMESTAMPTZ DEFAULT now()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                full_name TEXT,
                fmt TEXT,
                created_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )


async def register_user(chat_id: int, username: str | None):
    if not DATABASE_URL:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (chat_id, username) VALUES ($1, $2)
            ON CONFLICT (chat_id) DO NOTHING
            """,
            chat_id,
            username,
        )


async def log_document(chat_id: int, full_name: str, fmt: str):
    if not DATABASE_URL:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO documents (chat_id, full_name, fmt) VALUES ($1, $2, $3)
            """,
            chat_id,
            full_name,
            fmt,
        )


async def get_user_documents(chat_id: int, limit: int = 15):
    if not DATABASE_URL:
        return []
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT full_name, fmt, created_at FROM documents
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            chat_id,
            limit,
        )
    return rows


async def get_user_count() -> int:
    if not DATABASE_URL:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS c FROM users")
    return row["c"]


async def get_document_count() -> int:
    if not DATABASE_URL:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS c FROM documents")
    return row["c"]
