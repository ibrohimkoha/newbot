from aiogram import types, Router, F, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from routers.database.database import get_session
from routers.database.models import get_required_channels, check_subscription
from routers.keyboards.keyboard import user_main_menu_def, admin_settings_required_channel_def
from routers.admin.role import AdminRoleFilter
from routers.handlers.required_channel_settings import add_required_channel, read_required_channel, delete_required_channel
router = Router()
@router.callback_query(F.data == "check_required_channels")
async def handle_check_required_channels(callback_query: types.CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id

    async with get_session() as session:
        # Fetch the required channels
        required_channels = await get_required_channels(db=session)

        # Prepare the inline keyboard markup
        markup = InlineKeyboardMarkup(inline_keyboard=[])

        # Check each required channel
        for channel in required_channels:
            if not channel.is_active:
                continue

            # Check if the user is subscribed to the channel
            is_subscribed = await check_subscription(user_id=user_id, community_chat_id=channel.channel_id, bot=bot)

            # If the user is not subscribed, add the channel link to the inline keyboard
            if not is_subscribed:
                button = InlineKeyboardButton(text=f"Obuna bo'lish: {channel.name}",
                                              url=f"https://t.me/{channel.username}")
                markup.inline_keyboard.append([button])

        # If the user is not subscribed to any required channels, show the buttons again
        if markup.inline_keyboard:
            await bot.send_message(
                user_id,
                "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling  ❌",
                reply_markup=markup
            )
        else:
            await bot.send_message(
                user_id,
                "Siz barcha kerakli kanallarga obuna bo'ldingiz! ✅",
                reply_markup=await user_main_menu_def() # Send an empty keyboard to remove the inline buttons
            )
        await callback_query.message.delete()
        # Acknowledge the callback query to remove the loading state
        await callback_query.answer()



@router.message(F.text == "📢 Majburiy kanal sozlamalari",
                F.chat.type == "private",
                AdminRoleFilter())
async def handle_required_channel(message: types.Message):
    await message.answer(text="Animeni majburiy kanalini sozlang:", reply_markup=await admin_settings_required_channel_def())

router.include_router(add_required_channel.router)
router.include_router(read_required_channel.router)
router.include_router(delete_required_channel.router)