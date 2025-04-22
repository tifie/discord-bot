async def add_user_if_not_exists(discord_id: str, discord_name: str):
    try:
        # Supabaseからデータを非同期に取得
        res = await supabase.table("users").select("id").eq("discord_id", discord_id).execute()
        
        # res.dataがリスト（または辞書）として返されるので、そこから必要なデータを取り出す
        if res.data:  # ユーザーが既に存在する場合
            return res.data[0]  # idなどの情報を返す
        else:
            # ユーザーが存在しない場合は新規追加などの処理を行う
            return await supabase.table("users").insert({
                "discord_id": discord_id,
                "discord_name": discord_name
            }).execute()
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None  # エラーが発生した場合はNoneを返す

async def get_total_points(discord_id: str):
    try:
        user_id = await get_user_id(discord_id)
        if user_id is None:
            return 0

        res = await supabase.table("points_log").select("points").eq("user_id", user_id).execute()
        total = sum(entry["points"] for entry in res.data)
        return total

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 0  # エラーが発生した場合は0を返す

# 他の関数でも同様にエラーハンドリングを追加することを検討してください
