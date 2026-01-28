import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# DATABASE
from db import db

# BUTTONS
from buttons import (
    get_main_menu,
    get_cancel_menu,
    get_admin_menu,
    get_skip_video_menu,
    get_gender_menu,
    get_role_menu,
    get_channels_settings_menu,
    get_payment_settings_menu  # <--- Yangi import
)

# UTILS
from utils import gen_code, gen_temp_id, create_ad_text

# ================== CONFIG ==================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPER_ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Statik rasmlar (.env dan qoladi)
AYOL_ISHCHI_KERAK_PHOTO = os.getenv("AYOL_ISHCHI_KERAK_PHOTO")
AYOL_ISH_KERAK_PHOTO = os.getenv("AYOL_ISH_KERAK_PHOTO")
ERKAK_ISH_KERAK_PHOTO = os.getenv("ERKAK_ISH_KERAK_PHOTO")
ERKAK_ISHCHI_KERAK_PHOTO = os.getenv("ERKAK_ISHCHI_KERAK_PHOTO")

logging.basicConfig(level=logging.INFO)

pending_elons = {}
# Kesh (Cache) - Bazaga har safar murojaat qilmaslik uchun
bot_config = {
    "admins": [],
    "channels": {},
    "payment": {
        "card": os.getenv("KARTA_RAQAM", "8600 0000 0000 0000"),
        "owner": os.getenv("KARTA_EGA", "Noma'lum"),
        "price": os.getenv("ELON_NARXI", "10 000 so'm")
    }
}


# --- SOZLAMALARNI DB DAN YUKLASH ---
async def load_settings_from_db():
    # 1. Adminlar
    admins = await db.get_admins()
    if SUPER_ADMIN_ID not in admins:
        admins.append(SUPER_ADMIN_ID)
        await db.add_admin(SUPER_ADMIN_ID)
    bot_config["admins"] = admins

    # 2. Kanallar
    channels = await db.get_channels()
    env_channels = {
        "erkak": int(os.getenv("ERKAK_KANAL_ID", 0)),
        "ayol": int(os.getenv("AYOL_KANAL_ID", 0)),
        "yashirin": int(os.getenv("YASHIRIN_KANAL", 0))
    }
    for key, val in env_channels.items():
        if key not in channels and val != 0:
            await db.set_channel(key, val)
            channels[key] = val
    bot_config["channels"] = channels

    # 3. To'lov ma'lumotlari (YANGI)
    settings = await db.get_settings()

    # Bazada bo'lsa yangilaymiz, bo'lmasa .env dagini bazaga yozamiz
    if "card" in settings:
        bot_config["payment"]["card"] = settings["card"]
    else:
        await db.set_setting("card", bot_config["payment"]["card"])

    if "owner" in settings:
        bot_config["payment"]["owner"] = settings["owner"]
    else:
        await db.set_setting("owner", bot_config["payment"]["owner"])

    if "price" in settings:
        bot_config["payment"]["price"] = settings["price"]
    else:
        await db.set_setting("price", bot_config["payment"]["price"])

    logging.info("Sozlamalar DB dan yuklandi.")


def is_admin(user_id):
    return user_id in bot_config["admins"] or user_id == SUPER_ADMIN_ID


# ================== STATES ==================
class UserType(StatesGroup):
    choosing_role = State()


class Form(StatesGroup):
    hudud = State()
    jinsi = State()
    fish = State()
    yoshi = State()
    mahorat = State()
    masuliyat = State() # Ishchi uchun kerak
    vaqt = State()
    bosh_vaqt = State() # Ishchi uchun kerak
    qosimcha = State()  # Ishchi uchun kerak
    maosh = State()
    tel = State()
    video = State()
    waiting_for_check = State()
    admin_wait = State()


class AdminForm(StatesGroup):
    searching_ad = State()
    waiting_for_new_text = State()
    waiting_for_new_photo = State()
    current_temp_id = State()

    waiting_new_admin_id = State()
    waiting_del_admin_id = State()
    waiting_new_channel_id = State()

    # Yangi statelar (To'lov uchun)
    waiting_new_card = State()
    waiting_new_owner = State()
    waiting_new_price = State()


