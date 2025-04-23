# shop/shop_handler.py
import discord
from discord.ui import Button, View
from discord import Interaction
from shop.shop_items import SHOP_ITEMS
from db import add_user_if_not_exists, get_total_points, add_points

class ShopButton(Button):
    def __init__(self, item_name: str, cost: int, supabase):
        super().__init__(label=f"{item_name} - {cost}pt", style=discord.ButtonStyle.primary)
        self.item_name = item_name
        self.cost = cost
        self.supabase = supabase

    async def callback(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name

        await add_user_if_not_exists(self.supabase, user_id, display_name)

        total_points = await get_total_points(self.supabase, user_id)
        if total_points < self.cost:
            await interaction.response.send_message(
                f"💸 ポイントが足りません！\n必要: {self.cost}pt / 所持: {total_points}pt", 
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"🛍 **{self.item_name}** を **{self.cost}pt** で購入しますか？", 
            view=ConfirmPurchaseView(self.item_name, self.cost, self.supabase), 
            ephemeral=True
        )

class ConfirmPurchaseView(View):
    def __init__(self, item_name: str, cost: int, supabase):
        super().__init__(timeout=30)
        self.item_name = item_name
        self.cost = cost
        self.supabase = supabase

    @discord.ui.button(label="購入する", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        total_points = await get_total_points(self.supabase, user_id)
        if total_points < self.cost:
            await interaction.response.edit_message(
                content="⚠️ ポイントが足りません。", view=None
            )
            return

        await add_points(self.supabase, user_id, -self.cost)

        await interaction.response.edit_message(
            content=f"✅ **{self.item_name}** を購入しました！ 残ポイント: {total_points - self.cost}pt",
            view=None
        )

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="キャンセルしました。", view=None)

class ShopView(View):
    def __init__(self, category_items: dict, supabase):
        super().__init__(timeout=None)
        for item_name, cost in category_items.items():
            self.add_item(ShopButton(item_name, cost, supabase))

async def send_shop_category(interaction: Interaction, category: str, supabase):
    category_items = SHOP_ITEMS.get(category)
    if not category_items:
        await interaction.response.send_message("そのカテゴリは存在しません。", ephemeral=True)
        return

    await interaction.response.send_message(
        f"🛒 **{category}** カテゴリの商品一覧です！",
        view=ShopView(category_items, supabase),
        ephemeral=True
    )
