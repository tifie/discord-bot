from supabase import create_client, Client
from dotenv import load_dotenv
import os

# 環境変数を読み込み
load_dotenv()

# Supabase URL とキーの取得
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Supabaseクライアントを作成
supabase: Client = create_client(url, key)

# ユーザーが存在しない場合、ユーザー情報を追加
async def add_user_if_not_exists(discord_id: str, name: str):
    res = await supabase.table("users").select("id").eq("discord_id", discord_id).execute()  # 非同期で待機
    if len(res.data) == 0:
        insert_res = await supabase.table("users").insert({
            "discord_id": discord_id,
            "name": name
        }).execute()  # 非同期で待機
        user_id = insert_res.data[0]["id"]

        # 初期ポイントとして0を設定
        await supabase.table("points_log").insert({
            "user_id": user_id,
            "points": 0,
            "reason": "初期ポイント"
        }).execute()  # 非同期で待機

# ユーザーIDを取得
async def get_user_id(discord_id: str):
    res = await supabase.table("users").select("id").eq("discord_id", discord_id).execute()  # 非同期で待機
    if len(res.data) == 0:
        return None
    return res.data[0]["id"]

# ポイントを追加
async def add_points(discord_id: str, points: int, reason: str = "リアクションポイント"):
    user_id = await get_user_id(discord_id)  # 非同期で待機
    if user_id is None:
        return

    await supabase.table("points_log").insert({
        "user_id": user_id,
        "points": points,
        "reason": reason
    }).execute()  # 非同期で待機

# 総ポイントを取得
async def get_total_points(discord_id: str):
    user_id = await get_user_id(discord_id)  # 非同期で待機
    if user_id is None:
        return 0

    res = await supabase.table("points_log").select("points").eq("user_id", user_id).execute()  # 非同期で待機
    total = sum(entry["points"] for entry in res.data)
    return total

# ポイントを転送
async def transfer_points(from_discord_id: str, to_discord_id: str, points: int):
    from_user_id = await get_user_id(from_discord_id)  # 非同期で待機
    to_user_id = await get_user_id(to_discord_id)  # 非同期で待機

    if from_user_id is None or to_user_id is None:
        return False, "送信者または受信者が見つかりません。"

    res = await supabase.table("points_log").select("points").eq("user_id", from_user_id).execute()  # 非同期で待機
    total = sum(entry["points"] for entry in res.data)

    if total < points:
        return False, "ポイントが不足しています。"

    await supabase.table("points_log").insert({
        "user_id": from_user_id,
        "points": -points,
        "reason": "ポイント送信"
    }).execute()  # 非同期で待機

    await supabase.table("points_log").insert({
        "user_id": to_user_id,
        "points": points,
        "reason": "ポイント受け取り"
    }).execute()  # 非同期で待機

    return True, f"{points}ポイントを送信しました！"


# すでにリアクション済みか確認する関数
async def has_already_reacted(user_id: str, message_id: str, emoji: str):
    res = await supabase.table("reaction_logs").select("id")\
        .eq("user_id", user_id)\
        .eq("message_id", message_id)\
        .eq("emoji", emoji)\
        .execute()  # 非同期で待機

    if len(res.data) > 0:
        return True
    return False


# リアクションをログに記録（重複登録を防ぐ）
async def log_reaction(user_id: str, message_id: str, emoji: str):
    res = await supabase.table("reaction_logs").select("id")\
        .eq("user_id", user_id)\
        .eq("message_id", message_id)\
        .eq("emoji", emoji)\
        .execute()  # 非同期で待機

    if len(res.data) == 0:
        await supabase.table("reaction_logs").insert({
            "user_id": user_id,
            "message_id": message_id,
            "emoji": emoji
        }).execute()  # 非同期で待機

async def mark_name_change_purchased(user_id):
    """
    ユーザーが名前変更権を購入したことをデータベースに反映します。
    """
    # データベースの更新処理（例えば、has_renamedをTrueにするなど）
    user_data = await get_user_data(user_id)  # 仮にユーザーデータを取得する関数
    user_data["has_renamed"] = True  # 名前変更フラグをTrueに更新
    await save_user_data(user_data)  # 仮にデータ保存する関数
