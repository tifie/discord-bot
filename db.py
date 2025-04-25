import os
import asyncio
from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()
# Supabaseクライアント作成
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ========== 基本関数 ==========

async def add_user_if_not_exists(discord_id: str, discord_name: str):
    # ユーザーがすでに存在するか確認
    user_id = await get_user_by(discord_id)

    # エラーが発生した場合のチェック（APIResponseオブジェクトの確認）
    if not user_id:
        try:
            res = supabase.table("users").insert({
                "discord_id": discord_id,
                "discord_name": discord_name,
            }).execute()
            user_id = res.data[0]["id"]

            supabase.table("points").insert({
                    "user_id": user_id,
                    "point": 0  # ポイント初期化
            }).execute()
        except Exception as e:
            raise Exception(f"ユーザーの追加に失敗しました。{e}")
        # ユーザーが存在しない場合、新規登録


        return user_id  # 新規ユーザーの情報を返す


    return user_id  # ユーザー情報を返す


async def add_points_to_user(discord_id: str, points: int):
    # ここにSupabaseやデータベースの処理を記述
    # 例:
    user_id = await get_user_by(discord_id)
    user_point = await get_point_by(user_id)

    if user_point:
        current_points = user_point
        new_points = current_points + points
        await supabase.table("points").update({"point": new_points}).eq("user_id", user_id).execute()
        return True
    return False


async def get_user_by(discord_id: str):
    res = supabase.table("users").select("id").eq("discord_id", discord_id).execute()  # await外す

    # ユーザーIDが見つかればそのIDを返す
    if res.data:
        return res.data[0]["id"]

    return None

async def get_point_by(user_id: any):
    res = supabase.table("points").select("point").eq("user_id", user_id).execute()

    if res.data:
        return res.data[0]["point"]

    return None

async def update_points(discord_id: str, points: int, reason: str = "リアクションポイント"):
    print(f"[update_points] 開始: discord_id={discord_id}, points={points}, reason={reason}")
    
    user_id = await get_user_by(discord_id)
    print(f"[update_points] ユーザーID取得: {user_id}")

    # ユーザーが見つからない場合は何もしない
    if not user_id:
        print("[update_points] ユーザーが見つかりません")
        return False

    user_point = await get_point_by(user_id)
    print(f"[update_points] 現在のポイント: {user_point}")

    # ポイント更新
    try:
        # ポイントを更新
        new_points = user_point + points
        print(f"[update_points] 新しいポイント: {new_points}")
        
        # ポイントを更新
        result = supabase.table("points").update({
            "point": new_points
        }).eq("user_id", user_id).execute()
        print(f"[update_points] ポイント更新結果: {result.data}")

        # ポイントログを挿入
        log_result = supabase.table("points_log").insert({
            "user_id": user_id,
            "point": points,
            "reason": reason
        }).execute()
        print(f"[update_points] ログ挿入結果: {log_result.data}")

        return True
    except Exception as e:
        print(f"[update_points] エラー発生: {str(e)}")
        return False

async def get_total_points(discord_id: str):
    print(f"[get_total_points] ユーザーID取得開始: {discord_id}")
    user_id = await get_user_by(discord_id)  # ここはawaitが必要
    print(f"[get_total_points] ユーザーID取得結果: {user_id}")

    if not user_id:
        print("[get_total_points] ユーザーIDが見つかりませんでした。0を返します。")
        return 0

    print(f"[get_total_points] ポイント情報取得を開始: user_id={user_id}")

    total = await get_point_by(user_id)

    print(f"[get_total_points] 合計ポイント: {total}")
    return total

# ========== ポイント関連 ==========
# == ポイント譲渡の変更
async def transfer_points(from_discord_id: str, to_discord_id: str, points: int):
    from_user_id = await get_user_by(from_discord_id)
    to_user_id = await get_user_by(to_discord_id)

    if not from_user_id or not to_user_id:
        return False, "送信者または受信者が見つかりません。"

    # 送信元と送信先のポイントの合計を取得
    from_point = await get_point_by(from_user_id)
    to_point = await get_point_by(to_user_id)

    if from_point < points:
        return False, "ポイントが不足しています。"

    # ポイントを徴収
    supabase.table("points").update({
        "point": from_point-points,
    }).eq("user_id", from_user_id).execute()

    # ポイントを付与
    supabase.table("points").update({
        "point": to_point+points,
    }).eq("user_id", to_user_id).execute()

    # ポイントを譲渡記録を残す
    supabase.table("points_log").insert([
        {"user_id": from_user_id, "points": -points, "reason": "ポイント送信"},
        {"user_id": to_user_id, "points": points, "reason": "ポイント受け取り"}
    ]).execute()

    return True, f"{points}ポイントを送信しました！"

# ========== リアクションログ関連 ==========

async def has_already_reacted(discord_id: str, message_id: str):
    user_id = await get_user_by(discord_id)

    res = supabase.table("reaction_log").select("user_id")\
        .eq("user_id", user_id).eq("message_id", message_id).execute()  # await外す

    return bool(res.data)

async def log_reaction(discord_id: str, message_id: str):
    # すでにリアクションが記録されていないかチェック
    user_id = await get_user_by(discord_id)
    if not await has_already_reacted(discord_id, message_id):
        supabase.table("reaction_log").insert({
            "user_id": user_id,
            "message_id": message_id,
        }).execute()  # await外す

# ========== ユーザー設定関連 ==========

async def get_user_data(discord_id: str):
    res = supabase.table("users").select("*").eq("discord_id", discord_id).single().execute()  # await外す
    return res.data

async def save_user_data(user_data: dict):
    supabase.table("users").update(user_data).eq("id", user_data["id"]).execute()  # await外す

async def mark_name_change_purchased(discord_id: str):
    user_data = await get_user_data(discord_id)  # ここはawaitが必要
    # if user_data.get("has_renamed"):
    #     return "⚠️ すでに名前を変更しています。一度きりの変更です。"
    # user_data["has_renamed"] = True
    await save_user_data(user_data)  # ここもawaitが必要
    return "✅ 名前変更が購入されました。"
    # ユーザー情報を取得し、total_points と points の整合性を取る

async def fix_user_points(discord_id: str):
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

async def save_user_color(user_id: str, color_code: str):
    """ユーザーの色情報を保存する"""
    try:
        # 色情報を保存
        supabase.table("user_colors").upsert({
            "user_id": user_id,
            "color_code": color_code
        }).execute()
        return True
    except Exception as e:
        print(f"色情報の保存に失敗: {e}")
        return False

async def get_user_color(user_id: str):
    """ユーザーの色情報を取得する"""
    try:
        res = supabase.table("user_colors").select("color_code").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]["color_code"]
        return None
    except Exception as e:
        print(f"色情報の取得に失敗: {e}")
        return None

async def update_user_color(user_id: str, color_code: str):
    """ユーザーの色情報を更新する"""
    try:
        # 色情報を更新
        supabase.table("user_colors").update({
            "color_code": color_code
        }).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"色情報の更新に失敗: {e}")
        return False

# # ========== テスト用 ==========

# async def main():
#     await add_user_if_not_exists("test_discord_id", "TestUser")
#     points = await get_total_points("test_discord_id")
#     print(f"現在のポイント: {points}")

# if __name__ == "__main__":
#     asyncio.run(main())
