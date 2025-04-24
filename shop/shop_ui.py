import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from shop.shop_items import SHOP_ITEMS
from shop.shop_handler import ShopButton
from db import add_user_if_not_exists, mark_name_change_purchased, get_point_by
from db import update_points, supabase


CATEGORY_DESCRIPTIONS = {
    "プロフ変更系": {
        "名前変更権": "ニックネームを自由に変更できる",
        "名前変更指定権": "他人のニックネームを変更できる（要許可）",
        "ネームカラー変更権": "名前のカラーを変更できる"
    },
    # 他のカテゴリも続く
}

class ShopButton(Button):
    def __init__(self, item_name: str, cost: int, supabase):
        super().__init__(label=f"{item_name} - {cost}NP", style=discord.ButtonStyle.primary)
        self.item_name = item_name
        self.cost = cost
        self.supabase = supabase  # Supabaseインスタンス

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name

        try:
            # ポイント処理のためにユーザー確認
            await interaction.response.defer(ephemeral=True)

            # DBでユーザーがなければ追加
            user_id = await add_user_if_not_exists(user_id, display_name)

            user_point = await get_point_by(user_id)

            if user_point < self.cost:
                await interaction.followup.send(
                    f"⚠️ ポイントが足りません。必要: {self.cost}NP / 所持: {user_point}NP",
                    ephemeral=True
                )
                return

            # ポイントの減算
            await update_points(user_id, -self.cost)
            user_point = await get_point_by(user_id)

            if self.item_name == "名前変更権":
                # モーダルを表示
                modal = RenameModal(interaction.user)
                await interaction.followup.send("名前変更モーダルを開きます。", ephemeral=True)
                await interaction.message.reply(view=modal)
            else:
                # 購入後のUIの更新
                await interaction.followup.send(
                    content=f"✅ **{self.item_name}** を購入しました！ 残り: {user_point}NP",
                    ephemeral=True,
                    view=None  # UI（ボタン）の表示がない場合はview=Noneを指定
                )
        except discord.errors.NotFound:
            # インタラクションが無効になっている場合のエラーハンドリング
            await interaction.followup.send("⚠️ インタラクションが無効になりました。再試行してください。", ephemeral=True)
        except Exception as e:
            # 他のエラーが発生した場合
            await interaction.followup.send(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)








class CategoryShopView(View):
    def __init__(self, category_name, supabase):
        super().__init__(timeout=None)
        self.supabase = supabase
        items = CATEGORY_DESCRIPTIONS.get(category_name, {})
        for item_name in items:
            cost = SHOP_ITEMS[item_name]["cost"]
            self.add_item(ShopButton(item_name, cost, self.supabase))

async def send_shop_category(interaction: discord.Interaction, category_name: str):
    items = CATEGORY_DESCRIPTIONS.get(category_name, {})
    description = "\n".join(f"・{name} → {desc}" for name, desc in items.items())
    embed = discord.Embed(
        title=f"🛒 {category_name}",
        description=description,
        color=0x00ffcc
    )
    await interaction.response.send_message(embed=embed, view=CategoryShopView(category_name, supabase))

# 名前変更モーダル
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
        user_id = await add_user_if_not_exists(str(self.user.id), self.user.display_name)

        ### --- TODO --- ###
        # 名前変更済みかどうかを確認
        # if user_data["has_renamed"]:
        #     await interaction.response.send_message("⚠️ すでに名前を変更しています。名前変更は一度だけです。", ephemeral=True)
        #     return

        try:
            # 名前変更処理
            await self.user.edit(nick=self.new_name.value)
            # 名前変更後、データベースに変更を反映
            await mark_name_change_purchased(self.user.id)
            await interaction.response.send_message(
                f"✅ ニックネームを「{self.new_name.value}」に変更しました！", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ ニックネームを変更する権限がないみたい…", ephemeral=True)
