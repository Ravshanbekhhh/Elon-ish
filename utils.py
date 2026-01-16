import random
import string

def gen_code():
    return "E-" + ''.join(random.choices(string.digits, k=5))

def gen_temp_id():
    return "TEMP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_ad_text(data: dict, include_code: bool = False, with_phone: bool = False) -> str:
    role = data.get("role", "Noma’lum")

    text = (
        f"👤 Kim: {role}\n"
        f"📍 Hudud: {data.get('hudud', 'N/A')}\n"
        f"🚻 Jinsi: {data.get('jinsi', 'N/A')}\n"
        f"🙎 I. Sh.: {data.get('fish', 'N/A')}\n"
        f"🆔 Yoshi: {data.get('yoshi', 'N/A')}\n"
        f"🧑‍💻 Kasbiy mahorati: {data.get('mahorat', 'N/A')}\n"
        f"📌 Mas’uliyati: {data.get('masuliyat', 'N/A')}\n"
        f"⏰ Ish vaqti: {data.get('vaqt', 'N/A')}\n"
        f"🕒 Bo‘sh vaqt: {data.get('bosh_vaqt', 'N/A')}\n"
        f"🧰 Qo‘shimcha: {data.get('qosimcha', 'N/A')}\n"
        f"💰 Maosh: {data.get('maosh', 'N/A')}\n"
    )

    # FAQAT yashirin kanal uchun telefon raqam qo'shiladi
    if with_phone:
        text += f"📞 Aloqa: {data.get('tel', 'N/A')}\n"

    if include_code:
        text += f"\n🔎 E’lon kodi: {data.get('code', 'N/A')}"

    return text