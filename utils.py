import random
import string

def gen_code():
    return "E-" + ''.join(random.choices(string.digits, k=5))

def gen_temp_id():
    return "TEMP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_ad_text(data: dict, include_code: bool = False, with_phone: bool = False) -> str:
    role = data.get("role", "Noma’lum")
    
    # Sarlavha
    if role == "🏢 Ish beruvchiman":
        text = f"<b>🏢 ISH BOR ({data.get('hudud', 'N/A')})</b>\n\n"
        text += f"<b>🏢 Idora/Shaxs:</b> {data.get('fish', 'N/A')}\n"
        text += f"<b>📍 Hudud:</b> {data.get('hudud', 'N/A')}\n"
        text += f"<b>👷‍♂️ Kim kerak:</b> {data.get('jinsi', 'N/A')}\n"
        text += f"<b>🔞 Yosh chegarasi:</b> {data.get('yoshi', 'N/A')}\n"
        text += f"<b>📓 Talablar:</b> {data.get('mahorat', 'N/A')}\n"
        text += f"<b>⏰ Ish vaqti:</b> {data.get('vaqt', 'N/A')}\n"
        text += f"<b>💰 Maosh:</b> {data.get('maosh', 'N/A')}\n"
    else:
        # Ish qidiruvchi uchun (To'liq)
        text = f"<b>👷‍♂️ ISH KERAK ({data.get('hudud', 'N/A')})</b>\n\n"
        text += f"<b>👤 Ism:</b> {data.get('fish', 'N/A')}\n"
        text += f"<b>📍 Hudud:</b> {data.get('hudud', 'N/A')}\n"
        text += f"<b>🚻 Jinsi:</b> {data.get('jinsi', 'N/A')}\n"
        text += f"<b>🆔 Yoshi:</b> {data.get('yoshi', 'N/A')}\n"
        text += f"<b>🛠 Mutaxassisligi:</b> {data.get('mahorat', 'N/A')}\n"
        
        # Faqat kiritilgan bo'lsa chiqaramiz
        if data.get('masuliyat'):
            text += f"<b>📌 Mas’uliyati:</b> {data.get('masuliyat')}\n"
        
        text += f"<b>⏰ Ish vaqti:</b> {data.get('vaqt', 'N/A')}\n"
        
        if data.get('bosh_vaqt'):
            text += f"<b>🕒 Bo‘sh vaqt:</b> {data.get('bosh_vaqt')}\n"
        if data.get('qosimcha'):
            text += f"<b>🧰 Qo‘shimcha:</b> {data.get('qosimcha')}\n"
            
        text += f"<b>💰 Maosh:</b> {data.get('maosh', 'N/A')}\n"

    if with_phone:
        text += f"\n<b>📞 Aloqa:</b> {data.get('tel', 'N/A')}\n"

    if include_code:
        text += f"\n🔎 <b>E’lon kodi:</b> {data.get('code', 'N/A')}"

    return text
