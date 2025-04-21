from supabase import create_client, Client
from dotenv import load_dotenv
import os
import asyncpg

# 環境変数を読み込み（Northflankでは勝手に環境変数セットされてる）
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

async def add_user_if_not_exists(discord_id: str, name: str):
    res = supabase.table("users").select("id").eq("discord_id", discord_id).execute()
    if len(res.data) == 0:
        insert_res = supabase.table("users").insert({
            "discord_id": discord_id,
            "name": name
        }).execute()
        user_id = insert_res.data[0]["id"]

        supabase.table("points_log").insert({
            "user_id": user_id,
            "points": 0,
            "reason": "初期ポイント"
        }).execute()

async def add_points(discord_id: str, points: int, reason: str = "リアクションポイント"):
    user_id = get_user_id(discord_id)
    if user_id is None:
        return

    supabase.table("points_log").insert({
        "user_id": user_id,
        "points": points,
        "reason": reason
    }).execute()

def get_user_id(discord_id: str):
    res = supabase.table("users").select("id").eq("discord_id", discord_id).execute()
    if len(res.data) == 0:
        return None
    return res.data[0]["id"]

async def get_total_points(discord_id: str):
    user_id = get_user_id(discord_id)
    if user_id is None:
        return 0

    res = supabase.table("points_log").select("points").eq("user_id", user_id).execute()
    total = sum(entry["points"] for entry in res.data)
    return total

async def transfer_points(from_discord_id: str, to_discord_id: str, points: int):
    from_user_id = get_user_id(from_discord_id)
    to_user_id = get_user_id(to_discord_id)

    if from_user_id is None or to_user_id is None:
        return False

    res = supabase.table("points_log").select("points").eq("user_id", from_user_id).execute()
    total = sum(entry["points"] for entry in res.data)

    if total < points:
        return False

    supabase.table("points_log").insert({
        "user_id": from_user_id,
        "points": -points,
        "reason": "ポイント送信"
    }).execute()

    supabase.table("points_log").insert({
        "user_id": to_user_id,
        "points": points,
        "reason": "ポイント受け取り"
    }).execute()

    return True

# すでに反応したかどうか確認する関数
async def has_already_reacted(user_id: str, message_id: str, emoji: str) -> bool:
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        result = await conn.fetchrow("""
            SELECT 1 FROM reaction_logs
            WHERE user_id = $1 AND message_id = $2 AND emoji = $3
        """, user_id, message_id, emoji)
        return result is not None
    finally:
        await conn.close()

# 初めてのリアクションを記録（ポイント加算後に呼ぶとよい）
async def log_reaction(user_id: str, message_id: str, emoji: str):
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        await conn.execute("""
            INSERT INTO reaction_logs (user_id, message_id, emoji)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING
        """, user_id, message_id, emoji)
    finally:
        await conn.close()
