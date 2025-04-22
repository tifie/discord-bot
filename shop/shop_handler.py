# shop/shop_handler.py
import discord
from discord.ui import Button
from discord import Interaction
from shop.shop_items import SHOP_ITEMS
from db import add_user_if_not_exists, get_total_points, add_points
import asyncio

class ShopButton(Button):
    def __init__(self, item_name: str, cost: int):
        super().__init__(label=f"{item_name} - {cost}pt", style=discord.ButtonStyle.primary)
        self.item_name = item_name
        self.cost = cost

    async def callback(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name

        # DBにユーザーがなければ追加
        await add_user_if_not_exists(user_id, display_name)

        # 残高チェック
        total_points = await get_total_points(user_id)
        if total_points < self.cost:
            await interaction.response.send_message(
                f"💸 ポイントが足りません！\n必要: {self.cost}pt / 所持: {total_points}pt", 
                ephemeral=True
            )
            return

        # 購入確認
        await interaction.response.send_message(
            f"🛍 **{self.item_name}** を **{self.cost}pt** で購入しますか？", 
            view=ConfirmPurchaseView(self.item_name, self.cost), 
            ephemeral=True
        )


class ConfirmPurchaseView(discord.ui.View):
    def __init__(self, item_name: str, cost: int):
        super().__init__(timeout=30)
        self.item_name = item_name
        self.cost = cost

    @discord.ui.button(label="購入する", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        # 再度ポイント確認（多重押し対策）
        total_points = await get_total_points(user_id)
        if total_points < self.cost:
            await interaction.response.edit_message(
                content="⚠️ ポイントが足りません。", view=None
            )
            return

        # ポイントを減らす
        await add_points(user_id, -self.cost)

        # 購入完了メッセージ
        await interaction.response.edit_message(
            content=f"✅ **{self.item_name}** を購入しました！ 残ポイント: {total_points - self.cost}pt",
            view=None
        )

        # ここに管理者への通知処理などを追加してもOK！
        # 例: await notify_admin(interaction.user, self.item_name)

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="キャンセルしました。", view=None)
