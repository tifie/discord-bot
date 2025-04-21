import os
import discord
from discord.ext import commands
from discord import app_commands
from db import add_user_if_not_exists, add_points, get_total_points, transfer_points

# 監視したいチャンネルID（ここを自分のサーバーのチャンネルIDに置き換えてね！）
TARGET_CHANNEL_ID = 123456789012345678  # ← チャンネルIDをここに！

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

# インテント設定（メッセージ・リアクション・メンバーなどを取得するため）
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = MyBot(command_prefix="!", intents=intents)

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

    success, message = await transfer_points(sender_id, receiver_id, amount)
    await interaction.response.send_message(message, ephemeral=True)

# リアクションイベント：特定チャンネルのみでポイント加算
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.channel_id != TARGET_CHANNEL_ID:
        return  # 指定チャンネル以外は無視

    if payload.user_id == bot.user.id:
        return  # Bot自身のリアクションは無視

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not user:
        return

    await add_user_if_not_exists(str(user.id), user.display_name)
    await add_points(str(user.id), 1)  # リアクション1つで1ポイント加_
