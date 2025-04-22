import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, AsyncClient

# 環境変数を読み込む
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabaseクライアント作成
supabase: AsyncClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 基本関数 ==========

async def add_user_if_not_exists(discord_id: str, discord_name: str):
    res = await supabase.table("users").select("id").eq("discord_id", discord_id).execute()
    if res.data:
        return res.data[0]
    return (await supabase.table("users").insert({
        "discord_id": discord_id,
        "discord_name": discord_name
    }).execute()).data[0]

async def get_user_id(discord_id: str):
    res = await supabase.table("users").select("id").eq("discord_id", discord_id).execute()
    if res.data:
        return res.data[0]["id"]
    return None

async def add_points(discord_id: str, points: int, reason: str = "リアクションポイント"):
    user_id = await get_user_id(discord_id)
    if not user_id:
        return
    await supabase.table("points_log").insert({
        "user_id": user_id,
        "points": points,
        "reason":
