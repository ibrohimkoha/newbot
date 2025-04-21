from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from typing import Dict, Any, Callable, Awaitable
from aiogram import types, Bot
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from datetime import datetime
from sqlalchemy.orm import Session

from routers.database.database import get_session
from routers.database.models import RequiredChannel, get_user, check_subscription, add_user, get_employee_by_chat_id, \
    user_exists, get_required_channels


class CheckRequiredChannelsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        async with get_session() as session:
            user_id = event.chat.id
            bot: Bot = data['bot']
            # Check if the user is an employee
            is_employee = await get_employee_by_chat_id(chat_id=user_id, session=session)
            if is_employee:
                return await handler(event, data)

            # Ensure the user exists
            if not await user_exists(chat_id=user_id, session=session):
                await add_user(chat_id=user_id, db=session)

            user = await get_user(chat_id=user_id, db=session)

            # Get active required channels
            required_channels = await get_required_channels(db=session)

            # If no required channels, proceed to the handler
            if not required_channels:
                return await handler(event, data)

            # Prepare the inline keyboard markup
            markup = InlineKeyboardMarkup(inline_keyboard=[])

            # Check each required channel
            for channel in required_channels:
                if not channel.is_active:
                    continue

                # Check if the user is subscribed to the channel
                is_subscribed = await check_subscription(user_id=user_id, community_chat_id=channel.channel_id, bot=bot)

                if not is_subscribed:
                    button = InlineKeyboardButton(text=f"Obuna bo'lish: {channel.name}",
                                                  url=f"https://t.me/{channel.username}")
                    markup.inline_keyboard.append([button])

            # If the user is not subscribed to any required channels, show the buttons
            if markup.inline_keyboard:
                # Add a button for checking subscriptions
                button = InlineKeyboardButton(text="Obunani tekshirish  ⭕️", callback_data="check_required_channels")
                markup.inline_keyboard.append([button])

                # Inform the user to subscribe to required channels
                await event.answer(text="Tugmalar olib tashlandi ✅", reply_markup=ReplyKeyboardRemove())
                await event.answer(
                    text="Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling  ❌",
                    reply_markup=markup
                )
                return

            # Proceed to the handler if no required subscription is pending
            return await handler(event, data)

    async def get_required_channels(self):
        # Assuming you're using SQLAlchemy or an equivalent async DB method to fetch active required channels
        # You can replace the following query with your own DB logic
        return await RequiredChannel.query.filter(RequiredChannel.is_active == True).all()
