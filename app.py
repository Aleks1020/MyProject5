import streamlit as st
import requests
import re

# Настройка на страницата
st.set_page_config(page_title="Pro Label Scanner", page_icon="🥗")

# ==============================================================================
# 1. ПЪЛНА БАЗА ДАННИ (РАЗШИРЕН СПИСЪК)
# ==============================================================================
INGREDIENTS_DB = {
    # --- ЗЪРНЕНИ, ГЛУТЕН И БИРА ---
    "ечеми": {"severity": "medium", "bg": {"name": "Ечемик / Малц (Глутен)", "effect": "Алерген, съдържа глутен. Висок гликемичен индекс.", "alternatives": ["Безглутенова бира", "Вода"]}, "en": {"name": "Barley/Malt", "effect": "Contains gluten.", "alternatives": ["GF Beer"]}},
    "малц": {"severity": "medium", "bg": {"name": "Малц", "effect": "Концентрирани захари от зърно, вдигат инсулина.", "alternatives": ["Чай"]}, "en": {"name": "Malt", "effect": "Spikes insulin.", "alternatives": ["Tea"]}},
    "хмел": {"severity": "low", "bg": {"name": "Хмел", "effect": "Естествен горчив агент, може да влияе на хормоните.", "alternatives": []}, "en": {"name": "Hops", "effect": "Hormonal influence.", "alternatives": []}},
    "грис": {"severity": "medium", "bg": {"name": "Царевичен грис", "effect": "Рафиниран пълнител, често ГМО.", "alternatives": ["Чист малц"]}, "en": {"name": "Corn Grits", "effect": "Refined filler.", "alternatives": ["Pure malt"]}},

    # --- ОПАСНИ КОНСЕРВАНТИ (Е-та) ---
    "e211": {"severity": "high", "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Силно токсичен, риск от рак при смесване с Вит. С.", "alternatives": ["Био консерванти"]}, "en": {"name": "E211", "effect": "Carcinogenic risk.", "alternatives": ["Fresh food"]}},
    "е211": {"severity": "high", "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Силно токсичен.", "alternatives": []}, "en": {"name": "E211", "effect": "Toxic.", "alternatives": []}},
    "e250": {"severity": "high", "bg": {"name": "Е250 (Натриев нитрит)", "effect": "Използва се в колбаси. Силно канцерогенен.", "alternatives": ["Месо без нитрити"]}, "en": {"name": "E250", "effect": "Carcinogenic nitrite.", "alternatives": ["Fresh meat"]}},
    "е250": {"severity": "high", "bg": {"name": "Е250 (Натриев нитрит)", "effect": "Канцерогенен.", "alternatives": []}, "en": {"name": "E250", "effect": "Carcinogen.", "alternatives": []}},
    "e202": {"severity": "medium", "bg": {"name": "Е202 (Калиев сорбат)", "effect": "Консервант, може да предизвика алергии.", "alternatives": []}, "en": {"name": "E202", "effect": "Preservative.", "alternatives": []}},

    # --- ВКУСОВИ ПОДОБРИТЕЛИ ---
    "e621": {"severity": "high", "bg": {"name": "Е621 (Глутамат)", "effect": "Невротоксин, причинява главоболие и пристрастяване.", "alternatives": ["Естествени подправки"]}, "en": {"name": "E621 (MSG)", "effect": "Neurotoxin.", "alternatives": ["Spices"]}},
    "е621": {"severity": "high", "bg": {"name": "Е621 (Глутамат)", "effect": "Невротоксин.", "alternatives": []}, "en": {"name": "E621", "effect": "MSG.", "alternatives": []}},
    "глутамат": {"severity": "high", "bg": {"name": "Мононатриев глутамат", "effect": "Изкуствен подобрител на вкуса.", "alternatives": []}, "en": {"name": "MSG", "effect": "Flavor enhancer.", "alternatives": []}},

    # --- ПОДСЛАДИТЕЛИ (Много важни) ---
    "аспартам": {"severity": "high", "bg": {"name": "Аспартам (E951)", "effect": "Изкуствен подсладител, свързан с неврологични проблеми.", "alternatives": ["Стевия"]}, "en": {"name": "Aspartame", "effect": "Artificial sweetener.", "alternatives": ["Stevia"]}},
    "aspartame": {"severity": "high", "bg": {"name": "Аспартам", "effect": "Изкуствен подсладител.", "alternatives": ["Stevia"]}, "en": {"name": "Aspartame", "effect": "Sweetener.", "alternatives": ["Stevia"]}},
    "захар": {"severity": "medium", "bg": {"name": "Захар", "effect": "Води до инсулинова резистентност и затлъстяване.", "alternatives": ["Еритритол"]}, "en": {"name": "Sugar", "effect": "High calories.", "alternatives": ["Erythritol"]}},
    "глюкоз": {"severity": "high", "bg": {"name": "Глюкозно-фруктозен сироп", "effect": "Уврежда черния дроб по-бързо от захарта.", "alternatives": ["Мед"]}, "en": {"name": "HFCS", "effect": "Liver damage risk.", "alternatives": ["Honey"]}},
    "фруктоз": {"severity": "medium", "bg": {"name": "Добавена фруктоза", "effect": "Натоварва метаболизма на мазнините.", "alternatives": []}, "en": {"name": "Fructose", "effect": "Metabolic strain.", "alternatives": []}},

    # --- МАЗНИНИ ---
    "палмов": {"severity": "high", "bg": {"name": "Палмово масло", "effect": "Наситени мазнини, запушващи съдовете.", "alternatives": ["Зехтин"]}, "en": {"name": "Palm Oil", "effect": "Clogs arteries.", "alternatives": ["Olive oil"]}},
    "хидрогени": {"severity": "high", "bg": {"name": "Хидрогенирани мазнини", "effect": "Трансмазнини - най-опасните за сърцето.", "alternatives": ["Краве масло"]}, "en": {"name": "Hydrogenated Fat", "effect": "Trans fats.", "alternatives": ["Butter"]}},
    "рафиниран": {"severity": "medium", "bg": {"name": "Рафинирано олио", "effect": "Омега-6 излишък, причинява възпаления.", "alternatives": ["Студено пресовано олио"]}, "en": {"name": "Refined oil", "effect": "Inflammatory.", "alternatives": ["Cold-pressed"]}},

    # --- ОЦВЕТИТЕЛИ ---
    "e133": {"severity": "high", "bg": {"name": "Е133 (Брилянтно синьо)", "effect": "Синтетичен оцветител, забранен в някои страни.", "alternatives": ["Естествени оцветители"]}, "en": {"name": "E133", "effect": "Synthetic dye.", "alternatives": ["Natural color"]}},
    "e102": {"severity": "high", "bg": {"name": "Е102 (Тартразин)", "effect": "Причинява хиперактивност при деца.", "alternatives": []}, "en": {"name": "E102", "effect": "Hyperactivity risk.", "alternatives": []}},
    "оцветител": {"severity": "medium", "bg": {"name": "Изкуствен оцветител", "effect": "Може да предизвика алергични реакции.", "alternatives": []}, "en": {"name": "Artificial color", "effect": "Allergy risk.", "alternatives": []}}
}

