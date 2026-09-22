import re
from typing import Dict, Any, List

# Numbers in Uzbek text
UZ_NUMS = {
    "bir": 1, "bitta": 1, "yarim": 0.5, "yarimta": 0.5, "chorak": 0.25,
    "ikki": 2, "ikkita": 2, "uch": 3, "uchta": 3,
    "to'rt": 4, "tort": 4, "to'rtta": 4, "tortta": 4,
    "besh": 5, "beshta": 5, "olti": 6, "oltita": 6,
    "yetti": 7, "yettita": 7, "sakkiz": 8, "sakkizta": 8,
    "to'qqiz": 9, "toqqiz": 9, "to'qqizta": 9,
    "o'n": 10, "on": 10, "o'nta": 10
}

# Extensive Food Knowledge Base
# Default serving: unit_g (grams per serving or unit)
# Macros per 100g: kcal, p, c, f
FOOD_KNOWLEDGE = [
    # Multi-word items first!
    {
        "names": ["qovurma lag'mon", "qovurma lagmon"],
        "display": "Qovurma lag'mon",
        "kcal_100": 180, "p_100": 6.5, "c_100": 21.0, "f_100": 7.5,
        "portion_g": 350, "default_unit": "porsiya"
    },
    {
        "names": ["cho'zma lag'mon", "chuzma lagmon", "lag'mon", "lagmon"],
        "display": "Lag'mon",
        "kcal_100": 145, "p_100": 5.5, "c_100": 16.5, "f_100": 6.5,
        "portion_g": 400, "default_unit": "kosa"
    },
    {
        "names": ["qozon kabob", "qozon-kabob", "qozonkabob"],
        "display": "Qozon kabob",
        "kcal_100": 210, "p_100": 13.0, "c_100": 8.0, "f_100": 14.0,
        "portion_g": 350, "default_unit": "porsiya"
    },
    {
        "names": ["tovuq filesi", "tovuq file", "tovuq ko'kragi", "tovuq kokragi", "tovuq go'shti", "tovuq"],
        "display": "Tovuq go'shti (file)",
        "kcal_100": 165, "p_100": 31.0, "c_100": 0.0, "f_100": 3.6,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["tandir somsa", "go'shtli somsa", "somsa", "samsa"],
        "display": "Go'shtli somsa",
        "kcal_100": 240, "p_100": 9.2, "c_100": 23.5, "f_100": 12.5,
        "unit_g": 120, "is_unit": True, "unit_kcal": 290, "unit_p": 11.0, "unit_c": 28.0, "unit_f": 15.0
    },
    {
        "names": ["qovoqli somsa", "qovoq somsa"],
        "display": "Qovoqli somsa",
        "kcal_100": 160, "p_100": 3.5, "c_100": 23.5, "f_100": 6.0,
        "unit_g": 120, "is_unit": True, "unit_kcal": 190, "unit_p": 4.0, "unit_c": 28.0, "unit_f": 7.0
    },
    {
        "names": ["to'y oshi", "choyxona oshi", "osh", "palov"],
        "display": "Osh (Palov)",
        "kcal_100": 210, "p_100": 6.0, "c_100": 26.0, "f_100": 9.5,
        "portion_g": 350, "default_unit": "likopcha"
    },
    {
        "names": ["manti"],
        "display": "Manti",
        "kcal_100": 175, "p_100": 7.2, "c_100": 16.5, "f_100": 9.2,
        "unit_g": 90, "is_unit": True, "unit_kcal": 160, "unit_p": 6.5, "unit_c": 15.0, "unit_f": 8.5
    },
    {
        "names": ["sho'rva", "shurva", "sho'rba"],
        "display": "Sho'rva",
        "kcal_100": 90, "p_100": 6.0, "c_100": 4.5, "f_100": 5.5,
        "portion_g": 400, "default_unit": "kosa"
    },
    {
        "names": ["mastava"],
        "display": "Mastava",
        "kcal_100": 85, "p_100": 4.5, "c_100": 9.5, "f_100": 3.3,
        "portion_g": 400, "default_unit": "kosa"
    },
    {
        "names": ["chuchvara"],
        "display": "Chuchvara",
        "kcal_100": 130, "p_100": 5.8, "c_100": 15.0, "f_100": 5.2,
        "portion_g": 350, "default_unit": "kosa"
    },
    {
        "names": ["dimlama"],
        "display": "Dimlama",
        "kcal_100": 95, "p_100": 6.5, "c_100": 5.5, "f_100": 5.0,
        "portion_g": 400, "default_unit": "porsiya"
    },
    {
        "names": ["norin"],
        "display": "Norin",
        "kcal_100": 170, "p_100": 11.2, "c_100": 18.0, "f_100": 5.6,
        "portion_g": 250, "default_unit": "porsiya"
    },
    {
        "names": ["shashlik", "qiyma shashlik", "qo'y shashlik", "kabob"],
        "display": "Shashlik",
        "kcal_100": 220, "p_100": 19.0, "c_100": 1.0, "f_100": 16.0,
        "unit_g": 100, "is_unit": True, "unit_kcal": 220, "unit_p": 19.0, "unit_c": 1.0, "unit_f": 16.0
    },
    {
        "names": ["lavash", "doner", "shaurma"],
        "display": "Lavash",
        "kcal_100": 215, "p_100": 8.7, "c_100": 22.5, "f_100": 10.0,
        "unit_g": 300, "is_unit": True, "unit_kcal": 650, "unit_p": 26.0, "unit_c": 68.0, "unit_f": 30.0
    },
    {
        "names": ["burger", "gamburger", "chizburger"],
        "display": "Burger",
        "kcal_100": 240, "p_100": 11.0, "c_100": 21.0, "f_100": 12.0,
        "unit_g": 200, "is_unit": True, "unit_kcal": 480, "unit_p": 22.0, "unit_c": 42.0, "unit_f": 24.0
    },
    {
        "names": ["xot-dog", "hot-dog", "hotdog"],
        "display": "Xot-dog",
        "kcal_100": 225, "p_100": 8.0, "c_100": 21.5, "f_100": 12.0,
        "unit_g": 150, "is_unit": True, "unit_kcal": 340, "unit_p": 12.0, "unit_c": 32.0, "unit_f": 18.0
    },
    {
        "names": ["pizza", "pitsa"],
        "display": "Pitsa (bo'lak)",
        "kcal_100": 225, "p_100": 9.2, "c_100": 26.5, "f_100": 9.2,
        "unit_g": 120, "is_unit": True, "unit_kcal": 270, "unit_p": 11.0, "unit_c": 32.0, "unit_f": 11.0
    },
    {
        "names": ["kartoshka fri", "fri"],
        "display": "Kartoshka fri",
        "kcal_100": 300, "p_100": 3.4, "c_100": 40.0, "f_100": 14.5,
        "portion_g": 120, "default_unit": "porsiya"
    },
    {
        "names": ["tuxum", "omlet"],
        "display": "Tuxum",
        "kcal_100": 150, "p_100": 12.6, "c_100": 0.8, "f_100": 10.0,
        "unit_g": 55, "is_unit": True, "unit_kcal": 75, "unit_p": 6.5, "unit_c": 0.5, "unit_f": 5.0
    },
    {
        "names": ["grechka"],
        "display": "Grechka",
        "kcal_100": 115, "p_100": 4.5, "c_100": 23.0, "f_100": 1.3,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["guruch", "oq guruch"],
        "display": "Guruch",
        "kcal_100": 130, "p_100": 2.8, "c_100": 28.0, "f_100": 0.4,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["makaron", "pasta"],
        "display": "Makaron",
        "kcal_100": 140, "p_100": 5.0, "c_100": 28.0, "f_100": 1.0,
        "portion_g": 200, "default_unit": "gr"
    },
    {
        "names": ["ovsyanka", "suli", "suli bo'tqasi"],
        "display": "Ovsyanka (Suli)",
        "kcal_100": 110, "p_100": 4.0, "c_100": 19.0, "f_100": 2.5,
        "portion_g": 200, "default_unit": "kosa"
    },
    {
        "names": ["kartoshka pyure", "pyure"],
        "display": "Kartoshka pyure",
        "kcal_100": 90, "p_100": 2.0, "c_100": 16.0, "f_100": 2.5,
        "portion_g": 200, "default_unit": "gr"
    },
    {
        "names": ["mol go'shti", "mol goshti", "mol go'sht"],
        "display": "Mol go'shti",
        "kcal_100": 215, "p_100": 26.0, "c_100": 0.0, "f_100": 12.5,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["qo'y go'shti", "qoy goshti"],
        "display": "Qo'y go'shti",
        "kcal_100": 260, "p_100": 22.0, "c_100": 0.0, "f_100": 19.0,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["baliq", "baliq go'shti"],
        "display": "Baliq",
        "kcal_100": 135, "p_100": 22.0, "c_100": 0.0, "f_100": 5.0,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["tvorog"],
        "display": "Tvorog",
        "kcal_100": 115, "p_100": 18.0, "c_100": 3.0, "f_100": 3.0,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["protein", "gepate", "oqsil kokteyl"],
        "display": "Protein kokteyli",
        "kcal_100": 380, "p_100": 76.0, "c_100": 8.0, "f_100": 4.5,
        "unit_g": 35, "is_unit": True, "unit_kcal": 130, "unit_p": 25.0, "unit_c": 3.0, "unit_f": 1.5
    },
    {
        "names": ["tandir non", "patir", "non"],
        "display": "Non",
        "kcal_100": 250, "p_100": 8.0, "c_100": 50.0, "f_100": 1.5,
        "unit_g": 50, "is_unit": True, "unit_kcal": 125, "unit_p": 4.0, "unit_c": 25.0, "unit_f": 1.0
    },
    {
        "names": ["olma"],
        "display": "Olma",
        "kcal_100": 50, "p_100": 0.4, "c_100": 13.0, "f_100": 0.2,
        "unit_g": 160, "is_unit": True, "unit_kcal": 80, "unit_p": 0.5, "unit_c": 20.0, "unit_f": 0.3
    },
    {
        "names": ["banan"],
        "display": "Banan",
        "kcal_100": 90, "p_100": 1.2, "c_100": 23.0, "f_100": 0.3,
        "unit_g": 120, "is_unit": True, "unit_kcal": 110, "unit_p": 1.4, "unit_c": 28.0, "unit_f": 0.4
    },
    {
        "names": ["achchiq-chuchuk", "shakarob", "achchiq chuchuk", "salat"],
        "display": "Salat (Shakarob)",
        "kcal_100": 30, "p_100": 1.0, "c_100": 4.5, "f_100": 0.5,
        "portion_g": 150, "default_unit": "likopcha"
    },
    {
        "names": ["sut"],
        "display": "Sut",
        "kcal_100": 58, "p_100": 3.2, "c_100": 4.8, "f_100": 3.0,
        "portion_g": 250, "default_unit": "stakan"
    },
    {
        "names": ["qatiq", "kefir"],
        "display": "Qatiq",
        "kcal_100": 52, "p_100": 3.0, "c_100": 4.0, "f_100": 2.5,
        "portion_g": 250, "default_unit": "stakan"
    },
    {
        "names": ["ayron"],
        "display": "Ayron",
        "kcal_100": 36, "p_100": 2.0, "c_100": 2.5, "f_100": 1.8,
        "portion_g": 250, "default_unit": "stakan"
    },
    {
        "names": ["choy"],
        "display": "Choy",
        "kcal_100": 1, "p_100": 0.0, "c_100": 0.2, "f_100": 0.0,
        "portion_g": 200, "default_unit": "piyola"
    },
    {
        "names": ["kofe"],
        "display": "Kofe",
        "kcal_100": 10, "p_100": 0.5, "c_100": 1.5, "f_100": 0.2,
        "portion_g": 200, "default_unit": "finjon"
    },
    {
        "names": ["yong'oq", "yongoq", "bodom"],
        "display": "Yong'oq / Bodom",
        "kcal_100": 650, "p_100": 15.0, "c_100": 14.0, "f_100": 62.0,
        "portion_g": 30, "default_unit": "gr"
    }
]

