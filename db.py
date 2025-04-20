from supabase import create_client, Client
from dotenv import load_dotenv
import os

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