# ==============================================================================
# 2. ИНТЕРФЕЙС И ФУНКЦИИ
# ==============================================================================
lang_choice = st.sidebar.selectbox("Език / Language", ["Български (BG)", "English (EN)"])
lang = "bg" if "Български" in lang_choice else "en"

st.title("🥗 PRO Ingredient Scanner")
st.write("Качете ясна снимка от галерията за най-добър анализ.")

tab1, tab2 = st.tabs(["📁 Галерия / Gallery", "📷 Камера / Camera"])
img_file = None

with tab1:
    uploaded = st.file_uploader("Избери файл", type=["jpg", "jpeg", "png"])
    if uploaded: img_file = uploaded
with tab2:
    camera = st.camera_input("Снимай")
    if camera: img_file = camera

def ocr_process(img_bytes, target_lang):
    api_lang = "bul" if target_lang == "bg" else "eng"
    try:
        payload = {'apikey': 'helloworld', 'language': api_lang, 'scale': True, 'isTable': True}
        files = {'filename': ('img.jpg', img_bytes, 'image/jpeg')}
        r = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
        return r.json()["ParsedResults"][0]["ParsedText"]
    except: return ""

# ==============================================================================
# 3. АНАЛИЗ
# ==============================================================================
if img_file:
    st.image(img_file, use_container_width=True)
    with st.spinner("Анализиране..."):
        raw_text = ocr_process(img_file.getvalue(), lang)
        
        # Почистване: премахваме черти, скоби и символи, за да останат само буквите
        clean_text = re.sub(r'[^а-яА-Яa-zA-Z0-9\s]', ' ', raw_text.lower())
        
        if not raw_text.strip():
            st.error("Текстът не беше разчетен. Опитайте пак.")
            st.stop()

        found = []
        high_risk, med_risk = 0, 0
        
        for key, info in INGREDIENTS_DB.items():
            if key in clean_text:
                if info[lang]["name"] not in [i["name"] for i in found]:
                    found.append(info[lang])
                    if info["severity"] == "high": high_risk += 1
                    elif info["severity"] == "medium": med_risk += 1

        st.divider()
        if not found:
            st.success("✅ Чист продукт! Не открихме вредни съставки от базата ни данни.")
        else:
            if high_risk >= 1 or med_risk >= 2:
                st.error("🚨 ВНИМАНИЕ: Открити са опасни или вредни съставки!")
            else:
                st.warning("⚠️ Внимавайте: Продуктът съдържа умерено рискови съставки.")

            for item in found:
                st.markdown(f"**• 🛑 {item['name']}**")
                st.write(f"_{item['effect']}_")

            alts = set()
            for item in found:
                for a in item.get("alternatives", []): alts.add(a)
            if alts:
                st.subheader("💡 Здравословни замени:")
                for a in alts: st.success(f"👉 {a}")