def parse_food_test(user_text: str) -> Dict[str, Any]:
    text_lower = user_text.lower()
    
    # 1. Meal type
    meal_type = "Tushlik"
    if any(w in text_lower for w in ["nonushta", "ertalab", "tonggi"]):
        meal_type = "Nonushta"
    elif any(w in text_lower for w in ["tushlik", "kunduzi"]):
        meal_type = "Tushlik"
    elif any(w in text_lower for w in ["kechki", "kechqurun", "shom"]):
        meal_type = "Kechki ovqat"
    elif any(w in text_lower for w in ["gazak", "snack", "choy"]):
        meal_type = "Gazak"

    matched_ranges = []
    matched_items = []

    # Sort FOOD_KNOWLEDGE so longer phrases are evaluated first
    for item in FOOD_KNOWLEDGE:
        for name in sorted(item["names"], key=len, reverse=True):
            # Check if name is in text with word boundary
            pattern = rf'(?:\b|^){re.escape(name)}(?:\b|$)'
            m = re.search(pattern, text_lower)
            if m:
                start, end = m.span()
                # Check if this span overlaps with an already matched longer span
                overlap = any(s <= start < e or s < end <= e for s, e in matched_ranges)
                if not overlap:
                    matched_ranges.append((start, end))
                    matched_items.append((item, name, start, end))
                    break # Don't check other alias names for this item

    if not matched_items:
        return {
            "meal_type": meal_type,
            "food_name": user_text[:40],
            "calories": 350.0,
            "protein": 20.0,
            "carbs": 40.0,
            "fat": 12.0,
            "weight_grams": 250.0
        }

    total_kcal = 0.0
    total_p = 0.0
    total_c = 0.0
    total_f = 0.0
    total_grams = 0.0
    names_list = []

    for item, name, start, end in matched_items:
        names_list.append(item["display"])

        # Extract immediately preceding and following text
        pre = text_lower[max(0, start - 20):start].strip()
        post = text_lower[end:min(len(text_lower), end + 20)].strip()

        # 1. Check for Grams (e.g., 200gr, 150g, 100 gramm)
        gram_pre = re.search(r'(\d+)\s*(?:g|gr|gramm|gram)\s*$', pre)
        gram_post = re.search(r'^\s*(\d+)\s*(?:g|gr|gramm|gram)\b', post)
        gram_m = gram_pre or gram_post

        # 2. Check for Kilo (e.g., 1kg, 1.5 kilo)
        kg_pre = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilo)\s*$', pre)
        kg_post = re.search(r'^\s*(\d+(?:\.\d+)?)\s*(?:kg|kilo)\b', post)
        kg_m = kg_pre or kg_post

        # 3. Check for Bowl / Plate / Cup (kosa, likopcha, tarelka, porsiya, stakan)
        portion_pre = re.search(r'(\d+|bir|bitta|ikki|ikkita|uch|uchta|yarim|yarimta)?\s*(kosa|likopcha|tarelka|porsiya|pors|stakan)\s*$', pre)
        portion_post = re.search(r'^\s*(\d+|bir|bitta|ikki|ikkita|uch|uchta|yarim|yarimta)?\s*(kosa|likopcha|tarelka|porsiya|pors|stakan)\b', post)
        portion_m = portion_pre or portion_post

        # 4. Check for Units (dona, ta, bo'lak, siyx, tilim, or pure number)
        unit_pre = re.search(r'(\d+|bir|bitta|ikki|ikkita|uch|uchta|to\'rt|tort|to\'rtta|tortta|besh|beshta|yarim|yarimta|chorak)\s*(?:ta|dona|bo\'lak|bolak|siyx|tilim)?\s*$', pre)
        unit_post = re.search(r'^\s*(\d+|bir|bitta|ikki|ikkita|uch|uchta|to\'rt|tort|to\'rtta|tortta|besh|beshta|yarim|yarimta|chorak)\s*(?:ta|dona|bo\'lak|bolak|siyx|tilim)\b', post)
        unit_m = unit_pre or unit_post

        weight = 0.0
        multiplier = 1.0

        if gram_m:
            weight = float(gram_m.group(1))
            multiplier = weight / 100.0
        elif kg_m:
            weight = float(kg_m.group(1)) * 1000.0
            multiplier = weight / 100.0
        elif portion_m:
            raw_qty = portion_m.group(1) or "1"
            qty = float(UZ_NUMS.get(raw_qty, raw_qty if raw_qty.isdigit() else 1))
            unit_name = portion_m.group(2)
            if unit_name == "kosa":
                weight = qty * 400.0
            elif unit_name in ["likopcha", "tarelka", "porsiya", "pors"]:
                weight = qty * 350.0
            elif unit_name == "stakan":
                weight = qty * 250.0
            else:
                weight = qty * item.get("portion_g", 300)
            multiplier = weight / 100.0
        elif unit_m and (item.get("is_unit") or re.search(r'(?:ta|dona|bo\'lak|bolak|siyx|tilim)', unit_m.group(0))):
            raw_qty = unit_m.group(1)
            qty = float(UZ_NUMS.get(raw_qty, raw_qty if raw_qty.isdigit() else 1))
            if item.get("is_unit"):
                multiplier = qty
                weight = qty * item.get("unit_g", 100)
            else:
                weight = qty * item.get("portion_g", 150)
                multiplier = weight / 100.0
        else:
            # Default portion
            if item.get("is_unit"):
                multiplier = 1.0
                weight = item.get("unit_g", 100)
            else:
                weight = item.get("portion_g", 150)
                multiplier = weight / 100.0

        if item.get("is_unit") and not gram_m and not kg_m:
            total_kcal += item["unit_kcal"] * multiplier
            total_p += item["unit_p"] * multiplier
            total_c += item["unit_c"] * multiplier
            total_f += item["unit_f"] * multiplier
        else:
            total_kcal += item["kcal_100"] * multiplier
            total_p += item["p_100"] * multiplier
            total_c += item["c_100"] * multiplier
            total_f += item["f_100"] * multiplier

        total_grams += weight

    return {
        "meal_type": meal_type,
        "food_name": ", ".join(names_list[:3]),
        "calories": round(total_kcal, 1),
        "protein": round(total_p, 1),
        "carbs": round(total_c, 1),
        "fat": round(total_f, 1),
        "weight_grams": round(total_grams, 1)
    }

if __name__ == "__main__":
    tests = [
        "Tushlikda 200gr tovuq filesi va 150gr grechka yedim",
        "1 kosa lag'mon va 2 dona somsa yedim",
        "2 ta tuxum va 1 ta banan",
        "1 likopcha osh va achchiq-chuchuk salat",
        "1 dona lavash va 1 stakan kola",
        "go'shtli ovqat yedim"
    ]
    for t in tests:
        res = parse_food_test(t)
        print(f"INPUT: {t}")
        print(f"RESULT: {res}\n")
