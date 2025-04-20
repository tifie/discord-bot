import discord
from discord.ext import commands
from discord import app_commands
from db import add_user_if_not_exists, add_points, get_total_points, transfer_points

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

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
    try:
        await add_user_if_not_exists(str(interaction.user.id), interaction.user.display_name)
        points = await get_total_points(str(interaction.user.id))
        await interaction.response.send_message(f"あなたの現在のポイントは **{points}ポイント** です！", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {str(e)}", ephemeral=True)

# /givepointsコマンド
@bot.tree.command(name="givepoints", description="誰かにポイントを渡します")
@app_commands.describe(user="ポイントを渡したい相手", amount="渡すポイント数")
async def givepoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    try:
        if amount <= 0:
            await interaction.response.send_message("1以上のポイントを指定してください。", ephemeral=True)
            return

        sender_id = str(interaction.user.id)
        receiver_id = str(user.id)

        # ポイントの移動
        success, message = await transfer_points(sender_id, receiver_id, amount)

        await interaction.response.send_message(message, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {str(e)}", ephemeral=True)

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"ボットの実行中にエラーが発生しました: {str(e)}")
