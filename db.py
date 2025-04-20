from supabase import create_client, Client
from dotenv import load_dotenv
import os
import asyncio

load_dotenv(dotenv_path="C:/Users/owner/Desktop/DiscordBot/token.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_KEY: {key}")

supabase: Client = create_client(url, key)

async def add_user_if_not_exists(discord_id: str, name: str):
    res = await asyncio.to_thread(supabase.table("users").select("id").eq("discord_id", discord_id).execute)
    if len(res.data) == 0:
        insert_res = await asyncio.to_thread(supabase.table("users").insert({
            "discord_id": discord_id,
            "name": name
        }).execute)
        user_id = insert_res.data[0]["id"]

        await asyncio.to_thread(supabase.table("points_log").insert({
            "user_id": user_id,
            "points": 0,
            "reason": "初期ポイント"
        }).execute)

async def get_user_id(discord_id: str):
    res = await asyncio.to_thread(supabase.table("users").select("id").eq("discord_id", discord_id).execute)
    if len(res.data) == 0:
        return None
    return res.data[0]["id"]

async def add_points(discord_id: str, points: int, reason: str = "リアクションポイント"):
    user_id = await get_user_id(discord_id)
    if user_id is None:
        return

    await asyncio.to_thread(supabase.table("points_log").insert({
        "user_id": user_id,
        "points": points,
        "reason": reason
    }).execute)
