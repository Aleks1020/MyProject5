import cv2
import easyocr
import re

# 1. Локализация на съобщенията в приложението (Интерфейс)
MESSAGES = {
    "bg": {
        "loading": "Зареждане на OCR моделите... Моля, изчакайте...",
        "ready": "\n--- Скенерът за етикети е готов! ---",
        "instructions": "Инструкции:\n1. Насочете камерата към етикета на продукта.\n2. Натиснете 'S' за СКАНИРАНЕ.\n3. Натиснете 'Q' за ИЗЛЕЗЕТЕ от приложението.",
        "overlay": "Натиснете 'S' за сканиране | 'Q' за изход",
        "scanning": "\n Сканиране... Моля, задръжте неподвижно...",
        "read_text": "Прочетен текст от етикета:",
        "results_title": " РЕЗУЛТАТИ ОТ СКАНЕРА:",
        "clean_product": " СТАТУС: ПОЛЕЗЕН / ЧИСТ ПРОДУКТ\nНе бяха открити критични вредни вещества от базата данни.",
        "harmful": "ВРЕДЕН ПРОДУКТ (Избягвайте или консумирайте рядко!)",
        "medium": "СРЕДНО ПОЛЕЗЕН (Консумирайте с повишено внимание)",
        "status": "СТАТУС:",
        "detected_ingredients": "Открити съставки и техните ефекти върху тялото:",
        "alternatives": "\n ЗДРАВОСЛОВНИ ЗАМЕСТИТЕЛИ:",
        "closing": "Затваряне на приложението..."
    },
    "en": {
        "loading": "Loading OCR models... Please wait...",
        "ready": "\n--- Label Scanner is Ready! ---",
        "instructions": "Instructions:\n1. Point the camera at the product label.\n2. Press 'S' to SCAN.\n3. Press 'Q' to EXIT the application.",
        "overlay": "Press 'S' to scan | 'Q' to exit",
        "scanning": "\n Scanning... Please hold still...",
        "read_text": "Read text from label:",
        "results_title": " SCANNER RESULTS:",
        "clean_product": " STATUS: HEALTHY / CLEAN PRODUCT\nNo critical harmful substances were found in the database.",
        "harmful": "HARMFUL PRODUCT (Avoid or consume rarely!)",
        "medium": "MODERATELY HEALTHY (Consume with caution)",
        "status": "STATUS:",
        "detected_ingredients": "Detected ingredients and their effects on the body:",
        "alternatives": "\n HEALTHY ALTERNATIVES:",
        "closing": "Closing the application..."
    }
}

# 2. Двуезична база данни за вредните съставки
# Ключовете включват думи на български и английски. Резултатите се адаптират според избрания език.
INGREDIENTS_DB = {
    # Захари / Sugars
    "захар": {
        "severity": "medium",
        "bg": {"name": "Захар", "effect": "Риск от затлъстяване, диабет и кариеси.", "alternatives": ["Стевия", "Еритритол", "Мед"]},
        "en": {"name": "Sugar", "effect": "Risk of obesity, diabetes, and tooth decay.", "alternatives": ["Stevia", "Erythritol", "Honey"]}
    },
    "sugar": {
        "severity": "medium",
        "bg": {"name": "Захар", "effect": "Риск от затлъстяване, диабет и кариеси.", "alternatives": ["Стевия", "Еритритол", "Мед"]},
        "en": {"name": "Sugar", "effect": "Risk of obesity, diabetes, and tooth decay.", "alternatives": ["Stevia", "Erythritol", "Honey"]}
    },
    "глюкоз": {
        "severity": "high",
        "bg": {"name": "Глюкозно-фруктозен сироп", "effect": "Рязко вдига кръвната захар, натоварва черния дроб.", "alternatives": ["Натурален плодов сок", "Вода"]},
        "en": {"name": "Glucose-Fructose Syrup", "effect": "Spikes blood sugar levels, strains the liver.", "alternatives": ["Natural fruit juice", "Water"]}
    },
    "glucose": {
        "severity": "high",
        "bg": {"name": "Глюкозно-фруктозен сироп", "effect": "Рязко вдига кръвната захар, натоварва черния дроб.", "alternatives": ["Натурален плодов сок", "Вода"]},
        "en": {"name": "Glucose-Fructose Syrup", "effect": "Spikes blood sugar levels, strains the liver.", "alternatives": ["Natural fruit juice", "Water"]}
    },
    "малц": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Висок гликемичен индекс, съдържа глутен.", "alternatives": ["Продукти без глутен"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "High glycemic index, contains gluten.", "alternatives": ["Gluten-free alternatives"]}
    },
    "malt": {
        "severity": "medium",
        "bg": {"name": "Ечемичен малц / Малтодекстрин", "effect": "Висок гликемичен индекс, съдържа глутен.", "alternatives": ["Продукти без глутен"]},
        "en": {"name": "Barley Malt / Maltodextrin", "effect": "High glycemic index, contains gluten.", "alternatives": ["Gluten-free alternatives"]}
    },
    
    # Алкохол / Alcohol
    "алкохол": {
        "severity": "high",
        "bg": {"name": "Алкохол (Етанол)", "effect": "Токсичен за черния дроб и нервната система. Дехидратира.", "alternatives": ["Безалкохолни напитки", "Вода"]},
        "en": {"name": "Alcohol (Ethanol)", "effect": "Toxic to the liver and nervous system. Dehydrates.", "alternatives": ["Non-alcoholic drinks", "Water"]}
    },
    "alcohol": {
        "severity": "high",
        "bg": {"name": "Алкохол (Етанол)", "effect": "Токсичен за черния дроб и нервната система. Дехидратира.", "alternatives": ["Безалкохолни напитки", "Вода"]},
        "en": {"name": "Alcohol (Ethanol)", "effect": "Toxic to the liver and nervous system. Dehydrates.", "alternatives": ["Non-alcoholic drinks", "Water"]}
    },
    
    # Мазнини / Fats
    "палмово": {
        "severity": "high",
        "bg": {"name": "Палмово масло", "effect": "Повишава лошия холестерол (LDL) и риска от сърдечни проблеми.", "alternatives": ["Зехтин", "Кокосово масло"]},
        "en": {"name": "Palm Oil", "effect": "Increases bad cholesterol (LDL) and cardiovascular risks.", "alternatives": ["Olive oil", "Coconut oil"]}
    },
    "palm oil": {
        "severity": "high",
        "bg": {"name": "Палмово масло", "effect": "Повишава лошия холестерол (LDL) и риска от сърдечни проблеми.", "alternatives": ["Зехтин", "Кокосово масло"]},
        "en": {"name": "Palm Oil", "effect": "Increases bad cholesterol (LDL) and cardiovascular risks.", "alternatives": ["Olive oil", "Coconut oil"]}
    },
    
    # Изкуствени добавки (Е-та) / E-numbers
    "e211": {
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Потенциален алерген, уврежда клетките при реакция с Витамин Ц.", "alternatives": ["Продукти без консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Potential allergen, may damage DNA when mixed with Vitamin C.", "alternatives": ["Preservative-free alternatives"]}
    },
    "е211": { # вариант на кирилица 'е'
        "severity": "high",
        "bg": {"name": "Е211 (Натриев бензоат)", "effect": "Потенциален алерген, уврежда клетките.", "alternatives": ["Продукти без консерванти"]},
        "en": {"name": "E211 (Sodium Benzoate)", "effect": "Potential allergen, may damage DNA.", "alternatives": ["Preservative-free alternatives"]}
    },
    "e621": {
        "severity": "high",
        "bg": {"name": "Е621 (Мононатриев глутамат)", "effect": "Предизвиква пристрастяване към вкуса, главоболие.", "alternatives": ["Естествени подправки (сол, билки)"]},
        "en": {"name": "E621 (Monosodium Glutamate / MSG)", "effect": "Appetite stimulant, can cause headaches or flushing.", "alternatives": ["Natural spices, herbs"]}
    }
}

