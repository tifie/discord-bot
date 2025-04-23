import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# 環境変数を読み込む
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabaseクライアント作成
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== 基本関数 ==========

async def add_user_if_not_exists(supabase, discord_id: str, discord_name: str):
    # ユーザーがすでに存在するか確認
    res = supabase.table("users").select("id", "points").eq("discord_id", discord_id).execute()

    # エラーが発生した場合のチェック（APIResponseオブジェクトの確認）
    if not res.data:
        # ユーザーが存在しない場合、新規登録
        inserted_user = supabase.table("users").insert({
            "discord_id": discord_id,
            "discord_name": discord_name,
            "points": 0  # ポイント初期化
        }).execute()

        # 挿入後のデータが返される
        if inserted_user.data:
            return inserted_user.data[0]  # 新規ユーザーの情報を返す
        else:
            raise Exception("ユーザーの追加に失敗しました。")

    return res.data[0]  # ユーザー情報を返す




async def get_user_id(discord_id: str):
    res = supabase.table("users").select("id").eq("discord_id", discord_id).execute()  # await外す
    
    # ユーザーIDが見つかればそのIDを返す
    if res.data:
        return res.data[0]["id"]
    
    return None

async def add_points(discord_id: str, points: int, reason: str = "リアクションポイント"):
    user_id = await get_user_id(discord_id)
    
    # ユーザーが見つからない場合は何もしない
    if not user_id:
        return
    
    # ポイントログを挿入
    supabase.table("points_log").insert({
        "user_id": user_id,
        "points": points,
        "reason": reason
    }).execute()  # await外す

async def get_total_points(discord_id: str):
    print(f"[get_total_points] ユーザーID取得開始: {discord_id}")
    user_id = await get_user_id(discord_id)  # ここはawaitが必要
    print(f"[get_total_points] ユーザーID取得結果: {user_id}")

    if not user_id:
        print("[get_total_points] ユーザーIDが見つかりませんでした。0を返します。")
        return 0

    print(f"[get_total_points] ポイント情報取得を開始: user_id={user_id}")
    try:
        res = supabase.table("points_log").select("points").eq("user_id", user_id).execute()  # await外す
        print(f"[get_total_points] ポイント情報取得完了: データ件数 = {len(res.data)}")
    except Exception as e:
        print(f"❌ [get_total_points] エラー発生: {e}")
        return 0

    total = sum(entry["points"] for entry in res.data)
    print(f"[get_total_points] 合計ポイント: {total}")
    return total
    # ユーザー情報を取得し、total_points と points の整合性を取る
async def fix_user_points(supabase, discord_id):
    res = await supabase.table("users").select("id", "points", "total_points").eq("discord_id", discord_id).execute()
    user_data = res.data[0] if res.data else None
    
    if user_data:
        # points と total_points の整合性が取れていない場合、total_points を更新
        if user_data["points"] != user_data.get("total_points", 0):
            updated_user = await supabase.table("users").update({"total_points": user_data["points"]}).eq("discord_id", discord_id).execute()
            return updated_user
        else:
            return None  # 整合性が取れている場合
    else:
        return None  # ユーザーが見つからない場合


# ========== ポイント関連 ==========

async def transfer_points(from_discord_id: str, to_discord_id: str, points: int):
    from_user_id = await get_user_id(from_discord_id)
    to_user_id = await get_user_id(to_discord_id)
    
    if not from_user_id or not to_user_id:
        return False, "送信者または受信者が見つかりません。"

    # 送信者のポイントの合計を取得
    res = supabase.table("points_log").select("points").eq("user_id", from_user_id).execute()  # await外す
    total = sum(entry["points"] for entry in res.data)
    
    if total < points:
        return False, "ポイントが不足しています。"

    # ポイントを送信
    supabase.table("points_log").insert([
        {"user_id": from_user_id, "points": -points, "reason": "ポイント送信"},
        {"user_id": to_user_id, "points": points, "reason": "ポイント受け取り"}
    ]).execute()  # await外す

    return True, f"{points}ポイントを送信しました！"

# ========== リアクションログ関連 ==========

async def has_already_reacted(user_id: str, message_id: str, emoji: str):
    res = supabase.table("reaction_logs").select("id")\
        .eq("user_id", user_id).eq("message_id", message_id).eq("emoji", emoji).execute()  # await外す
    
    return bool(res.data)

async def log_reaction(user_id: str, message_id: str, emoji: str):
    # すでにリアクションが記録されていないかチェック
    if not await has_already_reacted(user_id, message_id, emoji):
        supabase.table("reaction_logs").insert({
            "user_id": user_id,
            "message_id": message_id,
            "emoji": emoji
        }).execute()  # await外す

# ========== ユーザー設定関連 ==========

async def get_user_data(user_id: str):
    res = supabase.table("users").select("*").eq("id", user_id).single().execute()  # await外す
    return res.data

async def save_user_data(user_data: dict):
    supabase.table("users").update(user_data).eq("id", user_data["id"]).execute()  # await外す

async def mark_name_change_purchased(user_id: str):
    user_data = await get_user_data(user_id)  # ここはawaitが必要
    if user_data.get("has_renamed"):
        return "⚠️ すでに名前を変更しています。一度きりの変更です。"
    user_data["has_renamed"] = True
    await save_user_data(user_data)  # ここもawaitが必要
    return "✅ 名前変更が購入されました。"
    # ユーザー情報を取得し、total_points と points の整合性を取る
async def fix_user_points(supabase, discord_id):
    res = await supabase.table("users").select("id", "points", "total_points").eq("discord_id", discord_id).execute()
    user_data = res.data[0] if res.data else None
    
    if user_data:
        # points と total_points の整合性が取れていない場合、total_points を更新
        if user_data["points"] != user_data.get("total_points", 0):
            updated_user = await supabase.table("users").update({"total_points": user_data["points"]}).eq("discord_id", discord_id).execute()
            return updated_user
        else:
            return None  # 整合性が取れている場合
    else:
        return None  # ユーザーが見つからない場合


# ========== テスト用 ==========

async def main():
    await add_user_if_not_exists("test_discord_id", "TestUser")
    points = await get_total_points("test_discord_id")
    print(f"現在のポイント: {points}")

if __name__ == "__main__":
    asyncio.run(main())
