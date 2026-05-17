import streamlit as st

from PIL import Image
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
    "фруктоза": {
        "severity": "medium",
        "bg": {"name": "Добавена Фруктоза", "effect": "Когато е изолирана (не от цял плод), води до омазняване на черния дроб (стеатоза).", "alternatives": ["Цял пресен плод"]},
        "en": {"name": "Added Fructose", "effect": "When isolated (not from whole fruit), it leads to non-alcoholic fatty liver disease.", "alternatives": ["Whole fresh fruit"]}
    },
    "fructose": {
        "severity": "medium",
        "bg": {"name": "Добавена Фруктоза", "effect": "Когато е изолирана (не от цял плод), води до омазняване на черния дроб (стеатоза).", "alternatives": ["Цял пресен плод"]},
        "en": {"name": "Added Fructose", "effect": "When isolated (not from whole fruit), it leads to non-alcoholic fatty liver disease.", "alternatives": ["Whole fresh fruit"]}
    },

    # --- СПИСЪК: МАЛЦ, ЕЧЕМИК И ГЛУТЕНОВИ ---
    "малц": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Има изключително висок гликемичен индекс (по-висок от захарта). Съдържа глутен.", "alternatives": ["Овесени брашна", "Продукти без глутен"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "Has an extremely high glycemic index (higher than sugar). Contains gluten.", "alternatives": ["Oat flour", "Gluten-free alternatives"]}
    },
    "malt": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Има изключително висок гликемичен индекс (по-висок от захарта). Съдържа глутен.", "alternatives": ["Овесени брашна", "Продукти без глутен"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "Has an extremely high glycemic index (higher than sugar). Contains gluten.", "alternatives": ["Oat flour", "Gluten-free alternatives"]}
    },
    "ечемик": {
        "severity": "medium",
        "bg": {"name": "Ечемик (Глутен)", "effect": "Може да предизвика подуване, тежест и възпаления при хора с чувствителност към глутен.", "alternatives": ["Ориз", "Елда", "Киноа"]},
        "en": {"name": "Barley (Gluten)", "effect": "Can cause bloating, digestive discomfort, and inflammation in gluten-sensitive people.", "alternatives": ["Rice", "Buckwheat", "Quinoa"]}
    },
    "barley": {
        "severity": "medium",
        "bg": {"name": "Ечемик (Глутен)", "effect": "Може да предизвика подуване, тежест и възпаления при хора с чувствителност към глутен.", "alternatives": ["Ориз", "Елда", "Киноа"]},
        "en": {"name": "Barley (Gluten)", "effect": "Can cause bloating, digestive discomfort, and inflammation in gluten-sensitive people.", "alternatives": ["Rice", "Buckwheat", "Quinoa"]}
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

    # --- СПИСЪК: ОПАСНИ Е-ТА (КОНСЕРВАНТИ И ОЦВЕТИТЕЛИ) ---
    "e211": {
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Химически консервант. В комбинация с Витамин Ц може да образува бензен, който е силен канцероген.", "alternatives": ["Продукти без консерванти", "Домашно приготвена храна"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Chemical preservative. When combined with Vitamin C, it can form benzene, a known carcinogen.", "alternatives": ["Preservative-free food", "Homemade food"]}
    },
    "е211": { # Хваща ако е написано с кирилско 'Е'
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Химически консервант. В комбинация с Витамин Ц може да образува бензен, който е силен канцероген.", "alternatives": ["Продукти без консерванти", "Домашно приготвена храна"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Chemical preservative. When combined with Vitamin C, it can form benzene, a known carcinogen.", "alternatives": ["Preservative-free food", "Homemade food"]}
    },
    "e621": {
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Изкуствен подобрител на вкуса. Предизвиква пристрастяване, главоболие, сърцебиене и засилен апетит.", "alternatives": ["Естествена хималайска сол", "Сухи билки и чисти подправки"]},
        "en": {"name": "E621 (Monosodium Glutamate / MSG)", "effect": "Excitotoxin that enhances flavor. Can cause headaches, sweating, heart palpitations, and overeating.", "alternatives": ["Natural sea salt", "Pure dry herbs and spices"]}
    },
    "е621": {
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Изкуствен подобрител на вкуса. Предизвиква пристрастяване, главоболие, сърцебиене и засилен апетит.", "alternatives": ["Естествена хималайска сол", "Сухи билки и чисти подправки"]},
        "en": {"name": "E621 (Monosodium Glutamate / MSG)", "effect": "Excitotoxin that enhances flavor. Can cause headaches, sweating, heart palpitations, and overeating.", "alternatives": ["Natural sea salt", "Pure dry herbs and spices"]}
    },
    "e250": {
        "severity": "high",
        "bg": {"name": "Е250 (Натриев нитрит)", "effect": "Използва се масово в колбасите за розов цвят. Силно токсичен в по-големи количества, класифициран като канцерогенен.", "alternatives": ["Прясно чисто месо", "Продукти без нитрити"]},
        "en": {"name": "E250 (Sodium Nitrite)", "effect": "Commonly used in cured meats. Forms nitrosamines in the stomach, which are highly carcinogenic.", "alternatives": ["Fresh un-cured meat", "Nitrite-free products"]}
    },
    "е250": {
        "severity": "high",
        "bg": {"name": "Е250 (Натриев нитрит)", "effect": "Използва се масово в колбасите за розов цвят. Силно токсичен в по-големи количества, класифициран като канцерогенен.", "alternatives": ["Прясно чисто месо", "Продукти без нитрити"]},
        "en": {"name": "E250 (Sodium Nitrite)", "effect": "Commonly used in cured meats. Forms nitrosamines in the stomach, which are highly carcinogenic.", "alternatives": ["Fresh un-cured meat", "Nitrite-free products"]}
    }
}

