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
            # DBでユーザーがなければ追加
            user_id = await add_user_if_not_exists(user_id, display_name)

            user_point = await get_point_by(user_id)

            if user_point < self.cost:
                await interaction.response.send_message(
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
                await interaction.response.send_modal(modal)
            elif self.item_name == "名前変更指定権":
                # ユーザー選択ビューを表示
                view = UserSelectView()
                await interaction.response.send_message(
                    "名前を変更するユーザーを選択してください：",
                    view=view,
                    ephemeral=True
                )
            else:
                # 購入後のUIの更新
                await interaction.response.send_message(
                    content=f"✅ **{self.item_name}** を購入しました！ 残り: {user_point}NP",
                    ephemeral=True
                )
        except discord.errors.NotFound:
            # インタラクションが無効になっている場合のエラーハンドリング
            await interaction.response.send_message("⚠️ インタラクションが無効になりました。再試行してください。", ephemeral=True)
        except Exception as e:
            # 他のエラーが発生した場合
            await interaction.response.send_message(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)








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
        try:
            user_id = await add_user_if_not_exists(str(self.user.id), self.user.display_name)

            try:
                # Botの権限で名前を変更
                guild = interaction.guild
                member = await guild.fetch_member(self.user.id)
                await member.edit(nick=self.new_name.value)
                
                # 名前変更後、データベースに変更を反映
                await mark_name_change_purchased(self.user.id)
                await interaction.response.send_message(
                    f"✅ ニックネームを「{self.new_name.value}」に変更しました！", ephemeral=True
                )
            except discord.Forbidden as e:
                error_message = str(e)
                await interaction.response.send_message(
                    f"⚠️ 権限エラーが発生しました：\n{error_message}\n\n"
                    "以下の点を確認してください：\n"
                    "1. Botに「メンバーのニックネームを管理」の権限があるか\n"
                    "2. Botのロールが変更対象のユーザーより上位にあるか\n"
                    "3. サーバー設定でBotの権限が正しく設定されているか",
                    ephemeral=True
                )
        except Exception as e:
            try:
                await interaction.response.send_message(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)
            except discord.errors.NotFound:
                # インタラクションが無効な場合は、新しいメッセージを送信
                await interaction.message.reply(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)

# 名前指定変更モーダル
class RenameOtherModal(Modal, title="他のユーザーの名前を変更します！"):
    def __init__(self, target_user: discord.Member):
        super().__init__()
        self.target_user = target_user
        self.new_name = TextInput(
            label="新しい名前",
            placeholder="ここに新しいニックネームを入力してね",
            max_length=32
        )
        self.add_item(self.new_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            try:
                # Botの権限で名前を変更
                guild = interaction.guild
                member = await guild.fetch_member(self.target_user.id)
                await member.edit(nick=self.new_name.value)
                
                await interaction.response.send_message(
                    f"✅ {self.target_user.display_name} さんのニックネームを「{self.new_name.value}」に変更しました！", 
                    ephemeral=True
                )
            except discord.Forbidden as e:
                error_message = str(e)
                await interaction.response.send_message(
                    f"⚠️ 権限エラーが発生しました：\n{error_message}\n\n"
                    "以下の点を確認してください：\n"
                    "1. Botに「メンバーのニックネームを管理」の権限があるか\n"
                    "2. Botのロールが変更対象のユーザーより上位にあるか\n"
                    "3. サーバー設定でBotの権限が正しく設定されているか",
                    ephemeral=True
                )
        except Exception as e:
            try:
                await interaction.response.send_message(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)
            except discord.errors.NotFound:
                await interaction.message.reply(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)

# ユーザー選択ビュー
class UserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.selected_user = None
        
        # ユーザー選択メニューを追加
        self.add_item(discord.ui.UserSelect(
            placeholder="名前を変更するユーザーを選択してください",
            min_values=1,
            max_values=1
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    @discord.ui.select(
        type=discord.ComponentType.user_select,
        placeholder="名前を変更するユーザーを選択してください",
        min_values=1,
        max_values=1
    )
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_user = select.values[0]
        modal = RenameOtherModal(self.selected_user)
        await interaction.response.send_modal(modal)
        self.stop()
