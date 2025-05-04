from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


async def admin_main_menu_def():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🫀 Animeni sozlash"), KeyboardButton(text="🌎 Animeni tlini sozlash")],
            [KeyboardButton(text="📮 Post sozlamalari"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🫀 Animelar"), KeyboardButton(text="📢 Majburiy kanal sozlamalari")],
            [KeyboardButton(text="💬 Habar yuborish sozlamalari")]
        ],
        resize_keyboard=True
    )
    return markup

async def user_main_menu_def():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🫀 Animelar")]
        ],
        resize_keyboard=True
    )
    return markup

async def cancel_keyboard():
    markup = ReplyKeyboardMarkup(
        keyboard=[
          [KeyboardButton(text="🚫 Bekor qilish")]
        ],
        resize_keyboard=True,
    )
    return markup

async def admin_post_menu_def():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Post yuborish uchun qo'shish"), KeyboardButton(text="👁 Post uchun kanallarni ko'rish")],
            [KeyboardButton(text="🗑 Post uchun kanalni o'chirish"), KeyboardButton(text="📝 Post tayyorlash")],
            [KeyboardButton(text="👤 Admin panelga qaytish")]
        ],
        resize_keyboard=True
    )
    return markup

async def admin_language_menu_def():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Animega til qo'shish"), KeyboardButton(text="📝 Animeni tilini tahrirlash")],
            [KeyboardButton(text="👁 Animeni tillarni ko'rish"), KeyboardButton(text="🗑 Animega oid tilni o'chirish")],
            [KeyboardButton(text="👤 Admin panelga qaytish")]
        ],
        resize_keyboard=True
    )
    return markup

async def admin_settings_menu_def():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👁 Barcha animelarni ko'rish")],
            [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="📝 Animeni tahrirlash")],
            [KeyboardButton(text="🗑 Animeni o'chirish"), KeyboardButton(text="👁 Animeni ko'zdan kechirish")],
            [KeyboardButton(text="👤 Admin panelga qaytish")]
        ],
        resize_keyboard=True
    )
    return markup

async def admin_settings_required_channel_def():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Kanal qo‘shish"), KeyboardButton(text="📋 Kanallar ro‘yxati")],
            [KeyboardButton(text="🗑 Kanalni o‘chirish") , KeyboardButton(text="🔛 Faollikni o‘zgartirish")],
            [KeyboardButton(text="👤 Admin panelga qaytish")]
        ],
        resize_keyboard=True
    )
    return markup

async def edit_anime_menu():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Nomi (title)ni tahrirlash"),
             KeyboardButton(text="🎭 Janrini (genre) tahrirlash")],
            [KeyboardButton(text="🎞 Qismlar sonini (count_episode) tahrirlash"),
             KeyboardButton(text="🖼 Rasm (image) havolasini tahrirlash")],
            [KeyboardButton(text="📅 Chiqarilish sanasini (release_date) tahrirlash"),
             KeyboardButton(text="📅 Tugash sanasini (end_date) tahrirlash")],
            [KeyboardButton(text="⭐ Reytingni (rating) tahrirlash"),
             KeyboardButton(text="💯 Baholashni (score) tahrirlash")],
            [KeyboardButton(text="🏢 Studio (studio)ni tahrirlash")],
            [KeyboardButton(text="🔙 Anime sozlamalariga qaytish")],
        ],
        resize_keyboard=True
    )
    return markup

async def admin_message_menu_def():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Habar yuborish oddiy"), KeyboardButton(text="⚙️ Habar yuborish inline")],
            [KeyboardButton(text="🍥 Anime habar yuborish")],
            [KeyboardButton(text="🖼️ Rasmli habar"), KeyboardButton(text="🎥 Video bilan habar")],
            [KeyboardButton(text="📎 Fayl yuborish"), KeyboardButton(text="🔁 Habarni forward qilish")],
            [KeyboardButton(text="⏱️ Rejalashtirish")],
            [KeyboardButton(text="👤 Admin panelga qaytish")],
        ],
        resize_keyboard=True
    )
    return markup


async def edit_language_keyboard(anime, lang):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Til nomini tahrirlash",
                    callback_data=f"edit_language_name_{anime.id}_{lang.id}"
                ),
                InlineKeyboardButton(
                    text="🎭 Til tavsifini (description) tahrirlash",
                    callback_data=f"edit_language_description_{anime.id}_{lang.id}"
                )
            ]
        ]
    )
    return markup

async def edit_anime_series(anime, lang):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Qism qo'shish", callback_data=f"add_series_{anime.id}_{lang.id}"),
                InlineKeyboardButton(text="🎭 Qismni o'chirish", callback_data=f"delete_series_{anime.id}_{lang.id}")
            ],
            [
                InlineKeyboardButton(text="🎞 Qismni ko'rish", callback_data=f"read_series_{anime.id}_{lang.id}"),
                InlineKeyboardButton(text="📝 Qism qo'shish tez", callback_data=f"add_episodes_{anime.id}_{lang.id}")
            ]
        ]
    )
    return markup

async def back_to_episode_settings(anime, lang):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Qism sozlamalariga qaytish", callback_data=f"anime_lang_{anime.id}_{lang.id}")
            ]
        ]
    )
    return markup

async def get_sort_buttons():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📛 Nom orqali", switch_inline_query_current_chat=""),
            InlineKeyboardButton(text="🔢 Kod orqali", callback_data="sort_by_id"),
        ],
        [
            # InlineKeyboardButton(text="👁 Ko‘p ko‘rilgan", callback_data="sort_by_views"),
            InlineKeyboardButton(text="🆕 So‘nggi yuklangan", callback_data="sort_by_latest"),
            # InlineKeyboardButton(text="Suniy intellektdan so'rash ", callback_data="use_ai")
        ]
    ])
    return keyboard


def generate_pagination_markup(current_page: int, total_pages: int):
    # Agar faqat 1 ta sahifa bo‘lsa, umuman pagination tugmasi kerak emas
    if total_pages <= 1:
        return None

    buttons = []

    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"anime_page:{current_page - 1}"
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop"
        )
    )

    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"anime_page:{current_page + 1}"
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[buttons])