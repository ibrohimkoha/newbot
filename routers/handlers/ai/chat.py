# import logging
# from datetime import datetime
# from aiogram import types, Router, F
# from aiogram.fsm.state import State, StatesGroup
# from aiogram.fsm.context import FSMContext
# from transformers import pipeline
# import redis.asyncio as redis
#
# from routers.keyboards.keyboard import cancel_keyboard
#
# # Hugging Face modelini yuklash
# model_name = "tiiuae/falcon-7b-instruct"
# nlp = pipeline("text-generation", model=model_name)
#
# router = Router()
# r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
#
# class ChatGetState(StatesGroup):
#     text = State()
#
# def get_today_key(user_id: int) -> str:
#     today = datetime.utcnow().strftime("%Y-%m-%d")
#     return f"user:{user_id}:{today}"
#
# @router.callback_query(F.data == "use_ai")
# async def use_ai(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.delete()
#     await callback.message.answer("Salom, savolingizni yozing:", reply_markup=await cancel_keyboard())
#     await state.set_state(ChatGetState.text)
#     await callback.answer()
#
# @router.message(ChatGetState.text, F.text)
# async def process_user_question(message: types.Message, state: FSMContext):
#     user_id = message.from_user.id
#     redis_key = get_today_key(user_id)
#
#     try:
#         count = int(await r.get(redis_key) or 0)
#         if count >= 2:
#             await message.answer("❌ Bugun siz 2 ta savolgina bera olasiz. Iltimos, ertaga qaytib keling.")
#             await state.clear()
#             return
#
#         await r.incr(redis_key)
#         await r.expire(redis_key, 86400)  # 1 kun
#
#         user_text = message.text
#         response = nlp(user_text)
#         bot_response = response[0]['generated_text']
#
#         await message.answer(bot_response, reply_markup=await cancel_keyboard())
#
#     except Exception as e:
#         logging.error(f"Xato yuz berdi: {e}")
#         await message.answer("⚠️ Xatolik yuz berdi. Iltimos, keyinroq yana urinib ko‘ring.")
#
#     await state.clear()
