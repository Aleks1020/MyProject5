import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# Настройка на заглавието на страницата
st.set_page_config(page_title="Smart Label Scanner", page_icon="🥗", layout="centered")

# БАЗА ДАННИ С ВСИЧКИ ВРЕДНИ СЪСТАВКИ (Разширени списъци)
INGREDIENTS_DB = {
    # === ГРУПА: ЗАХАРИ И СИРОПИ ===
    "захар": {
        "severity": "medium",
        "bg": {"name": "Захар", "effect": "Риск от затлъстяване, инсулинова резистентност и кариеси.", "alternatives": ["Стевия", "Еритритол", "Мед"]},
        "en": {"name": "Sugar", "effect": "Risk of obesity, insulin resistance, and tooth decay.", "alternatives": ["Stevia", "Erythritol", "Honey"]}
    },
    "sugar": {
        "severity": "medium",
        "bg": {"name": "Захар", "effect": "Риск от затлъстяване, инсулинова резистентност и кариеси.", "alternatives": ["Стевия", "Еритритол", "Мед"]},
        "en": {"name": "Sugar", "effect": "Risk of obesity, insulin resistance, and tooth decay.", "alternatives": ["Stevia", "Erythritol", "Honey"]}
    },
    "глюкоз": {
        "severity": "high",
        "bg": {"name": "Глюкозно-фруктозен сироп / Глюкоза", "effect": "Рязко вдига кръвната захар, претоварва черния дроб и води до мастни натрупвания.", "alternatives": ["Натурален плодов сок", "Вода"]},
        "en": {"name": "Glucose-Fructose Syrup / Glucose", "effect": "Causes severe blood sugar spikes, strains the liver, and leads to fat storage.", "alternatives": ["Natural fruit juice", "Water"]}
    },
    "glucose": {
        "severity": "high",
        "bg": {"name": "Глюкозно-фруктозен сироп / Глюкоза", "effect": "Рязко вдига кръвната захар, претоварва черния дроб.", "alternatives": ["Натурален плодов сок", "Вода"]},
        "en": {"name": "Glucose-Fructose Syrup / Glucose", "effect": "Causes severe blood sugar spikes, strains the liver.", "alternatives": ["Natural fruit juice", "Water"]}
    },
    "фруктоз": {
        "severity": "medium",
        "bg": {"name": "Фруктозен сироп", "effect": "При прекомерна употреба води до омазняване на черния дроб (стеатоза).", "alternatives": ["Пресни плодове"]},
        "en": {"name": "Fructose Syrup", "effect": "Excessive consumption leads to non-alcoholic fatty liver disease.", "alternatives": ["Fresh whole fruits"]}
    },
    "fructose": {
        "severity": "medium",
        "bg": {"name": "Фруктозен сироп", "effect": "При прекомерна употреба води до омазняване на черния дроб.", "alternatives": ["Пресни плодове"]},
        "en": {"name": "Fructose Syrup", "effect": "Excessive consumption leads to fatty liver.", "alternatives": ["Fresh whole fruits"]}
    },

    # === ГРУПА: МАЛЦ И ЗЪРНЕНИ (АЛЕРГЕНИ / ВИСОК ГЛИКЕМИЧЕН ИНДЕКС) ===
    "малц": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Изключително висок гликемичен индекс (по-висок от захарта). Съдържа глутен.", "alternatives": ["Продукти без глутен", "Кафяв ориз"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "Extremely high glycemic index (higher than table sugar). Contains gluten.", "alternatives": ["Gluten-free alternatives", "Brown rice"]}
    },
    "malt": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Изключително висок гликемичен индекс. Съдържа глутен.", "alternatives": ["Продукти без глутен"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "Extremely high glycemic index. Contains gluten.", "alternatives": ["Gluten-free alternatives"]}
    },
    "ечемик": {
        "severity": "medium",
        "bg": {"name": "Ечемик (Глутен)", "effect": "Силен алерген за хора с цолиакия или непоносимост към глутен.", "alternatives": ["Елда", "Ориз", "Киноа"]},
        "en": {"name": "Barley (Gluten)", "effect": "Strong allergen for people with celiac disease or gluten sensitivity.", "alternatives": ["Buckwheat", "Rice", "Quinoa"]}
    },
    "barley": {
        "severity": "medium",
        "bg": {"name": "Ечемик (Глутен)", "effect": "Силен алерген за хора с непоносимост към глутен.", "alternatives": ["Елда", "Ориз", "Киноа"]},
        "en": {"name": "Barley (Gluten)", "effect": "Strong allergen for people with gluten sensitivity.", "alternatives": ["Buckwheat", "Rice", "Quinoa"]}
    },

    # === ГРУПА: АЛКОХОЛ ===
    "алкохол": {
        "severity": "high",
        "bg": {"name": "Алкохол (Етанол)", "effect": "Невротоксичен, натоварва черния дроб, дехидратира клетките и забавя метаболизма.", "alternatives": ["Безалкохолни алтернативи", "Комбуча", "Вода"]},
        "en": {"name": "Alcohol (Ethanol)", "effect": "Neurotoxic, strains the liver, dehydrates cells, and slows down metabolism.", "alternatives": ["Non-alcoholic alternatives", "Kombucha", "Water"]}
    },
    "alcohol": {
        "severity": "high",
        "bg": {"name": "Алкохол (Етанол)", "effect": "Невротоксичен, натоварва черния дроб и дехидратира.", "alternatives": ["Безалкохолни алтернативи", "Вода"]},
        "en": {"name": "Alcohol (Ethanol)", "effect": "Neurotoxic, strains the liver, and dehydrates.", "alternatives": ["Non-alcoholic alternatives", "Water"]}
    },
    "спирт": {
        "severity": "high",
        "bg": {"name": "Етилов Спирт", "effect": "Силно токсичен за храносмилателната и нервната система.", "alternatives": ["Напитки без съдържание на спирт"]},
        "en": {"name": "Ethyl Alcohol", "effect": "Highly toxic to the digestive and nervous systems.", "alternatives": ["Alcohol-free beverages"]}
    },

    # === ГРУПА: ОПАСНИ Е-ТА (КОНСЕРВАНТИ, ОЦВЕТИТЕЛИ, ОВКУСИТЕЛИ) ===
    "e211": {
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Консервант. Може да предизвика хиперактивност при деца и алергични реакции.", "alternatives": ["Продукти без изкуствени консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Preservative. May promote hyperactivity in children and trigger allergic reactions.", "alternatives": ["Preservative-free products"]}
    },
    "е211": { # кирилица 'е'
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Консервант. Може да предизвика хиперактивност и алергии.", "alternatives": ["Продукти без изкуствени консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Preservative. May promote hyperactivity and allergies.", "alternatives": ["Preservative-free products"]}
    },
    "e621": {
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Овкусител. Предизвиква изкуствен глад, главоболие (синдром на китайския ресторант).", "alternatives": ["Естествени подправки, хималайска сол"]},
        "en": {"name": "E621 (Monosodium Glutamate / MSG)", "effect": "Flavor enhancer. Excitotoxin that overstimulates neurons, causes headaches and overeating.", "alternatives": ["Natural spices, sea salt, herbs"]}
    },
    "е621": { # кирилица 'е'
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Овкусител. Предизвиква изкуствен глад и главоболие.", "alternatives": ["Естествени подправки"]},
        "en": {"name": "E621 (MSG)", "effect": "Flavor enhancer. Causes headaches and overeating.", "alternatives": ["Natural spices"]}
    },
    "e250": {
        "severity": "high",
        "bg": {"name": "Е250 (Натриев нитрит)", "effect": "Използва се в колбаси. При термична обработка образува канцерогенни нитрозамини.", "alternatives": ["Чисто месо без добавени нитрити"]},
        "en": {"name": "E250 (Sodium Nitrite)", "effect": "Used in cured meats. Forms carcinogenic nitrosamines when heated.", "alternatives": ["Fresh organic meat, nitrite-free products"]}
    },
    "е250": {
        "severity": "high",
        "bg": {"name": "Е250 (Натриев нитрит)", "effect": "Използва се в колбаси. Потенциално канцерогенен.", "alternatives": ["Чисто месо"]},
        "en": {"name": "E250 (Sodium Nitrite)", "effect": "Potential carcinogen found in processed meats.", "alternatives": ["Fresh organic meat"]}
    },
    "e951": {
        "severity": "high",
        "bg": {"name": "Е951 (Аспартам)", "effect": "Изкуствен подсладител. Свързва се с главоболие, мигрена и метаболитни смущения.", "alternatives": ["Стевия", "Ксилитол"]},
        "en": {"name": "E951 (Aspartame)", "effect": "Artificial sweetener. Linked to headaches, migraines, and potential metabolic disruption.", "alternatives": ["Stevia", "Xylitol"]}
    },
    "е951": {
        "severity": "high",
        "bg": {"name": "Е951 (Аспартам)", "effect": "Изкуствен подсладител. Може да причини главоболие.", "alternatives": ["Стевия"]},
        "en": {"name": "E951 (Aspartame)", "effect": "Artificial sweetener. Can cause headaches.", "alternatives": ["Stevia"]}
    },

    # === ГРУПА: ОПАСНИ МАЗНИНИ ===
    "палмово": {
        "severity": "high",
        "bg": {"name": "Палмово масло / Палмова мазнина", "effect": "Богато на наситени мазнини, запушва артериите и повишава лошия холестерол (LDL).", "alternatives": ["Студено пресован зехтин", "Кокосово масло", "Краве масло"]},
        "en": {"name": "Palm Oil / Palm Fat", "effect": "High in saturated fats, clogs arteries, and significantly raises bad cholesterol (LDL).", "alternatives": ["Extra virgin olive oil", "Coconut oil", "Butter"]}
    },
    "palm": {
        "severity": "high",
        "bg": {"name": "Палмово масло", "effect": "Запушва артериите и повишава лошия холестерол (LDL).", "alternatives": ["Зехтин", "Кокосово масло"]},
        "en": {"name": "Palm Oil", "effect": "Clogs arteries and raises bad cholesterol (LDL).", "alternatives": ["Olive oil", "Coconut oil"]}
    },
    "хидрогенирани": {
        "severity": "high",
        "bg": {"name": "Хидрогенирани / Частично хидрогенирани мазнини", "effect": "Трансмазнини. Силно възпалителни процеси в тялото, риск от инфаркт и инсулт.", "alternatives": ["Краве масло", "Слънчогледово олио (нехидрогенирано)"]},
        "en": {"name": "Hydrogenated / Partially Hydrogenated Oils", "effect": "Trans fats. Highly inflammatory, damages blood vessels, drastically increases heart disease risk.", "alternatives": ["Ghee", "Unrefined oils"]}
    },
    "hydrogenated": {
        "severity": "high",
        "bg": {"name": "Хидрогенирани мазнини", "effect": "Трансмазнини. Силно възпалителни, опасни за сърцето.", "alternatives": ["Естествени масла"]},
        "en": {"name": "Hydrogenated Oils", "effect": "Trans fats. Highly inflammatory and dangerous for heart health.", "alternatives": ["Natural unrefined oils"]}
    }
}

