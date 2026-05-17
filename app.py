import streamlit as st
import requests
from PIL import Image
import io
import re

# Настройка на заглавието на страницата в браузъра
st.set_page_config(page_title="Smart Label Scanner", page_icon="🥗")

# ==============================================================================
# 1. ПЪЛЕН СПИСЪК (БАЗА ДАННИ) НА ВРЕДНИТЕ СЪСТАВКИ (ДВУЕЗИЧЕН)
# ==============================================================================
INGREDIENTS_DB = {
    # --- СПИСЪК: АЛКОХОЛ ---
    "алкохол": {
        "severity": "high",
        "bg": {"name": "Алкохол (Етанол)", "effect": "Токсичен за черния дроб и нервната система. Силно дехидратира тялото.", "alternatives": ["Вода", "Натурален студен чай", "Безалкохолен коктейл"]},
        "en": {"name": "Alcohol (Ethanol)", "effect": "Toxic to the liver and nervous system. Causes severe dehydration.", "alternatives": ["Water", "Natural iced tea", "Mocktails"]}
    },
    "alcohol": {
        "severity": "high",
        "bg": {"name": "Алкохол (Етанол)", "effect": "Токсичен за черния дроб и нервната система. Силно дехидратира тялото.", "alternatives": ["Вода", "Натурален студен чай", "Безалкохолен коктейл"]},
        "en": {"name": "Alcohol (Ethanol)", "effect": "Toxic to the liver and nervous system. Causes severe dehydration.", "alternatives": ["Water", "Natural iced tea", "Mocktails"]}
    },
    "етанол": {
        "severity": "high",
        "bg": {"name": "Етанол", "effect": "Чист алкохол. Влияе негативно на мозъчната дейност и черния дроб.", "alternatives": ["Чисти сокове", "Вода"]},
        "en": {"name": "Ethanol", "effect": "Pure alcohol. Negatively affects brain function and liver.", "alternatives": ["Pure juices", "Water"]}
    },
    "ethanol": {
        "severity": "high",
        "bg": {"name": "Етанол", "effect": "Чист алкохол. Влияе негативно на мозъчната дейност и черния дроб.", "alternatives": ["Чисти сокове", "Вода"]},
        "en": {"name": "Ethanol", "effect": "Pure alcohol. Negatively affects brain function and liver.", "alternatives": ["Pure juices", "Water"]}
    },

    # --- СПИСЪК: ЗАХАРИ И ПОДСЛАДИТЕЛИ ---
    "захар": {
        "severity": "medium",
        "bg": {"name": "Бяла захар", "effect": "Води до резки скокове в инсулина, риск от затлъстяване, диабет и кариеси.", "alternatives": ["Стевия", "Еритритол", "Мед"]},
        "en": {"name": "Sugar", "effect": "Causes sharp insulin spikes, risks of obesity, type 2 diabetes, and tooth decay.", "alternatives": ["Stevia", "Erythritol", "Honey"]}
    },
    "sugar": {
        "severity": "medium",
        "bg": {"name": "Бяла захар", "effect": "Води до резки скокове в инсулина, риск от затлъстяване, диабет и кариеси.", "alternatives": ["Стевия", "Еритритол", "Мед"]},
        "en": {"name": "Sugar", "effect": "Causes sharp insulin spikes, risks of obesity, type 2 diabetes, and tooth decay.", "alternatives": ["Stevia", "Erythritol", "Honey"]}
    },
    "глюкоз": {
        "severity": "high",
        "bg": {"name": "Глюкозно-фруктозен сироп", "effect": "Рязко натоварва черния дроб, превръща се директно в мазнини, уврежда метаболизма.", "alternatives": ["Продукти без добавена захар", "Пресни плодове"]},
        "en": {"name": "Glucose-Fructose Syrup / HFCS", "effect": "Strains the liver, converts directly into fat, disrupts metabolism.", "alternatives": ["No added sugar products", "Fresh fruits"]}
    },
    "glucose": {
        "severity": "high",
        "bg": {"name": "Глюкозно-фруктозен сироп", "effect": "Рязко натоварва черния дроб, превръща се директно в мазнини, уврежда метаболизма.", "alternatives": ["Продукти без добавена захар", "Пресни плодове"]},
        "en": {"name": "Glucose-Fructose Syrup / HFCS", "effect": "Strains the liver, converts directly into fat, disrupts metabolism.", "alternatives": ["No added sugar products", "Fresh fruits"]}
    },

    # --- СПИСЪК: ХИДРОГЕНИРАНИ МАЗНИНИ ---
    "палмово": {
        "severity": "high",
        "bg": {"name": "Палмово масло", "effect": "Богато на наситени мазнини, които запушват артериите и вдигат лошия холестерол (LDL).", "alternatives": ["Студено пресован зехтин", "Краве масло", "Кокосово масло"]},
        "en": {"name": "Palm Oil", "effect": "High in saturated fats, which can clog arteries and increase bad cholesterol (LDL).", "alternatives": ["Extra virgin olive oil", "Butter", "Coconut oil"]}
    },
    "palm": {
        "severity": "high",
        "bg": {"name": "Палмово масло", "effect": "Богато на наситени мазнини, които запушват артериите и вдигат лошия холестерол (LDL).", "alternatives": ["Студено пресован зехтин", "Краве масло", "Кокосово масло"]},
        "en": {"name": "Palm Oil", "effect": "High in saturated fats, which can clog arteries and increase bad cholesterol (LDL).", "alternatives": ["Extra virgin olive oil", "Butter", "Coconut oil"]}
    },
    "хидрогенирани": {
        "severity": "high",
        "bg": {"name": "Хидрогенирани мазнини (Трансмазнини)", "effect": "Най-опасните мазнини. Предизвикват сериозни сърдечно-съдови заболявания и вътрешни възпаления.", "alternatives": ["Нерафинирани растителни масла"]},
        "en": {"name": "Hydrogenated Fats (Trans Fats)", "effect": "The most dangerous fats. Directly linked to heart disease, strokes, and systemic inflammation.", "alternatives": ["Unrefined vegetable oils"]}
    },
    "hydrogenated": {
        "severity": "high",
        "bg": {"name": "Хидрогенирани мазнини (Трансмазнини)", "effect": "Най-опасните мазнини. Предизвикват сериозни сърдечно-съдови заболявания и вътрешни възпаления.", "alternatives": ["Нерафинирани растителни масла"]},
        "en": {"name": "Hydrogenated Fats (Trans Fats)", "effect": "The most dangerous fats. Directly linked to heart disease, strokes, and systemic inflammation.", "alternatives": ["Unrefined vegetable oils"]}
    },

    # --- СПИСЪК: ОПАСНИ Е-ТА ---
    "e211": {
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Химически консервант. В комбинация с Витамин Ц може да образува бензен, който е силен канцероген.", "alternatives": ["Продукти без консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Preservative. Can form benzene (carcinogen) when mixed with Vitamin C.", "alternatives": ["Preservative-free food"]}
    },
    "е211": { 
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Химически консервант. В комбинация с Витамин Ц може да образува бензен, който е силен канцероген.", "alternatives": ["Продукти без консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Preservative. Can form benzene (carcinogen) when mixed with Vitamin C.", "alternatives": ["Preservative-free food"]}
    },
    "e621": {
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Изкуствен подобрител на вкуса. Предизвиква изкуствен апетит и главоболие.", "alternatives": ["Чисти подправки", "Хималайска сол"]},
        "en": {"name": "E621 (Monosodium Glutamate / MSG)", "effect": "Flavor enhancer. Can trigger headaches and overeating.", "alternatives": ["Pure spices", "Sea salt"]}
    },
    "е621": {
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Изкуствен подобрител на вкуса. Предизвиква изкуствен апетит и главоболие.", "alternatives": ["Чисти подправки", "Хималайска сол"]},
        "en": {"name": "E621 (Monosodium Glutamate / MSG)", "effect": "Flavor enhancer. Can trigger headaches and overeating.", "alternatives": ["Pure spices", "Sea salt"]}
    }
}

