import streamlit as st
import requests
import re

# Настройка на страницата
st.set_page_config(page_title="Ultimate Food Scanner", page_icon="🛡️", layout="wide")

# Избор на език (Добавен за работа на два езика)
lang_option = st.sidebar.selectbox("Language / Език", ["Български", "English"])
lang = "bg" if lang_option == "Български" else "en"

# ==============================================================================
# 1. ОБЕДИНЕНА И РАЗШИРЕНА БАЗА ДАННИ (ТВОЯТ СПИСЪК + ДОБАВЕН АЛКОХОЛ)
# ==============================================================================
INGREDIENTS_DB = {
    # --- ТВОИТЕ Е600 СЕРИЯ ---
    "е621": {
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Невротоксин. Предизвиква пристрастяване, главоболие и уврежда нервните клетки.", "alts": ["sea_salt", "spices"]},
        "en": {"name": "E621 (MSG)", "effect": "Neurotoxin. Causes addiction, headaches and damages nerve cells.", "alts": ["sea_salt", "spices"]}
    },
    "е622": {
        "severity": "high",
        "bg": {"name": "Е622 (Монокалиев глутамат)", "effect": "Може да причини гадене и сърцебиене.", "alts": ["spices"]},
        "en": {"name": "E622 (Monopotassium Glutamate)", "effect": "May cause nausea and heart palpitations.", "alts": ["spices"]}
    },
    "е627": {
        "severity": "high",
        "bg": {"name": "Е627 (Динатриев гуанилат)", "effect": "Опасен за хора с подагра. Маскира лошото качество на храната.", "alts": ["yeast_free"]},
        "en": {"name": "E627 (Disodium Guanylate)", "effect": "Dangerous for gout. Masks low food quality.", "alts": ["yeast_free"]}
    },
    "е631": {
        "severity": "high",
        "bg": {"name": "Е631 (Динатриев инозинат)", "effect": "Изкуствен подобрител, често комбиниран с Е621.", "alts": ["yeast_free"]},
        "en": {"name": "E631 (Disodium Inosinate)", "effect": "Artificial enhancer, often combined with MSG.", "alts": ["yeast_free"]}
    },
    "е635": {
        "severity": "high",
        "bg": {"name": "Е635 (Динатриев 5-рибонуклеотид)", "effect": "Може да доведе до сериозни кожни обриви.", "alts": ["spices"]},
        "en": {"name": "E635 (Disodium 5'-ribonucleotides)", "effect": "May lead to serious skin rashes.", "alts": ["spices"]}
    },
    "глутамат": {
        "severity": "high",
        "bg": {"name": "Глутамати", "effect": "Възбуждат мозъка изкуствено и пречат на засищането.", "alts": ["sea_salt"]},
        "en": {"name": "Glutamates", "effect": "Artificially excites the brain and prevents satiety.", "alts": ["sea_salt"]}
    },

    # --- ТВОИТЕ Е400 СЕРИЯ ---
    "е450": {
        "severity": "high",
        "bg": {"name": "Е450 (Дифосфати)", "effect": "Извличат калция от костите. Водят до остеопороза.", "alts": ["labne", "cottage"]},
        "en": {"name": "E450 (Diphosphates)", "effect": "Leeches calcium from bones. Leads to osteoporosis.", "alts": ["labne", "cottage"]}
    },
    "е451": {
        "severity": "high",
        "bg": {"name": "Е451 (Трифосфати)", "effect": "Химически соли, натоварващи бъбреците и метаболизма.", "alts": ["labne", "cottage"]},
        "en": {"name": "E451 (Triphosphates)", "effect": "Chemical salts straining kidneys and metabolism.", "alts": ["labne", "cottage"]}
    },
    "е452": {
        "severity": "high",
        "bg": {"name": "Е452 (Полифосфати)", "effect": "Пречат на усвояването на минерали. Вредят на сърцето.", "alts": ["labne"]},
        "en": {"name": "E452 (Polyphosphates)", "effect": "Interferes with mineral absorption. Harms the heart.", "alts": ["labne"]}
    },
    "е407": {
        "severity": "medium",
        "bg": {"name": "Е407 (Карагенан)", "effect": "Използва се за гъстота. Може да причини язви и възпаления.", "alts": ["natural_yogurt"]},
        "en": {"name": "E407 (Carrageenan)", "effect": "Used for thickening. May cause ulcers and inflammation.", "alts": ["natural_yogurt"]}
    },
    "е412": {
        "severity": "low",
        "bg": {"name": "Е412 (Гума гуар)", "effect": "Стабилизатор. При големи количества действа слабително.", "alts": []},
        "en": {"name": "E412 (Guar Gum)", "effect": "Stabilizer. Laxative effect in large amounts.", "alts": []}
    },
    "е471": {
        "severity": "medium",
        "bg": {"name": "Е471 (Моно- и диглицериди)", "effect": "Емулгатор. Може да съдържа трансмазнини и да пречи на метаболизма.", "alts": ["butter"]},
        "en": {"name": "E471 (Mono- and diglycerides)", "effect": "Emulsifier. May contain trans fats and disrupt metabolism.", "alts": ["butter"]}
    },
    "е472": {
        "severity": "medium",
        "bg": {"name": "Е472 (Естери на моно- и диглицериди)", "effect": "Синтетични мазнини. Могат да причинят храносмилателни проблеми.", "alts": ["butter"]},
        "en": {"name": "E472 (Esters of mono- and diglycerides)", "effect": "Synthetic fats. Can cause digestive issues.", "alts": ["butter"]}
    },
    # --- ТВОИТЕ Е200 СЕРИЯ ---
    "е250": {
        "severity": "high",
        "bg": {"name": "Е250 (Натриев нитрит)", "effect": "Силно канцерогенен. Може да образува нитрозамини в стомаха.", "alts": ["fresh_meat"]},
        "en": {"name": "E250 (Sodium Nitrite)", "effect": "Highly carcinogenic. Can form nitrosamines in the stomach.", "alts": ["fresh_meat"]}
    },
    "е251": {
        "severity": "high",
        "bg": {"name": "Е251 (Натриев нитрат)", "effect": "Използва се за консервиране. Опасен при загряване.", "alts": ["fresh_meat"]},
        "en": {"name": "E251 (Sodium Nitrate)", "effect": "Preservative. Dangerous when heated.", "alts": ["fresh_meat"]}
    },
    "е249": {
        "severity": "high",
        "bg": {"name": "Е249 (Калиев нитрит)", "effect": "Токсичен за кръвта. Намалява кислорода в клетките.", "alts": ["fresh_meat"]},
        "en": {"name": "E249 (Potassium Nitrite)", "effect": "Toxic to blood. Reduces cell oxygen.", "alts": ["fresh_meat"]}
    },
    "е211": {
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Причинява алергии и уврежда клетъчните митохондрии.", "alts": ["homemade_juice"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Causes allergies and damages mitochondria.", "alts": ["homemade_juice"]}
    },
    "нитрит": {
        "severity": "high",
        "bg": {"name": "Нитрити", "effect": "Опасни консерванти в месни продукти.", "alts": ["fresh_meat"]},
        "en": {"name": "Nitrites", "effect": "Dangerous preservatives in meat products.", "alts": ["fresh_meat"]}
    },
    "нитрат": {
        "severity": "high",
        "bg": {"name": "Нитрати", "effect": "Токсични вещества, често превишени в зеленчуци и меса.", "alts": ["fresh_meat"]},
        "en": {"name": "Nitrates", "effect": "Toxic substances often high in vegetables and meats.", "alts": ["fresh_meat"]}
    },

    # --- ТВОИТЕ ПОДСЛАДИТЕЛИ ---
    "аспартам": {
        "severity": "high", 
        "bg": {"name": "Аспартам (E951)", "effect": "Изкуствен подсладител. Потенциален риск за мозъка.", "alts": ["stevia", "erythritol"]},
        "en": {"name": "Aspartame (E951)", "effect": "Artificial sweetener. Potential brain risk.", "alts": ["stevia", "erythritol"]}
    },
    "е951": {
        "severity": "high", 
        "bg": {"name": "Е951", "effect": "Аспартам. Опасен химикал в 'диетични' напитки.", "alts": ["stevia"]},
        "en": {"name": "E951", "effect": "Aspartame. Dangerous chemical in diet drinks.", "alts": ["stevia"]}
    },
    "е950": {
        "severity": "high", 
        "bg": {"name": "Е950 (Ацесулфам К)", "effect": "Изкуствен химикал, по-сладък от захарта 200 пъти.", "alts": ["erythritol"]},
        "en": {"name": "E950 (Acesulfame K)", "effect": "Artificial chemical 200x sweeter than sugar.", "alts": ["erythritol"]}
    },
    "глюкоз": {
        "severity": "high", 
        "bg": {"name": "Глюкозно-фруктозен сироп", "effect": "Води до мастен черен дроб и бързо затлъстяване.", "alts": ["honey"]},
        "en": {"name": "HFCS", "effect": "Leads to fatty liver and rapid obesity.", "alts": ["honey"]}
    },
    "захар": {
        "severity": "medium", 
        "bg": {"name": "Захар", "effect": "Празни калории, руши зъбите и имунитета.", "alts": ["stevia", "honey"]},
        "en": {"name": "Sugar", "effect": "Empty calories, harms teeth and immunity.", "alts": ["stevia", "honey"]}
    },

    # --- ТВОИТЕ МАЗНИНИ ---
    "палмов": {
        "severity": "high", 
        "bg": {"name": "Палмова мазнина", "effect": "Наситени мазнини, които запушват артериите.", "alts": ["butter", "olive_oil"]},
        "en": {"name": "Palm Oil", "effect": "Saturated fats that clog arteries.", "alts": ["butter", "olive_oil"]}
    },
    "хидрогени": {
        "severity": "high", 
        "bg": {"name": "Хидрогенирани мазнини", "effect": "Трансмазнини. Основна причина за сърдечни заболявания.", "alts": ["olive_oil"]},
        "en": {"name": "Hydrogenated Fats", "effect": "Trans fats. Leading cause of heart disease.", "alts": ["olive_oil"]}
    },
    "рафиниран": {
        "severity": "medium", 
        "bg": {"name": "Рафинирани масла", "effect": "Извлечени чрез химикали. Предизвикват възпаления.", "alts": ["extra_virgin"]},
        "en": {"name": "Refined Oils", "effect": "Chemically extracted. Cause inflammation.", "alts": ["extra_virgin"]}
    },

    # --- ТВОИТЕ ОЦВЕТИТЕЛИ ---
    "е102": {
        "severity": "high", 
        "bg": {"name": "Е102 (Тартразин)", "effect": "Жълт оцветител. Предизвиква астма и копривна треска.", "alts": ["natural_colors"]},
        "en": {"name": "E102 (Tartrazine)", "effect": "Yellow dye. Causes asthma and hives.", "alts": ["natural_colors"]}
    },
    "е133": {
        "severity": "high", 
        "bg": {"name": "Е133 (Брилянтно синьо)", "effect": "Синтетична боя. Може да дразни храносмилането.", "alts": ["natural_colors"]},
        "en": {"name": "E133 (Brilliant Blue)", "effect": "Synthetic dye. May irritate digestion.", "alts": ["natural_colors"]}
    },
    "е120": {
        "severity": "medium", 
        "bg": {"name": "Е120 (Кармин)", "effect": "Оцветител от насекоми. Силно алергизиращ.", "alts": ["natural_colors"]},
        "en": {"name": "E120 (Carmine)", "effect": "Insect-derived dye. Highly allergenic.", "alts": ["natural_colors"]}
    },

    # --- ТВОИТЕ ЗЪРНЕНИ ---
    "ечеми": {
        "severity": "medium", 
        "bg": {"name": "Ечемик / Малц (Глутен)", "effect": "Алерген за много хора. Висок гликемичен индекс.", "alts": ["water", "kombucha"]},
        "en": {"name": "Barley/Malt", "effect": "Allergen for many. High glycemic index.", "alts": ["water", "kombucha"]}
    },
    "малц": {
        "severity": "medium", 
        "bg": {"name": "Малц", "effect": "Обработено зърно с бързи захари.", "alts": ["tea"]},
        "en": {"name": "Malt", "effect": "Processed grain with fast sugars.", "alts": ["tea"]}
    },
    "хмел": {
        "severity": "low", 
        "bg": {"name": "Хмел", "effect": "Може да промени хормоналния баланс при мъжете.", "alts": []},
        "en": {"name": "Hops", "effect": "May affect hormonal balance in men.", "alts": []}
    },
    "грис": {
        "severity": "medium", 
        "bg": {"name": "Царевичен грис", "effect": "Рафиниран пълнител, често ГМО.", "alts": ["pure_malt_beer"]},
        "en": {"name": "Corn Grits", "effect": "Refined filler, often GMO.", "alts": ["pure_malt_beer"]}
    },

    # --- ДОБАВЕНА АЛКОХОЛНА ЧАСТ ---
    "алкохол": {
        "severity": "high", 
        "bg": {"name": "Алкохол", "effect": "Токсичен за черния дроб и нервната система.", "alts": ["water"]},
        "en": {"name": "Alcohol", "effect": "Toxic to the liver and nervous system.", "alts": ["water"]}
    },
    "вино": {
        "severity": "medium",
        "bg": {"name": "Вино", "effect": "Съдържа етанол и сулфити. Риск от дехидратация.", "alts": ["water", "kombucha"]},
        "en": {"name": "Wine", "effect": "Contains ethanol and sulfites. Dehydration risk.", "alts": ["water", "kombucha"]}
    },
    "бира": {
        "severity": "medium",
        "bg": {"name": "Бира", "effect": "Алкохолна напитка, причиняваща подуване и гликемичен скок.", "alts": ["water"]},
        "en": {"name": "Beer", "effect": "Alcoholic drink, causes bloating and blood sugar spikes.", "alts": ["water"]}
    },
    "уиски": {
        "severity": "high",
        "bg": {"name": "Уиски", "effect": "Висока концентрация на алкохол. Натоварва сърцето и черния дроб.", "alts": ["water"]},
        "en": {"name": "Whisky", "effect": "High alcohol concentration. Strains heart and liver.", "alts": ["water"]}
    },
    "водка": {
        "severity": "high",
        "bg": {"name": "Водка", "effect": "Концентриран етилов спирт. Силно токсичен при злоупотреба.", "alts": ["water"]},
        "en": {"name": "Vodka", "effect": "Concentrated ethyl alcohol. Highly toxic in excess.", "alts": ["water"]}
    },
    "ракия": {
        "severity": "high",
        "bg": {"name": "Ракия", "effect": "Силна алкохолна напитка, бързо дехидратира тялото.", "alts": ["water"]},
        "en": {"name": "Rakia", "effect": "Strong alcoholic drink, rapidly dehydrates the body.", "alts": ["water"]}
    }
}

