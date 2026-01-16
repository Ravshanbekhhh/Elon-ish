from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# ===== USER MENU =====
def get_role_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👷‍♂️ Ish qidiryapman")
    builder.button(text="🏢 Ish beruvchiman")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 E’lon berish")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="cancel_form")
    return builder.as_markup()

def get_skip_video_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="➡️ Videoni o'tkazib yuborish")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_gender_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🚹 Erkak")
    builder.button(text="👩 Ayol")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# ===== ADMIN MENYU (YANGILANDI) =====
def get_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔎 Kod orqali qidirish")
    builder.button(text="⚙️ Kanal sozlamalari")
    builder.button(text="💳 To'lov sozlamalari") # <--- YANGI
    builder.button(text="➕ Admin qo'shish")
    builder.button(text="➖ Admin o'chirish")
    builder.button(text="📋 Adminlar ro'yxati")
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

# ===== KANAL SOZLAMALARI =====
def get_channels_settings_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚹 Erkaklar kanali", callback_data="set_channel_erkak")
    builder.button(text="👩 Ayollar kanali", callback_data="set_channel_ayol")
    builder.button(text="🔒 Yashirin kanal", callback_data="set_channel_yashirin")
    builder.adjust(1)
    return builder.as_markup()

# ===== TO'LOV SOZLAMALARI (YANGI) =====
def get_payment_settings_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Karta raqam", callback_data="set_pay_card")
    builder.button(text="👤 Karta egasi", callback_data="set_pay_owner")
    builder.button(text="💰 Narx", callback_data="set_pay_price")
    builder.adjust(1)
    return builder.as_markup()