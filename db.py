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
        # statement_cache_size=0 — Supabase'ning Connection Pooling (PgBouncer,
        # transaction rejimi) bilan mos ishlashi uchun kerak.
        _pool = await asyncpg.create_pool(
            DATABASE_URL, ssl="require", statement_cache_size=0
        )
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
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance BIGINT NOT NULL DEFAULT 0")

        # Eski jadvalda bo'lmasa — faylning o'zini saqlash uchun ustunlar qo'shamiz
        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_name TEXT")
        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_data BYTEA")


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


async def log_document(chat_id: int, full_name: str, fmt: str, file_name: str, file_data: bytes):
    if not DATABASE_URL:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO documents (chat_id, full_name, fmt, file_name, file_data)
            VALUES ($1, $2, $3, $4, $5)
            """,
            chat_id,
            full_name,
            fmt,
            file_name,
            file_data,
        )


async def get_user_documents(chat_id: int, limit: int = 15):
    if not DATABASE_URL:
        return []
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, full_name, fmt, created_at FROM documents
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            chat_id,
            limit,
        )
    return rows


async def get_document_file(doc_id: int, chat_id: int):
    """Foydalanuvchiga tegishli hujjatning fayl nomi va bayt ma'lumotini qaytaradi."""
    if not DATABASE_URL:
        return None
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT file_name, file_data FROM documents
            WHERE id = $1 AND chat_id = $2
            """,
            doc_id,
            chat_id,
        )
    return row


async def get_all_user_ids() -> list[int]:
    if not DATABASE_URL:
        return []
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT chat_id FROM users")
    return [r["chat_id"] for r in rows]


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


async def get_user_balance(chat_id: int) -> int:
    if not DATABASE_URL:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT balance FROM users WHERE chat_id = $1", chat_id)
    return int(row["balance"] or 0) if row else 0


async def get_total_income() -> int:
    """To'lov jadvali mavjud bo'lsa, tasdiqlangan to'lovlar yig'indisini qaytaradi."""
    if not DATABASE_URL:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='payments')"
        )
        if not exists:
            return 0
        row = await conn.fetchrow(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM payments "
            "WHERE status IN ('paid','success','confirmed')"
        )
    return int(row["total"] or 0)
