# shop/shop_ui.py
import discord
from discord.ext import commands
from discord.ui import View
from shop.shop_items import SHOP_ITEMS
from shop.shop_handler import ShopButton

CATEGORY_DESCRIPTIONS = {
    "プロフ変更系": {
        "名前変更権": "ニックネームを自由に変更できる",
        "名前変更指定権": "他人のニックネームを変更できる（要許可）",
        "ネームカラー変更権": "名前のカラーを変更できる"
    },
    # 他のカテゴリも続く
}

SHOP_ITEMS = {
    "名前変更権": {"cost": 100},
    "名前変更指定権": {"cost": 200},
    "ネームカラー変更権": {"cost": 150},
    # 他も追加
}

class CategoryShopView(View):
    def __init__(self, category_name):
        super().__init__(timeout=None)
        items = CATEGORY_DESCRIPTIONS.get(category_name, {})
        for item_name in items:
            cost = SHOP_ITEMS[item_name]["cost"]
            self.add_item(ShopButton(item_name, cost))

async def send_shop_category(channel: discord.Interaction, category_name: str):
    items = CATEGORY_DESCRIPTIONS.get(category_name, {})
    description = "\n".join(f"・{name} → {desc}" for name, desc in items.items())
    embed = discord.Embed(
        title=f"🛒 {category_name}",
        description=description,
        color=0x00ffcc
    )
    await channel.send(embed=embed, view=CategoryShopView(category_name))
    await interaction.response.send_message(f"✅ {category_name} を表示しました！", ephemeral=True)