def analyze_text(text, lang):
    """Анализира извлечения текст и показва резултатите на избрания език."""
    text_lower = text.lower()
    found_ingredients = []
    
    high_risk_count = 0
    medium_risk_count = 0
    
    msg = MESSAGES[lang]
    
    # Сканиране за съвпадения
    for key, info in INGREDIENTS_DB.items():
        if re.search(key, text_lower):
            # Избягване на дублиране на една и съща съставка, ако е намерена и на двата езика
            if info[lang]["name"] not in [i["name"] for i in found_ingredients]:
                found_ingredients.append(info[lang])
                if info["severity"] == "high":
                    high_risk_count += 1
                elif info["severity"] == "medium":
                    medium_risk_count += 1
                
    print("\n" + "="*50)
    print(msg["results_title"])
    print("="*50)
    
    if not found_ingredients:
        print(msg["clean_product"])
        print("="*50 + "\n")
        return

    # Оценка на риска
    if high_risk_count >= 1 or medium_risk_count >= 3:
        status_text = msg["harmful"]
        show_alternatives = True
    elif medium_risk_count > 0:
        status_text = msg["medium"]
        show_alternatives = False
    else:
        status_text = "OK"
        show_alternatives = False

    print(f"{msg['status']} {status_text}\n")
    print(msg["detected_ingredients"])
    
    all_alternatives = set()
    
    for ing in found_ingredients:
        print(f" • {ing['name']} -> {ing['effect']}")
        if show_alternatives:
            for alt in ing["alternatives"]:
                all_alternatives.add(alt)
                
    if show_alternatives and all_alternatives:
        print(msg["alternatives"])
        for alt in all_alternatives:
            print(f" -> {alt}")
            
    print("="*50 + "\n")

def main():
    # Избор на език при стартиране на приложението
    print("Изберете език на приложението / Choose application language:")
    print("1 - Български (BG)")
    print("2 - English (EN)")
    choice = input("Избор / Choice (1/2): ").strip()
    
    lang = "en" if choice == "2" else "bg"
    msg = MESSAGES[lang]
    
    print(msg["loading"])
    # Инициализиране на EasyOCR (пази и двата езика активни за сканиране!)
    reader = easyocr.Reader(['bg', 'en'], gpu=False)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Camera could not be opened." if lang == "en" else "Грешка: Камерата не може да се отвори.")
        return

    print(msg["ready"])
    print(msg["instructions"])
    
    while True:
        ret, frame = cap.get()
        if not ret:
            break
            
        # Поставяне на текст върху видеото в реално време
        cv2.putText(frame, msg["overlay"], (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("Smart Label Scanner", frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # 'S' за сканиране (хваща латиница и кирилица от клавиатурата)
        if key in [ord('s'), ord('S'), ord('я'), ord('Я')]:
            print(msg["scanning"])
            
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            results = reader.readtext(gray_frame, detail=0)
            full_text = " ".join(results)
            
            print(f"\n{msg['read_text']} \n\"{full_text}\"")
            analyze_text(full_text, lang)
            
        # 'Q' за изход
        elif key in [ord('q'), ord('Q'), ord('й'), ord('Й')]:
            print(msg["closing"])
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
