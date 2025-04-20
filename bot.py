# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="C:/Users/owner/Desktop/DiscordBot/token.env")

TOKEN = os.getenv("DISCORD_TOKEN")
print(f"DISCORD_TOKEN: {TOKEN}")

import discord
from discord.ext import commands
from db import add_user_if_not_exists, add_points  # ← DBと連携してる想定！
try:
    # 実行したい処理
    print("処理を実行中...")
except Exception as e:
    print(f"エラー発生: {e}")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)




# 対象チャンネルのIDリスト（複数OK）
TARGET_CHANNEL_IDS = [
    1362883049104343211,  # チャンネル自慢
    1361249839567867995,  # チャンネル写真
    1360987317229322410,  # クリップ
    1363170014349496571,  # 飯テロ
    1363171100359659620,  # ネタ
]

# メッセージごとのリアクション済みユーザー追跡
reaction_tracker = {}

@bot.event
async def on_ready():
    print(f"{bot.user} はオンラインです！")
    print(f"ログイン完了: {bot.user}")
    for guild in bot.guilds:
        print(f"サーバー名: {guild.name}")
        for member in guild.members:
            if not member.bot:
                await add_user_if_not_exists(str(member.id), member.display_name)

@bot.event
async def on_member_join(member):
    if not member.bot:
        await add_user_if_not_exists(str(member.id), member.display_name)

@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    author = message.author

    # 対象チャンネルでなければ無視
    if message.channel.id not in TARGET_CHANNEL_IDS:
        return

    # 自分の投稿にリアクションした場合は無視
    if user.id == author.id:
        return

    msg_id = message.id
    user_id = user.id
    author_id = author.id

    # リアクション追跡用の初期化
    if msg_id not in reaction_tracker:
        reaction_tracker[msg_id] = set()

    # 同じ人が同じ投稿に再リアクション → 無視
    if user_id in reaction_tracker[msg_id]:
        return

    # 初リアクションなら記録してポイント加算
    reaction_tracker[msg_id].add(user_id)

    await add_user_if_not_exists(str(author_id), author.display_name)
    await add_points(str(author_id), 10)

    # ポイント加算後もメッセージ送らず完了！


if __name__ == "__main__":
    bot.run(TOKEN)
