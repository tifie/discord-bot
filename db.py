import os
import asyncio
from dotenv import load_dotenv
from supabase._async.client import AsyncClient, create_client

# 環境変数を読み込み
load_dotenv()

# Supabase URL とキーの取得
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabaseクライアントを作成する非同期関数
async def create_supabase_client():
    return await create_client(SUPABASE_URL, SUPABASE_KEY)

# ユーザーが存在しない場合、ユーザー情報を追加
async def add_user_if_not_exists(supabase, discord_id: str, discord_name: str):
    res = await supabase.table("users").select("id").eq("discord_id", discord_id).execute()
    if res.data:
        return res.data[0]
    else:
        return await supabase.table("users").insert({
            "discord_id": discord_id,
            "discord_name": discord_name
        }).execute()

# ユーザーIDを取得
async def get_user_id(supabase, discord_id: str):
    res = await supabase.table("users").select("id").eq("discord_id", discord_id).execute()
    if not res.data:
        return None
    return res.data[0]["id"]

# ポイントを追加
async def add_points(supabase, discord_id: str, points: int, reason: str = "リアクションポイント"):
    user_id = await get_user_id(supabase, discord_id)
    if user_id is None:
        return
    await supabase.table("points_log").insert({
        "user_id": user_id,
        "points": points,
        "reason": reason
    }).execute()

# 総ポイントを取得
async def get_total_points(supabase, discord_id: str):
    user_id = await get_user_id(supabase, discord_id)
    if user_id is None:
        return 0
    res = await supabase.table("points_log").select("points").eq("user_id", user_id).execute()
    return sum(entry["points"] for entry in res.data)

# ポイントを転送
async def transfer_points(supabase, from_discord_id: str, to_discord_id: str, points: int):
    from_user_id = await get_user_id(supabase, from_discord_id)
    to_user_id = await get_user_id(supabase, to_discord_id)
    if from_user_id is None or to_user_id is None:
        return False, "送信者または受信者が見つかりません。"
    res = await supabase.table("points_log").select("points").eq("user_id", from_user_id).execute()
    total = sum(entry["points"] for entry in res.data)
    if total < points:
        return False, "ポイントが不足しています。"
    await supabase.table("points_log").insert({
        "user_id": from_user_id,
        "points": -points,
        "reason": "ポイント送信"
    }).execute()
    await supabase.table("points_log").insert({
        "user_id": to_user_id,
        "points": points,
        "reason": "ポイント受け取り"
    }).execute()
    return True, f"{points}ポイントを送信しました！"

# すでにリアクション済みか確認する関数
async def has_already_reacted(supabase, user_id: str, message_id: str, emoji: str):
    res = await supabase.table("reaction_logs").select("id")\
        .eq("user_id", user_id)\
        .eq("message_id", message_id)\
        .eq("emoji", emoji)\
        .execute()
    return bool(res.data)

# リアクションをログに記録（重複登録を防ぐ）
async def log_reaction(supabase, user_id: str, message_id: str, emoji: str):
    if not await has_already_reacted(supabase, user_id, message_id, emoji):
        await supabase.table("reaction_logs").insert({
            "user_id": user_id,
            "message_id": message_id,
            "emoji": emoji
        }).execute()

# ユーザーデータ取得
async def get_user_data(supabase, user_id: str):
    res = await supabase.table("users").select("*").eq("id", user_id).single().execute()
    return res.data

# ユーザーデータ保存（データベースに保存）
async def save_user_data(supabase, user_data: dict):
    await supabase.table("users").update(user_data).eq("id", user_data["id"]).execute()

# 名前変更を購入済みにマークする
async def mark_name_change_purchased(supabase, user_id: str):
    user_data = await get_user_data(supabase, user_id)
    if user_data.get("has_renamed"):
        return "⚠️ すでに名前を変更しています。一度きりの変更です。"
    user_data["has_renamed"] = True
    await save_user_data(supabase, user_data)
    return "✅ 名前変更が購入されました。"

# 非同期処理を実行
async def main():
    supabase = await create_supabase_client()  # Supabaseクライアントの作成
    await add_user_if_not_exists(supabase, "discord_id_example", "Example User")

if __name__ == "__main__":
    asyncio.run(main())
