import os
import discord
from discord.ext import commands
from discord import app_commands
from db import add_user_if_not_exists, add_points, get_total_points, transfer_points, has_already_reacted, log_reaction
import asyncpg  # 追加
from dotenv import load_dotenv  # 追加

# .envファイルから環境変数を読み込む
load_dotenv()

# データベース接続用関数（追加）
async def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL が環境変数から取得できませんでした")
    connection = await asyncpg.connect(database_url)
    return connection

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
@app_commands.describe(user="ポイントを渡したい相手", amount="渡す_