# ==============================================================================
# 2. ИНТЕРФЕЙС И ПОТРЕБИТЕЛСКИ ИЗБОР
# ==============================================================================
lang_choice = st.sidebar.selectbox("Изберете език / Choose language", ["Български (BG)", "English (EN)"])
lang = "bg" if "Български" in lang_choice else "en"

if lang == "bg":
    st.title("🥗 Скенер за вредни съставки")
    st.write("Снимайте списъка със съставките от етикета на продукта, за да проверим дали е полезен.")
    capture_label = "Насочете камерата към текста на етикета:"
else:
    st.title("🥗 Ingredient Safety Scanner")
    st.write("Take a photo of the ingredients text on the product label to check its safety.")
    capture_label = "Point your camera at the label text:"

# Компонент за пускане на камерата на живо в браузъра
img_file = st.camera_input(capture_label)

# ==============================================================================
# 3. ЛОГИКА ЗА СКАНИРАНЕ И АНАЛИЗ
# ==============================================================================
if img_file is not None:
    st.image(img_file, caption="Сканирана снимка" if lang == "bg" else "Scanned image")
    
    with st.spinner("Четене на етикета..." if lang == "bg" else "Reading label..."):
        image = Image.open(img_file)
        
        # Настройка на Tesseract за едновременно четене на БГ и ЕН
        custom_config = r'-l bul+eng --psm 6'
        full_text = pytesseract.image_to_string(image, config=custom_config)
        
        st.subheader("Прочетен текст от продукта:" if lang == "bg" else "Detected Text from Product:")
        if full_text.strip():
            st.info(full_text)
        else:
            st.error("Не беше разпознат текст. Моля, опитайте пак при по-добра светлина и фокус." if lang == "bg" else "No text detected. Please try again with better lighting and focus.")
            st.stop()
        
        # Търсене на съвпадения в текста
        text_lower = full_text.lower()
        found_ingredients = []
        high_risk_count = 0
        medium_risk_count = 0
        
        for key, info in INGREDIENTS_DB.items():
            if re.search(key, text_lower):
                # Проверка за избягване на дублиране (ако намери съставката и на двата езика)
                if info[lang]["name"] not in [i["name"] for i in found_ingredients]:
                    found_ingredients.append(info[lang])
                    if info["severity"] == "high":
                        high_risk_count += 1
                    elif info["severity"] == "medium":
                        medium_risk_count += 1
        
        st.divider()
        st.subheader("ЗДРАВНА ОЦЕНКА:" if lang == "bg" else "HEALTH EVALUATION:")
        
        # --- Сценарий 1: Чист/Полезен продукт ---
        if not found_ingredients:
            if lang == "bg":
                st.success("✅ ПОЛЕЗЕН / ЧИСТ ПРОДУКТ! Не бяха открити вредни съставки от нашата база данни.")
            else:
                st.success("✅ HEALTHY / CLEAN PRODUCT! No harmful ingredients were detected from our database.")
        
        # --- Сценарий 2: Открити са вредни неща ---
        else:
            # Преценяване на нивото на опасност
            if high_risk_count >= 1 or medium_risk_count >= 3:
                if lang == "bg":
                    st.error("🚨 ВРЕДЕН ПРОДУКТ! Съдържа силно токсични или опасни за здравето вещества. Избягвайте консумацията!")
                else:
                    st.error("🚨 HARMFUL PRODUCT! Contains highly toxic or hazardous substances. Avoid consuming!")
                show_alternatives = True
            else:
                if lang == "bg":
                    st.warning("⚠️ СРЕДНО ПОЛЕЗЕН (Нещо по средата). Консумирайте в ограничени количества и с повишено внимание.")
                else:
                    st.warning("⚠️ MODERATELY HEALTHY (In-between). Consume in limited quantities and with caution.")
                show_alternatives = False
            
            # Показване на списъка с открити вредители и ефектите им
            st.write("🔍 **Конкретни открити съставки:**" if lang == "bg" else "🔍 **Specific detected ingredients:**")
            all_alternatives = set()
            
            for ing in found_ingredients:
                st.markdown(f"• 🛑 **{ing['name']}**")
                st.write(f"  *Ефект върху тялото:* {ing['effect']}")
                if show_alternatives:
                    for alt in ing["alternatives"]:
                        all_alternatives.add(alt)
            
            # --- Сценарий 3: Показване на здравословни алтернативи (само ако продуктът е много вреден) ---
            if show_alternatives and all_alternatives:
                st.write("---")
                st.subheader("💡 ЗДРАВОСЛОВНИ ЗАМЕСТИТЕЛИ:" if lang == "bg" else "💡 HEALTHY ALTERNATIVES:")
                st.write("Вместо този продукт, можете да изберете или използвате:" if lang == "bg" else "Instead of this product, you can choose or use:")
                for alt in all_alternatives:
                    st.success(f"👉 {alt}")