# ==============================================================================
# 2. ТВОЯТА БИБЛИОТЕКА ЗА ЗАМЕСТИТЕЛИ (С ДОБАВЕН EN)
# ==============================================================================
ALTS_LIB = {
    "labne": {
        "bg": {"name": "Лабне (Цедено мляко)", "desc": "Естествен продукт, получен чрез изцеждане на кисело мляко. Гъсто, маслено и без никакви фосфати или химия."},
        "en": {"name": "Labneh", "desc": "Natural strained yogurt product. Thick and chemical-free."}
    },
    "cottage": {
        "bg": {"name": "Котидж сирене", "desc": "Сирене на малки зърна, богато на протеин (казеин). Идеално за диети, без добавени консерванти."},
        "en": {"name": "Cottage Cheese", "desc": "High-protein curd cheese. Preservative-free and diet-friendly."}
    },
    "fresh_meat": {
        "bg": {"name": "Прясно месо", "desc": "Най-безопасният избор. Опечете месо у дома вместо да купувате колбаси с нитрити."},
        "en": {"name": "Fresh Meat", "desc": "The safest choice. Roast meat at home to avoid nitrites."}
    },
    "stevia": {
        "bg": {"name": "Стевия", "desc": "Растение, което е многократно по-сладко от захарта, но не съдържа калории и не храни бактериите в устата."},
        "en": {"name": "Stevia", "desc": "Natural zero-calorie plant sweetener."}
    },
    "erythritol": {
        "bg": {"name": "Еритритол", "desc": "Естествен подсладител, който се среща в плодовете. Има 0 калории и не причинява подуване."},
        "en": {"name": "Erythritol", "desc": "Natural sugar alcohol found in fruits. Zero calories."}
    },
    "honey": {
        "bg": {"name": "Натурален мед", "desc": "Пълен с витамини и ензими, но съдържа захар, така че консумирайте с мярка."},
        "en": {"name": "Natural Honey", "desc": "Packed with vitamins, but use in moderation due to sugar."}
    },
    "olive_oil": {
        "bg": {"name": "Зехтин Екстра Върджин", "desc": "Студено пресована мазнина от маслини. Лекува съдовете и сърцето."},
        "en": {"name": "Extra Virgin Olive Oil", "desc": "Cold-pressed oil. Good for heart and vessels."}
    },
    "butter": {
        "bg": {"name": "Краве масло (82% масленост)", "desc": "Чист животински продукт. Съдържа витамини A, E и K2. Далеч по-добре от маргарин."},
        "en": {"name": "Butter (82%)", "desc": "Pure animal product with vitamins. Better than margarine."}
    },
    "sea_salt": {
        "bg": {"name": "Морска сол", "desc": "Нерафинирана сол, която съдържа йод, магнезий и други минерали от морето."},
        "en": {"name": "Sea Salt", "desc": "Unrefined salt containing natural minerals."}
    },
    "spices": {
        "bg": {"name": "Чисти подправки", "desc": "Босилек, мащерка, черен пипер. Придават вкус без да увреждат нервните клетки."},
        "en": {"name": "Pure Spices", "desc": "Natural herbs and peppers for flavor without MSG."}
    },
    "kombucha": {
        "bg": {"name": "Комбуча", "desc": "Жива напитка, получена от ферментация на чай. Пълна с пробиотици за здрави черва."},
        "en": {"name": "Kombucha", "desc": "Probiotic fermented tea drink."}
    },
    "pure_malt_beer": {
        "bg": {"name": "Бира '100% малц'", "desc": "Бира, произведена по традиционна рецепта без добавен царевичен грис или ориз."},
        "en": {"name": "100% Malt Beer", "desc": "Traditional beer without corn grits or rice fillers."}
    },
    "yeast_free": {
        "bg": {"name": "Продукти без дрожди", "desc": "Храни, които не съдържат екстракт от дрожди (често използван параван за глутамат)."},
        "en": {"name": "Yeast-Free Products", "desc": "Foods without yeast extract (often a hidden MSG source)."}
    },
    "natural_yogurt": {
        "bg": {"name": "Чисто кисело мляко", "desc": "Търсете такова по БДС стандарта – само мляко и закваска."},
        "en": {"name": "Pure Yogurt", "desc": "Look for products with only milk and cultures."}
    },
    "homemade_juice": {
        "bg": {"name": "Домашен сок/смути", "desc": "Изцеден плод у дома. Без бензоати и без изкуствени бои."},
        "en": {"name": "Homemade Juice", "desc": "Freshly squeezed at home. No benzoates or dyes."}
    },
    "extra_virgin": {
        "bg": {"name": "Студено пресовани масла", "desc": "Масла, извлечени механично, без нагряване и хексан (химикал)."},
        "en": {"name": "Cold-pressed Oils", "desc": "Mechanically extracted oils without chemicals."}
    },
    "natural_colors": {
        "bg": {"name": "Натурални оцветители", "desc": "Екстракти от цвекло, бета-каротин или грозде вместо синтетични Е-номера."},
        "en": {"name": "Natural Colors", "desc": "Beet, carrot or grape extracts instead of E-numbers."}
    },
    "tea": {
        "bg": {"name": "Билков чай", "desc": "Натурална напитка, богата на антиоксиданти. Без добавени подсладители."},
        "en": {"name": "Herbal Tea", "desc": "Antioxidant-rich drink without sweeteners."}
    },
    "water": {
        "bg": {"name": "Минерална вода", "desc": "Най-добрата хидратация без никаква химия."},
        "en": {"name": "Mineral Water", "desc": "Best hydration without any chemicals."}
    }
}

