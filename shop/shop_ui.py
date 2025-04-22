# shop/shop_ui.py
import discord
from discord.ext import commands
from discord.ui import View
from shop.shop_items import SHOP_ITEMS
from shop.shop_handler import ShopButton

class ShopView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.create_shop_buttons()

    def create_shop_buttons(self):
        categories = {}
        for item_name, item_data in SHOP_ITEMS.items():
            category = item_data['category']
            if category not in categories:
                categories[category] = []
            button = ShopButton(item_name, item_data['cost'])
            categories[category].append(button)

        for category, buttons in categories.items():
            self.add_item(discord.ui.Button(label=f"――― {category} ―――", style=discord.ButtonStyle.secondary, disabled=True))
            for button in buttons:
                self.add_item(button)

async def send_shop(channel: discord.TextChannel):
    embed = discord.Embed(title="🛒 NPショップ", description="ここではNPを使用して交換ができます👍", color=0x00ffcc)
    await channel.send(embed=embed, view=ShopView())
