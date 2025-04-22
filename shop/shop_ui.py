import discord
from discord import app_commands
from discord.ext import commands
from db import get_total_points, add_points  # 必要に応じて調整

class ShopButton(discord.ui.Button):
    def __init__(self, label, custom_id, cost):
        super().__init__(label=f"{label}（{cost}pt）", style=discord.ButtonStyle.success, custom_id=custom_id)
        self.cost = cost
        self.item_name = label

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        points = await get_total_points(user_id)
        if points < self.cost:
            await interaction.response.send_message(f"❌ ポイントが足りません！必要: {self.cost}pt", ephemeral=True)
            return

        await add_points(user_id, -self.cost)
        await interaction.response.send_message(f"✅ `{self.item_name}` を購入しました！ -{self.cost}pt", ephemeral=True)

        # 購入後の特典処理
        if self.item_name == "Legend Nanker ロール":
            role = discord.utils.get(interaction.guild.roles, name="Legend Nanker")
            if role:
                await interaction.user.add_roles(role)
                await interaction.followup.send("🎉 ロールを付与しました！", ephemeral=True)

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopButton("名前変更権", "name_change", 100))
        self.add_item(ShopButton("センシティブチャンネル開放", "sensitive", 150))
        self.add_item(ShopButton("Legend Nanker ロール", "legend", 50000))

async def post_shop_message(channel: discord.TextChannel):
    embed = discord.Embed(
        title="🎁 もりたけポイントショップ",
        description="下のボタンからアイテムを購入できます！\n購入にはポイントが必要です。",
        color=discord.Color.green()
    )
    embed.add_field(name="📛 名前変更権", value="50pt", inline=False)
    embed.add_field(name="🔞 センシティブチャンネル開放", value="300pt", inline=False)
    embed.add_field(name="🔥 Legend Nanker ロール", value="3000pt", inline=False)

    await channel.send(embed=embed, view=ShopView())