# ==============================================================================
# 3. ИНТЕРФЕЙС И ЛОГИКА
# ==============================================================================
UI_TEXTS = {
    "bg": {
        "title": "🛡️ Експертен Анализатор на Храни",
        "desc": "Сканирайте продукт и приложението ще ви каже дали се съдържат вещества като: Е-номера, мазнини, захари и алкохоли.",
        "found": "🛑 Открихме рискови елемента!",
        "harm_sub": "⚠️ Анализ на вредните вещества:",
        "alt_sub": "🥗 Препоръчани заместители:",
        "alt_click": "*(Кликни върху името за подробна информация)*",
        "clean": "✅ Продуктът изглежда чист според нашия пълен списък!"
    },
    "en": {
        "title": "🛡️ Expert Food Scanner",
        "desc": "Scan a product and find out if it contains: E-numbers, fats, sugars, and alcohols.",
        "found": "🛑 Found risky elements!",
        "harm_sub": "⚠️ Substance Analysis:",
        "alt_sub": "🥗 Recommended Alternatives:",
        "alt_click": "*(Click name for details)*",
        "clean": "✅ Product looks clean according to our list!"
    }
}

st.title(UI_TEXTS[lang]["title"])
st.write(UI_TEXTS[lang]["desc"])

# Опции за качване
tab1, tab2 = st.tabs(["📁 Галерия", "📷 Камера на момента"])
img_data = None

