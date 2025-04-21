import os
import discord
from discord.ext import commands
from discord import app_commands
from db import add_user_if_not_exists, add_points, get_total_points, transfer_points, has_already_reacted, log_reaction

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

# インテントの設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = MyBot(command_prefix="!", intents=intents)

# 対象チャンネルID
TARGET_CHANNEL_IDS = [
    1363171100359659620,   # ← ネタ
    1360987317229322410,   # クリップ
    1362883049104343211,   # 自慢
    1363192621698384112,   # 動物
    1363170014349496571,   # 飯
    1363192707207397546    # 他のチャンネル
]

# /mypointsコマンド
@bot.tree.command(name="mypoints", description="自分のポイントを確認します")
async def mypoints(interaction: discord.Interaction):
    await add_user_if_not_exists(str(interaction.user.id), interaction.user.display_name)
    points = await get_total_points(str(interaction.user.id))
    await interaction.response.send_message(f"あなたの現在のポイントは **{points}ポイント** です！", ephemeral=True)

# /givepointsコマンド
@bot.tree.command(name="givepoints", description="誰かにポイントを渡します")
@app_commands.describe(user="ポイントを渡したい相手", amount="渡すポイント数")
async def givepoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("1以上のポイントを指定してください。", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    receiver_id = str(user.id)

    # ポイントの移動
    success, message = await transfer_points(sender_id, receiver_id, amount)
    await interaction.response.send_message(message, ephemeral=True)

# リアクション追加イベント
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # 対象チャンネルかどうかを確認
    if payload.channel_id not in TARGET_CHANNEL_IDS:
        return

    # 自分のリアクションは無視
    if payload.user_id == bot.user.id:
        return

    # ユーザーとメッセージ情報を取得
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    if not user:
        return

    user_id = str(user.id)
    message_id = str(payload.message_id)
    emoji = str(payload.emoji)

    # すでにリアクションしていたらスキップ
    already_reacted = await has_already_reacted(user_id, message_id, emoji)
    if already_reacted:
        return

    # ログに記録（リアクション情報）
    await log_reaction(user_id, message_id, emoji)

    # ユーザー情報を追加し、ポイントを加算
    await add_user_if_not_exists(user_id, user.display_name)
    await add_points(user_id, 1)

    print(f"{user.display_name} にポイント追加しました！（リアクション in 対象チャンネル）")

if __name__ == "__main__":
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN が環境変数から取得できませんでした")
    bot.run(DISCORD_TOKEN)
