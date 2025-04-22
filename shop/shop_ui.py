import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from db import (
    add_user_if_not_exists,
    add_points,
    get_total_points,
    transfer_points,
    has_already_reacted,
    log_reaction
)
from supabase import create_client, Client
from shop.shop_ui import send_shop_category
from dotenv import load_dotenv


# .env から環境変数読み込み
load_dotenv()

# Supabase クライアント作成
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Botクラス定義
class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

# Intents設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

# Botインスタンス作成
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

# `/mypoints` コマンド
@bot.tree.command(name="mypoints", description="自分のNPを確認します")
async def mypoints(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await add_user_if_not_exists(str(interaction.user.id), interaction.user.display_name)
    points = await get_total_points(str(interaction.user.id))
    await interaction.followup.send(f"現在のNP： **{points}NP** ", ephemeral=True)

# `/givepoints` コマンド
@bot.tree.command(name="givepoints", description="誰かにNPを渡します")
@app_commands.describe(user="NPを渡す相手", amount="渡すNP数")
async def givepoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    await interaction.response.defer(ephemeral=True)

    if amount <= 0:
        await interaction.followup.send("1以上のNPを指定してください。", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    receiver_id = str(user.id)

    success, message = await transfer_points(sender_id, receiver_id, amount)
    await interaction.followup.send(message, ephemeral=True)

    try:
        await user.send(f"{interaction.user.display_name} さんから **{amount}NP** を受け取りました！")
    except discord.Forbidden:
        await interaction.followup.send(f"{user.display_name} さんにDMを送れませんでした。", ephemeral=True)

# リアクションイベント処理
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.channel_id not in TARGET_CHANNEL_IDS or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    user = guild.get_member(payload.user_id)
    if not user:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return

    if not message or message.author.bot:
        return

    user_id = str(user.id)
    message_id = str(payload.message_id)
    emoji = str(payload.emoji)
    message_author_id = str(message.author.id)

    if await has_already_reacted(user_id, message_id, emoji):
        return

    await log_reaction(user_id, message_id, emoji)
    await add_user_if_not_exists(message_author_id, message.author.display_name)
    await add_points(message_author_id, 10)
    print(f"{message.author.display_name} にポイント追加！（{emoji}）")

# `/shop_profile` コマンド
@bot.tree.command(name="shop_profile", description="プロフィール系ショップを表示します")
@app_commands.checks.has_permissions(administrator=True)
async def send_profile_shop(interaction: discord.Interaction):
  
    await send_shop_category(interaction, "プロフ変更系")

# モーダル定義（名前変更）
class RenameModal(Modal, title="名前を変更します！"):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.user = user

        self.new_name = TextInput(
            label="新しい名前",
            placeholder="ここに新しいニックネームを入力してね",
            max_length=32
        )
        self.add_item(self.new_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.user.edit(nick=self.new_name.value)
            await interaction.response.send_message(
                f"✅ ニックネームを「{self.new_name.value}」に変更したよ！", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ ニックネームを変更する権限がないみたい…", ephemeral=True)

# 起動処理
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN が .env に設定されていません")
    bot.run(token)