with tab1:
    f = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
    if f: img_data = f
with tab2:
    c = st.camera_input("Scan Label")
    if c: img_data = c

def get_text(img_bytes, target_lang):
    try:
        api_lang = "bul" if target_lang == "bg" else "eng"
        payload = {'apikey': 'helloworld', 'language': api_lang, 'scale': True, 'isTable': True}
        files = {'filename': ('label.jpg', img_bytes, 'image/jpeg')}
        res = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
        return res.json()["ParsedResults"][0]["ParsedText"]
    except: return ""

if img_data:
    st.image(img_data, width=350)
    with st.spinner("Analyzing..."):
        text_raw = get_text(img_data.getvalue(), lang).lower()
        text_clean = re.sub(r'[^а-я0-9a-z\s]', ' ', text_raw)
        
        found = []
        for key, info in INGREDIENTS_DB.items():
            if key in text_clean:
                if info[lang]["name"] not in [i[lang]["name"] for i in found]:
                    found.append(info)

        st.divider()
        if found:
            st.error(f"{UI_TEXTS[lang]['found']} ({len(found)})")
            
            left, right = st.columns(2)
            
            with left:
                st.subheader(UI_TEXTS[lang]["harm_sub"])
                for item in found:
                    with st.expander(f"📌 {item[lang]['name']}"):
                        st.write(f"**Risk/Риск:** {item[lang]['effect']}")
            
            with right:
                st.subheader(UI_TEXTS[lang]["alt_sub"])
                st.write(UI_TEXTS[lang]["alt_click"])
                alts_to_show = set()
                for item in found:
                    for a_id in item[lang]['alts']:
                        alts_to_show.add(a_id)
                
                for a_id in alts_to_show:
                    data = ALTS_LIB.get(a_id)
                    if data:
                        with st.status(f"✅ {data[lang]['name']}", expanded=False):
                            st.info(data[lang]['desc'])
        else:
            st.success(UI_TEXTS[lang]["clean"])
