# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os

# .envファイルを読み込む（パス指定なしでOK！）
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
print(f"DISCORD_TOKEN: {TOKEN}")

import discord
from discord.ext import commands
from db import add_user_if_not_exists, add_points  # DB連携想定

try:
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

# 対象チャンネルのIDリスト
TARGET_CHANNEL_IDS = [
    1362883049104343211,  # チャンネル自慢
    1361249839567867995,  # チャンネル写真
    1360987317229322410,  # クリップ
    1363170014349496571,  # 飯テロ
    1363171100359659620,  # ネタ
]

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

    if message.channel.id not in TARGET_CHANNEL_IDS:
        return

    if user.id == author.id:
        return

    msg_id = message.id
    user_id = user.id
    author_id = author.id

    if msg_id not in reaction_tracker:
        reaction_tracker[msg_id] = set()

    if user_id in reaction_tracker[msg_id]:
        return

    reaction_tracker[msg_id].add(user_id)

    await add_user_if_not_exists(str(author_id), author.display_name)
    await add_points(str(author_id), 10)

if __name__ == "__main__":
    bot.run(TOKEN)