# ==============================================================================
# 2. ИНТЕРФЕЙС И ПОТРЕБИТЕЛСКИ ИЗБОР
# ==============================================================================
lang_choice = st.sidebar.selectbox("Изберете език / Choose language", ["Български (BG)", "English (EN)"])
lang = "bg" if "Български" in lang_choice else "en"

if lang == "bg":
    st.title("🥗 Скенер за вредни съставки")
    st.write("Качете снимка на етикета или го заснемете с камерата, за да го анализираме.")
    tab1_title, tab2_title = "📁 Качване от галерия", "📷 Снимка на момента"
    upload_label = "Изберете снимка от устройството си:"
    camera_label = "Насочете камерата към етикета:"
else:
    st.title("🥗 Ingredient Safety Scanner")
    st.write("Upload a label photo or take one using your camera for analysis.")
    tab1_title, tab2_title = "📁 Upload from Gallery", "📷 Take Live Photo"
    upload_label = "Choose an image file from your device:"
    camera_label = "Point your camera at the label text:"

# Създаване на раздели (Tabs) за двата метода на въвеждане
tab1, tab2 = st.tabs([tab1_title, tab2_title])
img_file = None

with tab1:
    uploaded_file = st.file_uploader(upload_label, type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        img_file = uploaded_file

with tab2:
    camera_file = st.camera_input(camera_label)
    if camera_file is not None:
        img_file = camera_file

# Функция за уеб-базиран OCR чрез OCR.Space API
def ocr_space_file(img_bytes, target_lang):
    api_lang = "bul" if target_lang == "bg" else "eng"
    try:
        payload = {
            'apikey': 'helloworld',  # Безплатен публичен ключ
            'language': api_lang,
            'isOverlayRequired': False,
            'scale': True
        }
        files = {'filename': ('image.jpg', img_bytes, 'image/jpeg')}
        response = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
        result = response.json()
        
        if result.get("OCRExitCode") == 1:
            return result["ParsedResults"][0]["ParsedText"]
        return ""
    except Exception:
        return ""

# ==============================================================================
# 3. ЛОГИКА ЗА СКАНИРАНЕ И АНАЛИЗ
# ==============================================================================
if img_file is not None:
    st.image(img_file, caption="Заредена снимка" if lang == "bg" else "Loaded image", use_container_width=True)
    
    with st.spinner("Четене на етикета..." if lang == "bg" else "Reading label..."):
        img_bytes = img_file.getvalue()
        full_text = ocr_space_file(img_bytes, lang)
        
        # Ако липсва текст на избрания език, тестваме с другия за сигурност
        if not full_text.strip():
            backup_lang = "en" if lang == "bg" else "bg"
            full_text = ocr_space_file(img_bytes, backup_lang)

        st.subheader("Прочетен текст от продукта:" if lang == "bg" else "Detected Text from Product:")
        if full_text.strip():
            st.info(full_text)
        else:
            st.error("Не беше разпознат текст. Моля, уверете се, че снимката е на фокус, текстът е хоризонтален и има добра светлина." if lang == "bg" else "No text detected. Please make sure the photo is focused, text is horizontal, and lighting is good.")
            st.stop()
        
        # Търсене на съвпадения
        text_lower = full_text.lower()
        found_ingredients = []
        high_risk_count = 0
        medium_risk_count = 0
        
        for key, info in INGREDIENTS_DB.items():
            if re.search(key, text_lower):
                if info[lang]["name"] not in [i["name"] for i in found_ingredients]:
                    found_ingredients.append(info[lang])
                    if info["severity"] == "high":
                        high_risk_count += 1
                    elif info["severity"] == "medium":
                        medium_risk_count += 1
        
        st.divider()
        st.subheader("ЗДРАВНА ОЦЕНКА:" if lang == "bg" else "HEALTH EVALUATION:")
        
        if not found_ingredients:
            st.success("✅ ПОЛЕЗЕН / ЧИСТ ПРОДУКТ! Не бяха открити вредни съставки от нашата база данни." if lang == "bg" else "✅ HEALTHY / CLEAN PRODUCT! No harmful ingredients were detected from our database.")
        else:
            if high_risk_count >= 1 or medium_risk_count >= 3:
                st.error("🚨 ВРЕДЕН ПРОДУКТ! Съдържа силно токсични или опасни за здравето вещества. Избягвайте консумацията!" if lang == "bg" else "🚨 HARMFUL PRODUCT! Contains highly toxic or hazardous substances. Avoid consuming!")
                show_alternatives = True
            else:
                st.warning("⚠️ СРЕДНО ПОЛЕЗЕН (Нещо по средата). Консумирайте в ограничени количества." if lang == "bg" else "⚠️ MODERATELY HEALTHY (In-between). Consume in limited quantities.")
                show_alternatives = False
            
            st.write("🔍 **Конкретни открити съставки:**" if lang == "bg" else "🔍 **Specific detected ingredients:**")
            all_alternatives = set()
            
            for ing in found_ingredients:
                st.markdown(f"• 🛑 **{ing['name']}**")
                st.write(f"  *Ефект върху тялото:* {ing['effect']}")
                if show_alternatives:
                    for alt in ing["alternatives"]:
                        all_alternatives.add(alt)
            
            if show_alternatives and all_alternatives:
                st.write("---")
                st.subheader("💡 ЗДРАВОСЛОВНИ ЗАМЕСТИТЕЛИ:" if lang == "bg" else "💡 HEALTHY ALTERNATIVES:")
                for alt in all_alternatives:
                    st.success(f"👉 {alt}")
