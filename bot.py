import os
from logging import info
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from db import add_user_if_not_exists, add_points, get_total_points, add_points_to_user, transfer_points, has_already_reacted, log_reaction, get_user_by, get_point_by
from dotenv import load_dotenv

from shop.shop_ui import ShopButton

# 環境変数を読み込み
load_dotenv()

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

@bot.tree.command(name="mypoints", description="自分のnpを確認します")
async def mypoints(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # ログを追加
    print(f"mypoints コマンドが呼ばれました。discord_id: {interaction.user.id}, discord_name: {interaction.user.display_name}")

    try:
        await add_user_if_not_exists(str(interaction.user.id), interaction.user.display_name)
    except Exception as e:
        print(f"add_user_if_not_exists 呼び出し時にエラー: {e}")

    # 修正: get_total_points を supabase とユーザーIDで呼び出し
    points = await get_total_points(str(interaction.user.id))  # 修正箇所
    await interaction.followup.send(f"現在のnp： **{points}NP** ", ephemeral=True)


@bot.tree.command(name="givepoints", description="誰かのnpを渡します")
@app_commands.describe(user="NPを渡す相手", amount="渡すNP数")
async def givepoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    await interaction.response.defer(ephemeral=True)

    if amount <= 0:
        await interaction.followup.send("1以上のnpを指定してください。", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    receiver_id = str(user.id)

    # ✅ supabase は不要
    success, message = await transfer_points(sender_id, receiver_id, amount)
    await interaction.followup.send(message, ephemeral=True)

    try:
        await user.send(f"{interaction.user.display_name} さんから **{amount}NP** を受け取りました！")
    except discord.Forbidden:
        await interaction.followup.send(
            f"{user.display_name} さんにDMを送れなかったので、通知できませんでした。",
            ephemeral=True
        )

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.channel_id not in TARGET_CHANNEL_IDS or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    if not user:
        return

    discord_id = str(user.id)
    message_id = str(payload.message_id)
    emoji = str(payload.emoji)

    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if not message:
        return

    message_author_id = str(message.author.id)

    info("userは存在すか")
    await add_user_if_not_exists(message_author_id, message.author.display_name)

    info("すでにリアクションをしたメッセージか")
    if await has_already_reacted(discord_id, message_id):
        return

    info("リアクションしたメッセージを記録")
    await log_reaction(discord_id, message_id)

    await add_points(message_author_id, 10)
    info(f"{message.author.display_name} にポイント追加！（{emoji}）")

@bot.tree.command(name="shop_profile", description="プロフィール系ショップを表示します")
@app_commands.checks.has_permissions(administrator=True)
async def shop_profile(interaction: discord.Interaction):
    from shop.shop_ui import send_shop_category
    await send_shop_category(interaction, "プロフ変更系")

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

@bot.command()
async def add_points(ctx: commands.Context, points: int):
    """自分に指定したポイントを加算するコマンド"""
    user_id = str(ctx.author.id)  # コマンドを実行したユーザーのIDを取得
    success = await add_points_to_user(user_id, points)  # add_points_to_user関数でDBに反映

    if success:
        await ctx.send(f"✅ {points}ポイントを {ctx.author.display_name} さんに付与しました！")
    else:
        await ctx.send("⚠️ ポイントの付与に失敗しました。")



if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN が .env に設定されていません")
    bot.run(token)