import streamlit as st
import requests
from PIL import Image
import io
import re

# Настройка на страницата
st.set_page_config(page_title="Smart Label Scanner", page_icon="🥗")

# ПЪЛЕН СПИСЪК НА ВРЕДНИТЕ СЪСТАВКИ
INGREDIENTS_DB = {
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
    "малц": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Има изключително висок гликемичен индекс (по-висок от захарта). Съдържа глутен.", "alternatives": ["Овесени брашна", "Продукти без глутен"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "Has an extremely high glycemic index (higher than sugar). Contains gluten.", "alternatives": ["Oat flour", "Gluten-free alternatives"]}
    },
    "malt": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Има изключително висок гликемичен индекс (по-висок от захарта). Съдържа глутен.", "alternatives": ["Овесени брашна", "Продукти без глутен"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "Has an extremely high glycemic index (higher than sugar). Contains gluten.", "alternatives": ["Oat flour", "Gluten-free alternatives"]}
    },
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
    "e211": {
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Химически консервант. В комбинация с Витамин Ц може да образува бензен (канцероген).", "alternatives": ["Продукти без консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Chemical preservative. When combined with Vitamin C, it can form benzene.", "alternatives": ["Preservative-free food"]}
    },
    "е211": {
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Химически консервант. В комбинация с Витамин Ц може да образува бензен (канцероген).", "alternatives": ["Продукти без консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Chemical preservative. When combined with Vitamin C, it can form benzene.", "alternatives": ["Preservative-free food"]}
    }
}