# Инициализиране и кеширане на EasyOCR модела
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_ocr()

# Странично меню за избор на език
lang_choice = st.sidebar.selectbox("Изберете език / Choose language", ["Български (BG)", "English (EN)"])
lang = "bg" if "Български" in lang_choice else "en"

# Динамичен текст според езика
if lang == "bg":
    st.title("🥗 Скенер за вредни съставки в храните")
    st.write("Насочете камерата и снимайте **текста със съставките** върху етикета (не баркода).")
    capture_label = "Снимайте етикета тук"
else:
    st.title("🥗 Food Ingredient Safety Scanner")
    st.write("Point your camera and take a photo of the **ingredients text** on the label (not the barcode).")
    capture_label = "Take a photo of the label"

# Компонент за камерата
img_file = st.camera_input(capture_label)

if img_file is not None:
    st.image(img_file, caption="Сканиран етикет" if lang == "bg" else "Scanned label")
    
    with st.spinner("Анализиране на съставките..." if lang == "bg" else "Analyzing ingredients..."):
        image = Image.open(img_file)
        img_array = np.array(image)
        
        # Разпознаване на текст
        results = reader.readtext(img_array, detail=0)
        full_text = " ".join(results)
        
        st.subheader("Прочетен текст от етикета:" if lang == "bg" else "Detected Text from Label:")
        st.info(full_text)
        
        # Сканиране на разчетения текст спрямо разширената база данни
        text_lower = full_text.lower()
        found_ingredients = []
        high_risk_count = 0
        medium_risk_count = 0
        
        for key, info in INGREDIENTS_DB.items():
            if re.search(key, text_lower):
                # Проверка за избягване на дублиране на съставки (ако се намерят по БГ и ЕН ключове едновременно)
                if info[lang]["name"] not in [i["name"] for i in found_ingredients]:
                    found_ingredients.append(info[lang])
                    if info["severity"] == "high":
                        high_risk_count += 1
                    elif info["severity"] == "medium":
                        medium_risk_count += 1
        
        st.divider()
        st.subheader("Резултати и оценка:" if lang == "bg" else "Evaluation & Results:")
        
        # 1. СЛУЧАЙ: Няма открити вредни неща
        if not found_ingredients:
            if lang == "bg":
                st.success("✅ ПОЛЕЗЕН / ЧИСТ ПРОДУКТ! Не бяха открити опасни вещества от базата данни.")
            else:
                st.success("✅ HEALTHY / CLEAN PRODUCT! No hazardous substances were detected.")
        else:
            # Оценка на крайната вредност
            if high_risk_count >= 1 or medium_risk_count >= 3:
                if lang == "bg":
                    st.error("🚨 ВРЕДЕН ПРОДУКТ! Опасен за редовна консумация. Вижте ефектите по-долу.")
                else:
                    st.error("🚨 HARMFUL PRODUCT! Dangerous for regular consumption. Check the effects below.")
                show_alternatives = True
            else:
                if lang == "bg":
                    st.warning("⚠️ СРЕДНО ПОЛЕЗЕН (Нещо по средата). Консумирайте в ограничени количества.")
                else:
                    st.warning("⚠️ MODERATELY HEALTHY (In-between). Consume in limited quantities.")
                show_alternatives = False
            
            # Показване на вредните съставки и ефектите им
            st.write("**Открити проблемни съставки:**" if lang == "bg" else "**Detected problematic ingredients:**")
            all_alternatives = set()
            for ing in found_ingredients:
                st.write(f"• **{ing['name']}** ➡️ {ing['effect']}")
                if show_alternatives:
                    for alt in ing["alternatives"]:
                        all_alternatives.add(alt)
            
            # 2. СЛУЧАЙ: Продуктът е много вреден -> Показваме здравословни алтернативи
            if show_alternatives and all_alternatives:
                st.write("---")
                st.write("💡 **Здравословни заместители на този продукт:**" if lang == "bg" else "💡 **Healthy alternatives for this product:**")
                for alt in all_alternatives:
                    st.markdown(f"- **{alt}**")
