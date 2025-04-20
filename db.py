async def get_total_points(discord_id: str) -> int:
    user_id = await get_user_id(discord_id)
    if user_id is None:
        return 0

    user_data = await asyncio.to_thread(
        lambda: supabase.table("users").select("total_points").eq("id", user_id).single().execute()
    )
    return user_data.data.get("total_points", 0)

async def transfer_points(sender_discord_id: str, receiver_discord_id: str, amount: int):
    sender_id = await get_user_id(sender_discord_id)
    receiver_id = await get_user_id(receiver_discord_id)

    if sender_id is None or receiver_id is None:
        return False, "送信者または受信者が見つかりませんでした。"

    # 送信者のポイント確認
    sender_data = await asyncio.to_thread(
        lambda: supabase.table("users").select("total_points").eq("id", sender_id).single().execute()
    )
    sender_points = sender_data.data.get("total_points", 0)

    if sender_points < amount:
        return False, "ポイントが足りません。"

    # ポイント移動ログ
    await asyncio.to_thread(
        lambda: supabase.table("points_log").insert([
            {"user_id": sender_id, "points": -amount, "reason": "他ユーザーへのポイント譲渡"},
            {"user_id": receiver_id, "points": amount, "reason": "他ユーザーからのポイント受け取り"}
        ]).execute()
    )

    # 合計ポイントを更新
    await asyncio.to_thread(
        lambda: supabase.table("users").update({"total_points": sender_points - amount}).eq("id", sender_id).execute()
    )
    receiver_data = await asyncio.to_thread(
        lambda: supabase.table("users").select("total_points").eq("id", receiver_id).single().execute()
    )
    receiver_points = receiver_data.data.get("total_points", 0)
    await asyncio.to_thread(
        lambda: supabase.table("users").update({"total_points": receiver_points + amount}).eq("id", receiver_id).execute()
    )

    return True, f"{amount}ポイントを {receiver_discord_id} に渡しました！"
