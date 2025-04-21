import os
import discord
from discord.ext import commands
from discord import app_commands
from db import add_user_if_not_exists, add_points, get_total_points, transfer_points, has_already_reacted, log_reaction
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Supabaseクライアント作成
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

# Discord Bot 設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = MyBot(command_prefix="!", intents=intents)

# 対象チャンネルID
TARGET_CHANNEL_IDS = [
    1363171100359659620,
    1360987317229322410,
    1362883049104343211,
    1363192621698384112,
    1363170014349496571,
    1363192707207397546
]

@bot.tree.command(name="mypoints", description="自分のポイントを確認します")
async def mypoints(interaction: discord.Interaction):
    await add_user_if_not_exists(str(interaction.user.id), interaction.user.display_name)
    points = await get_total_points(str(interaction.user.id))
    await interaction.response.send_message(f"あなたの現在のポイントは **{points}ポイント** です！", ephemeral=True)

@bot.tree.command(name="givepoints", description="誰かにポイントを渡します")
@app_commands.describe(user="ポイントを渡す相手", amount="渡すポイント数")
async def givepoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("1以上のポイントを指定してください。", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    receiver_id = str(user.id)

    success, message = await transfer_points(sender_id, receiver_id, amount)
    await interaction.response.send_message(message, ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.channel_id not in TARGET_CHANNEL_IDS or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    if not user:
        return

    user_id = str(user.id)
    message_id = str(payload.message_id)
    emoji = str(payload.emoji)

    # メッセージをしたユーザーを取得
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    if not message:
        return

    message_author_id = str(message.author.id)

    # ユーザーがすでに反応していた場合、処理を中止
    if await has_already_reacted(user_id, message_id, emoji):
        return

    # ログにリアクションを記録
    await log_reaction(user_id, message_id, emoji)

    # メッセージをしたユーザーに10ポイント追加
    await add_user_if_not_exists(message_author_id, message.author.display_name)
    await add_points(message_author_id, 10)  # 1リアクションにつき10ポイントを追加
    print(f"{message.author.display_name} にポイント追加！（{emoji}）")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN が .env に設定されていません")
    bot.run(token)