# Избор на език
lang_choice = st.sidebar.selectbox("Изберете език / Choose language", ["Български (BG)", "English (EN)"])
lang = "bg" if "Български" in lang_choice else "en"

if lang == "bg":
    st.title("🥗 Скенер за вредни съставки")
    st.write("Снимайте етикета със съставките на продукта.")
    capture_label = "Насочете камерата към текста:"
else:
    st.title("🥗 Ingredient Safety Scanner")
    st.write("Take a photo of the ingredients list on the label.")
    capture_label = "Point your camera at the text:"

img_file = st.camera_input(capture_label)

def ocr_space_file(img_bytes, target_lang):
    """Изпраща снимката към безплатния OCR.Space API за разпознаване на текст"""
    api_lang = "bul" if target_lang == "bg" else "eng"
    try:
        # Използваме публичния безплатен ключ на OCR.Space ('helloworld')
        payload = {
            'apikey': 'helloworld',
            'language': api_lang,
            'isOverlayRequired': False,
            'scale': True
        }
        files = {'filename': ('image.jpg', img_bytes, 'image/jpeg')}
        response = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
        result = response.json()
        
        if result.get("OCRExitCode") == 1:
            parsed_text = result["ParsedResults"][0]["ParsedText"]
            return parsed_text
        else:
            return ""
    except Exception:
        return ""

if img_file is not None:
    st.image(img_file, caption="Сканирана снимка" if lang == "bg" else "Scanned image")
    
    with st.spinner("Анализиране на текста онлайн..." if lang == "bg" else "Analyzing text online..."):
        # Преобразуване на снимката в байтове
        img_bytes = img_file.getvalue()
        
        # Сканиране чрез безплатното онлайн API
        full_text = ocr_space_file(img_bytes, lang)
        
        # Ако първият избор на език не върне нищо, пробваме с другия (за максимално покритие)
        if not full_text.strip():
            backup_lang = "en" if lang == "bg" else "bg"
            full_text = ocr_space_file(img_bytes, backup_lang)

        st.subheader("Прочетен текст от продукта:" if lang == "bg" else "Detected Text from Product:")
        if full_text.strip():
            st.info(full_text)
        else:
            st.error("Не беше разпознат текст. Моля, снимайте по-отблизо, на светлина и фокус." if lang == "bg" else "No text detected. Please take a closer picture with better lighting.")
            st.stop()
        
        # Търсене в базата данни
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
            st.success("✅ ПОЛЕЗЕН / ЧИСТ ПРОДУКТ! Не бяха открити критични вредни съставки." if lang == "bg" else "✅ HEALTHY / CLEAN PRODUCT! No critical harmful ingredients detected.")
        else:
            if high_risk_count >= 1 or medium_risk_count >= 3:
                st.error("🚨 ВРЕДЕН ПРОДУКТ! Избягвайте консумацията!" if lang == "bg" else "🚨 HARMFUL PRODUCT! Avoid consuming!")
                show_alternatives = True
            else:
                st.warning("⚠️ СРЕДНО ПОЛЕЗЕН. Консумирайте в ограничени количества." if lang == "bg" else "⚠️ MODERATELY HEALTHY. Consume in limited quantities.")
                show_alternatives = False
            
            st.write("🔍 **Открити съставки:**" if lang == "bg" else "🔍 **Detected ingredients:**")
            all_alternatives = set()
            for ing in found_ingredients:
                st.markdown(f"• 🛑 **{ing['name']}** — {ing['effect']}")
                if show_alternatives:
                    for alt in ing["alternatives"]:
                        all_alternatives.add(alt)
            
            if show_alternatives and all_alternatives:
                st.write("---")
                st.subheader("💡 ЗДРАВОСЛОВНИ ЗАМЕСТИТЕЛИ:" if lang == "bg" else "💡 HEALTHY ALTERNATIVES:")
                for alt in all_alternatives:
                    st.success(f"👉 {alt}")