# ================== BOT SETUP ==================
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


# ================== HELPER FUNCTIONS ==================
def get_admin_check_keyboard(temp_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"approve_{temp_id}")
    kb.button(text="❌ Rad etish", callback_data=f"reject_{temp_id}")
    kb.button(text="✏️ Matnni tahrirlash", callback_data=f"edit_text_{temp_id}")
    kb.button(text="🖼 Rasm biriktirish", callback_data=f"attach_photo_{temp_id}")
    kb.adjust(2)
    return kb.as_markup()


def get_ad_photo(role: str, gender: str) -> str | None:
    if role == "👷‍♂️ Ish qidiryapman" and gender == "Erkak": return ERKAK_ISH_KERAK_PHOTO
    if role == "🏢 Ish beruvchiman" and gender == "Erkak": return ERKAK_ISHCHI_KERAK_PHOTO
    if role == "👷‍♂️ Ish qidiryapman" and gender == "Ayol": return AYOL_ISH_KERAK_PHOTO
    if role == "🏢 Ish beruvchiman" and gender == "Ayol": return AYOL_ISHCHI_KERAK_PHOTO
    return None


# ================== START & USER FLOW ==================
@dp.message(CommandStart())
async def start_handler(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("Assalomu alaykum!\n\nSiz kimsiz?", reply_markup=get_role_menu())
    await state.set_state(UserType.choosing_role)


@dp.message(UserType.choosing_role, F.text.in_(["👷‍♂️ Ish qidiryapman", "🏢 Ish beruvchiman"]))
async def choose_role(msg: types.Message, state: FSMContext):
    await state.update_data(role=msg.text)
    await msg.answer("Ajoyib. Endi e’lon berishingiz mumkin.", reply_markup=get_main_menu())
    await state.clear()


# ================== USER FLOW ==================

@dp.message(F.text == "📝 E’lon berish")
async def elon_start(msg: types.Message, state: FSMContext):
    await msg.answer("📍 Hududni kiriting:", reply_markup=get_cancel_menu())
    await state.set_state(Form.hudud)

@dp.callback_query(F.data == "cancel_form")
async def cancel_form(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Jarayon bekor qilindi.")
    await callback.message.answer("Bosh menyu:", reply_markup=get_main_menu())
    await callback.answer()

# --- 1. HUDUD ---
@dp.message(Form.hudud)
async def hudud(msg: types.Message, state: FSMContext):
    await state.update_data(hudud=msg.text)
    await msg.answer("Jinsingizni tanlang:", reply_markup=get_gender_menu())
    await state.set_state(Form.jinsi)

# --- 2. JINSI (YO'L SHU YERDAN AJRALADI) ---
@dp.callback_query(Form.jinsi, F.data.in_(["gender_male", "gender_female"]))
async def jinsi(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    gender = "Erkak" if callback.data == "gender_male" else "Ayol"
    await state.update_data(jinsi=gender)
    
    # Rolni tekshiramiz
    user_data = await state.get_data()
    role = user_data.get("role")

    if role == "🏢 Ish beruvchiman":
        # ISH BERUVCHI: Ism so'ramaymiz -> Yosh chegarasiga o'tamiz
        # fish (ism) xatolik bermasligi uchun "Ish beruvchi" deb yozib qo'yamiz
        await state.update_data(fish="Ish beruvchi") 
        
        await callback.message.answer("Yosh chegarasini kiriting:\n(Masalan: 20-30 yosh)", reply_markup=get_cancel_menu())
        await state.set_state(Form.yoshi)
    else:
        # ISHCHI: Ism so'raymiz
        await callback.message.answer("Ism sharifingizni kiriting:", reply_markup=get_cancel_menu())
        await state.set_state(Form.fish)
    
    await callback.answer()


# --- 3. FISH (Faqat Ishchi uchun ishlaydi) ---
@dp.message(Form.fish)
async def fish(msg: types.Message, state: FSMContext):
    await state.update_data(fish=msg.text)
    await msg.answer("Yoshingiz:", reply_markup=get_cancel_menu())
    await state.set_state(Form.yoshi)


# --- 4. YOSHI ---
@dp.message(Form.yoshi)
async def yoshi(msg: types.Message, state: FSMContext):
    await state.update_data(yoshi=msg.text)
    
    user_data = await state.get_data()
    if user_data.get("role") == "🏢 Ish beruvchiman":
        # ISH BERUVCHI: Talablar (Mahorat o'rniga)
        await msg.answer("❗️ Talablar va vazifalarni yozing:\n(Xodim nima ish qilishi kerak?)", reply_markup=get_cancel_menu())
    else:
        # ISHCHI: Mahorat
        await msg.answer("Kasbiy mahoratingiz (nima ish qila olasiz):", reply_markup=get_cancel_menu())
        
    await state.set_state(Form.mahorat)


# --- 5. MAHORAT / TALABLAR ---
@dp.message(Form.mahorat)
async def mahorat(msg: types.Message, state: FSMContext):
    await state.update_data(mahorat=msg.text)
    
    user_data = await state.get_data()
    if user_data.get("role") == "🏢 Ish beruvchiman":
        # ISH BERUVCHI: Mas'uliyatni o'tkazib yuboramiz -> Ish vaqti
        await msg.answer("⏰ Ish vaqtini kiriting:", reply_markup=get_cancel_menu())
        await state.set_state(Form.vaqt)
    else:
        # ISHCHI: Mas'uliyatni so'raymiz
        await msg.answer("Mas'uliyatingiz (qaysi ishlarga javob bera olasiz):", reply_markup=get_cancel_menu())
        await state.set_state(Form.masuliyat)


# --- 6. MAS'ULIYAT (Faqat Ishchi) ---
@dp.message(Form.masuliyat)
async def masuliyat(msg: types.Message, state: FSMContext):
    await state.update_data(masuliyat=msg.text)
    await msg.answer("⏰ Ish vaqti:", reply_markup=get_cancel_menu())
    await state.set_state(Form.vaqt)


# --- 7. VAQT ---
@dp.message(Form.vaqt)
async def vaqt(msg: types.Message, state: FSMContext):
    await state.update_data(vaqt=msg.text)
    
    user_data = await state.get_data()
    if user_data.get("role") == "🏢 Ish beruvchiman":
        # ISH BERUVCHI: Bo'sh vaqt yo'q -> Qo'shimcha ma'lumot
        await msg.answer("ℹ️ Qo'shimcha ma'lumotlar (Manzil, mo'ljal va h.k):", reply_markup=get_cancel_menu())
        await state.set_state(Form.qosimcha)
    else:
        # ISHCHI: Bo'sh vaqtni so'raymiz
        await msg.answer("Bo'sh vaqtingiz bormi? (bo'lsa yozing):", reply_markup=get_cancel_menu())
        await state.set_state(Form.bosh_vaqt)


# --- 8. BO'SH VAQT (Faqat Ishchi) ---
@dp.message(Form.bosh_vaqt)
async def bosh_vaqt(msg: types.Message, state: FSMContext):
    await state.update_data(bosh_vaqt=msg.text)
    await msg.answer("Qo'shimcha ma'lumotlar (ixtiyoriy):", reply_markup=get_cancel_menu())
    await state.set_state(Form.qosimcha)


# --- 9. QO'SHIMCHA ---
@dp.message(Form.qosimcha)
async def qosimcha(msg: types.Message, state: FSMContext):
    await state.update_data(qosimcha=msg.text)
    
    user_data = await state.get_data()
    if user_data.get("role") == "🏢 Ish beruvchiman":
        await msg.answer("💰 Qancha maosh bermoqchisiz?", reply_markup=get_cancel_menu())
    else:
        await msg.answer("💰 Qancha maosh kutmoqdasiz?", reply_markup=get_cancel_menu())
        
    await state.set_state(Form.maosh)


# --- 10. MAOSH ---
@dp.message(Form.maosh)
async def maosh(msg: types.Message, state: FSMContext):
    await state.update_data(maosh=msg.text)
    await msg.answer("📞 Telefon raqamingiz:", reply_markup=get_cancel_menu())
    await state.set_state(Form.tel)


# --- 11. TEL (Video so'rash yoki so'ramaslik) ---
@dp.message(Form.tel)
async def tel(msg: types.Message, state: FSMContext):
    await state.update_data(tel=msg.text)
    
    user_data = await state.get_data()
    
    # AGAR ISH BERUVCHI BO'LSA -> Video so'ramaymiz, darhol to'lovga o'tamiz
    if user_data.get("role") == "🏢 Ish beruvchiman":
        # Videoni o'tkazib yuborish logikasini chaqiramiz (video_id=None bo'ladi)
        # To'g'ridan to'g'ri to'lov funksiyasini chaqiramiz:
        await request_payment(msg, state) 
    else:
        # ISHCHI BO'LSA -> Video so'raymiz
        await msg.answer("Agar xohlasangiz video yuboring yoki o'tkazib yuboring.", reply_markup=get_skip_video_menu())
        await state.set_state(Form.video)

# --- TO'LOV QISMI (DINAMIK) ---
@dp.message(Form.video, F.video | (F.text == "➡️ Videoni o'tkazib yuborish"))
async def request_payment(msg: types.Message, state: FSMContext):
    if msg.video: await state.update_data(video_id=msg.video.file_id)

    # Konfiguratsiyadan ma'lumotlarni olamiz
    price = bot_config["payment"]["price"]
    card = bot_config["payment"]["card"]
    owner = bot_config["payment"]["owner"]

    payment_text = (
        f"<b>📋 Ma'lumotlar qabul qilindi!</b>\n\n"
        f"E'lonni kanallarga joylash pullik.\n"
        f"Narxi: <b>{price}</b>\n\n"
        f"💳 Karta: <code>{card}</code>\n"
        f"👤 Egasi: <b>{owner}</b>\n\n"
        f"Iltimos, to'lov qiling va <b>chek rasmini</b> shu yerga yuboring."
    )
    await msg.answer(payment_text, reply_markup=get_cancel_menu())
    await state.set_state(Form.waiting_for_check)


@dp.message(Form.waiting_for_check, F.photo)
async def handle_check(msg: types.Message, state: FSMContext):
    check_photo_id = msg.photo[-1].file_id
    data = await state.get_data()
    temp_id = gen_temp_id()

    pending_elons[temp_id] = {
        "data": data,
        "user_id": msg.from_user.id,
        "video_id": data.get("video_id"),
        "check_id": check_photo_id,
        "admin_text": None,
        "admin_photo": None
    }

    ad_text = create_ad_text(data, with_phone=True)
    caption = f"🆕 <b>YANGI E'LON!</b>\n\n{ad_text}\n\n<i>Boshqarish tugmalari:</i>"

    for admin_id in bot_config["admins"]:
        try:
            await bot.send_photo(admin_id, photo=check_photo_id, caption=caption,
                                 reply_markup=get_admin_check_keyboard(temp_id))
        except:
            pass

    await msg.answer("⏳ Chek adminga yuborildi.", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Form.admin_wait)


# ================== ADMIN PANEL ==================

@dp.message(Command("admin"))
async def admin_panel_cmd(msg: types.Message):
    if is_admin(msg.from_user.id):
        await msg.answer("Admin panel:", reply_markup=get_admin_menu())


@dp.message(F.text == "👤 Foydalanuvchi rejimi")
async def back_to_user_mode(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "Foydalanuvchi rejimiga o'tdingiz. Siz kimsiz?", 
        reply_markup=get_role_menu()
    )
    await state.set_state(UserType.choosing_role)


# --- ADMIN QO'SHISH/O'CHIRISH ---
@dp.message(F.text == "➕ Admin qo'shish")
async def add_admin_start(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    await msg.answer("ID yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(AdminForm.waiting_new_admin_id)


@dp.message(AdminForm.waiting_new_admin_id)
async def add_admin_finish(msg: types.Message, state: FSMContext):
    try:
        new_id = int(msg.text)
        await db.add_admin(new_id)
        if new_id not in bot_config["admins"]: bot_config["admins"].append(new_id)
        await msg.answer(f"✅ {new_id} admin qilindi.", reply_markup=get_admin_menu())
    except ValueError:
        await msg.answer("Raqam bo'lishi kerak.")
    await state.clear()


@dp.message(F.text == "➖ Admin o'chirish")
async def del_admin_start(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    await msg.answer("ID yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(AdminForm.waiting_del_admin_id)


@dp.message(AdminForm.waiting_del_admin_id)
async def del_admin_finish(msg: types.Message, state: FSMContext):
    try:
        del_id = int(msg.text)
        if del_id == SUPER_ADMIN_ID:
            await msg.answer("Asosiy adminni o'chirolmaysiz!")
        else:
            await db.remove_admin(del_id)
            if del_id in bot_config["admins"]: bot_config["admins"].remove(del_id)
            await msg.answer(f"✅ {del_id} o'chirildi.", reply_markup=get_admin_menu())
    except ValueError:
        await msg.answer("Raqam bo'lishi kerak.")
    await state.clear()


@dp.message(F.text == "📋 Adminlar ro'yxati")
async def list_admins(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    admins = await db.get_admins()
    text = "👮‍♂️ Adminlar:\n\n" + "\n".join([f"• <code>{a}</code>" for a in admins])
    await msg.answer(text)


# --- KANAL SOZLAMALARI ---
@dp.message(F.text == "⚙️ Kanal sozlamalari")
async def channel_settings(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    channels = await db.get_channels()
    text = (
        f"🚹 Erkak: <code>{channels.get('erkak', 'yoq')}</code>\n"
        f"👩 Ayol: <code>{channels.get('ayol', 'yoq')}</code>\n"
        f"🔒 Yashirin: <code>{channels.get('yashirin', 'yoq')}</code>"
    )
    await msg.answer(text, reply_markup=get_channels_settings_menu())


@dp.callback_query(F.data.startswith("set_channel_"))
async def set_channel_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    channel_type = callback.data.split("_")[2]
    await state.update_data(editing_channel=channel_type)
    await callback.message.edit_text("Yangi ID ni yuboring (-100...)")
    await state.set_state(AdminForm.waiting_new_channel_id)


@dp.message(AdminForm.waiting_new_channel_id)
async def set_channel_finish(msg: types.Message, state: FSMContext):
    try:
        new_id = int(msg.text)
        data = await state.get_data()
        ctype = data.get("editing_channel")
        await db.set_channel(ctype, new_id)
        bot_config["channels"][ctype] = new_id
        await msg.answer(f"✅ {ctype} kanali yangilandi.", reply_markup=get_admin_menu())
    except ValueError:
        await msg.answer("Raqam bo'lishi kerak.")
    await state.clear()


# --- TO'LOV SOZLAMALARI (YANGI) ---
@dp.message(F.text == "💳 To'lov sozlamalari")
async def payment_settings(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    p = bot_config["payment"]
    text = (
        f"<b>Joriy sozlamalar:</b>\n\n"
        f"💳 Karta: <code>{p['card']}</code>\n"
        f"👤 Ega: <b>{p['owner']}</b>\n"
        f"💰 Narx: <b>{p['price']}</b>\n\n"
        "O'zgartirish uchun tanlang:"
    )
    await msg.answer(text, reply_markup=get_payment_settings_menu())


# 1. Karta raqamni o'zgartirish
@dp.callback_query(F.data == "set_pay_card")
async def set_pay_card(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("Yangi karta raqamini yuboring:")
    await state.set_state(AdminForm.waiting_new_card)


@dp.message(AdminForm.waiting_new_card)
async def save_pay_card(msg: types.Message, state: FSMContext):
    new_card = msg.text
    await db.set_setting("card", new_card)
    bot_config["payment"]["card"] = new_card
    await msg.answer("✅ Karta raqami yangilandi.", reply_markup=get_admin_menu())
    await state.clear()


# 2. Karta egasini o'zgartirish
@dp.callback_query(F.data == "set_pay_owner")
async def set_pay_owner(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("Yangi karta egasini yuboring (Ism Familiya):")
    await state.set_state(AdminForm.waiting_new_owner)


@dp.message(AdminForm.waiting_new_owner)
async def save_pay_owner(msg: types.Message, state: FSMContext):
    new_owner = msg.text
    await db.set_setting("owner", new_owner)
    bot_config["payment"]["owner"] = new_owner
    await msg.answer("✅ Karta egasi yangilandi.", reply_markup=get_admin_menu())
    await state.clear()


# 3. Narxni o'zgartirish
@dp.callback_query(F.data == "set_pay_price")
async def set_pay_price(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("Yangi narxni yuboring (Masalan: 15 000 so'm):")
    await state.set_state(AdminForm.waiting_new_price)


@dp.message(AdminForm.waiting_new_price)
async def save_pay_price(msg: types.Message, state: FSMContext):
    new_price = msg.text
    await db.set_setting("price", new_price)
    bot_config["payment"]["price"] = new_price
    await msg.answer("✅ Narx yangilandi.", reply_markup=get_admin_menu())
    await state.clear()


# --- KOD ORQALI QIDIRISH ---
@dp.message(F.text == "🔎 Kod orqali qidirish")
async def search_start(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    await msg.answer("Kod kiriting:", reply_markup=get_cancel_menu())
    await state.set_state(AdminForm.searching_ad)


@dp.message(AdminForm.searching_ad)
async def search_finish(msg: types.Message, state: FSMContext):
    code = msg.text.strip()
    ad_data = await db.get_ad(code)
    if ad_data:
        text = create_ad_text(ad_data, include_code=True, with_phone=True)
        await msg.answer(f"✅ Topildi:\n\n{text}", reply_markup=get_admin_menu())
    else:
        await msg.answer("❌ Topilmadi.", reply_markup=get_admin_menu())
    await state.clear()


@dp.message(F.text == "👤 Foydalanuvchi rejimi")
async def user_menukb(msg: types.Message):
    await msg.answer("Foydalauvchi Rejimi.", reply_markup=get_role_menu())


# ================== TASDIQLASH (APPROVE) ==================

@dp.callback_query(F.data.startswith("edit_text_"))
async def click_edit_text(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    temp_id = callback.data.split("_")[2]
    await state.update_data(editing_temp_id=temp_id)
    elon = pending_elons.get(temp_id)
    if elon:
        current_data = elon["data"]
        txt = elon.get("admin_text") or create_ad_text(current_data, with_phone=True)
        await callback.message.answer("Eski matn pastda:")
        await callback.message.answer(txt)
        await state.set_state(AdminForm.waiting_for_new_text)
    await callback.answer()


@dp.message(AdminForm.waiting_for_new_text)
async def receive_new_text(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    temp_id = data.get("editing_temp_id")
    if temp_id in pending_elons:
        pending_elons[temp_id]["admin_text"] = msg.text
        await msg.answer("✅ Matn yangilandi.")
    await state.clear()


@dp.callback_query(F.data.startswith("attach_photo_"))
async def click_attach_photo(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    temp_id = callback.data.split("_")[2]
    await state.update_data(editing_temp_id=temp_id)
    await callback.message.answer("Rasm yuboring:")
    await state.set_state(AdminForm.waiting_for_new_photo)
    await callback.answer()


@dp.message(AdminForm.waiting_for_new_photo, F.photo)
async def receive_new_photo(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    temp_id = data.get("editing_temp_id")
    if temp_id in pending_elons:
        pending_elons[temp_id]["admin_photo"] = msg.photo[-1].file_id
        await msg.answer("✅ Rasm biriktirildi.")
    await state.clear()


@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return

    temp_id = callback.data.split("_")[1]
    if temp_id not in pending_elons:
        await callback.answer("Topilmadi.", show_alert=True)
        return

    elon = pending_elons.pop(temp_id)
    data = elon["data"]
    user_id = elon["user_id"]
    admin_text = elon.get("admin_text")
    admin_photo = elon.get("admin_photo")

    code = gen_code()
    data["code"] = code

    # --- MATN TAYYORLASH ---
    if admin_text:
        final_text_public = admin_text
        final_text_hidden = admin_text
        if f"Kod: {code}" not in final_text_public:
            final_text_public += f"\n\n🔎 E’lon kodi: {code}"
            final_text_hidden += f"\n\n🔎 E’lon kodi: {code}"
    else:
        final_text_public = create_ad_text(data, include_code=True, with_phone=False)
        final_text_hidden = create_ad_text(data, include_code=True, with_phone=True)

    # --- KANALLARNI ANIQLASH ---
    channels = bot_config["channels"]
    if data["jinsi"] == "Erkak":
        target_channel_id = channels.get("erkak")
    else:
        target_channel_id = channels.get("ayol")
    
    hidden_channel_id = channels.get("yashirin")

    # --- RASM ---
    photo_to_send = admin_photo if admin_photo else get_ad_photo(data.get("role"), data.get("jinsi"))

    try:
        # 1. OMMAVIY KANALGA JOYLASh
        if target_channel_id:
            if photo_to_send:
                await bot.send_photo(target_channel_id, photo=photo_to_send, caption=final_text_public)
            else:
                await bot.send_message(target_channel_id, final_text_public)
        
        # 2. YASHIRIN KANALGA JOYLASh
        if hidden_channel_id:
            if admin_photo:
                await bot.send_photo(hidden_channel_id, photo=admin_photo, caption=f"🔐 #ARXIV\n\n{final_text_hidden}")
            else:
                await bot.send_message(hidden_channel_id, f"🔐 #ARXIV\n\n{final_text_hidden}")

        # 3. DB GA SAQLASH
        await db.save_ad(code, data)

        # ---------------------------------------------------------
        # 4. USERGA XABAR + KANAL LINKI (YANGILANGAN QISM)
        # ---------------------------------------------------------
        channel_link = None
        
        # Kanal linkini olishga harakat qilamiz
        if target_channel_id:
            try:
                chat_info = await bot.get_chat(target_channel_id)
                if chat_info.username:
                    channel_link = f"https://t.me/{chat_info.username}"
                elif chat_info.invite_link:
                    channel_link = chat_info.invite_link
                else:
                    # Agar link yo'q bo'lsa, uni hosil qilamiz (Private kanallar uchun)
                    channel_link = await bot.export_chat_invite_link(target_channel_id)
            except Exception as e:
                logging.warning(f"Kanal linkini olib bo'lmadi: {e}")

        # Userga boradigan xabar matni
        user_msg = (
            f"✅ <b>Tabriklaymiz! E'loningiz tasdiqlandi.</b>\n"
            f"🔎 E'lon kodi: <b>{code}</b>\n\n"
        )

        kb = None
        if channel_link:
            user_msg += (
                f"📢 E'loningiz kanalimizga joylandi.\n"
                f"Pastdagi tugma orqali kirib ko'rishingiz va obuna bo'lishingiz mumkin."
            )
            # Link tugmasini yasaymiz
            kb_builder = InlineKeyboardBuilder()
            kb_builder.button(text="↗️ E'lonni ko'rish va Obuna bo'lish", url=channel_link)
            kb = kb_builder.as_markup()
        
        await bot.send_message(user_id, user_msg, reply_markup=kb)
        
        # Admin xabarini yangilash
        await callback.message.edit_caption(caption=f"✅ <b>JOYLANDI</b>\nKod: {code}")

    except Exception as e:
        await callback.message.answer(f"Xatolik: {e}")
        logging.error(e)
    
    await callback.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    temp_id = callback.data.split("_")[1]
    if temp_id in pending_elons:
        elon = pending_elons.pop(temp_id)
        await bot.send_message(elon["user_id"], "❌ Rad etildi.")
        await callback.message.edit_caption(caption="❌ <b>RAD ETILDI</b>")
    await callback.answer()


# ================== MAIN ==================
async def main():
    await db.connect()
    await load_settings_from_db()
    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())





