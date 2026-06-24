import json
import os
import math
import urllib.parse

# ============================================================
# db.py — Data layer for the Hương Vị Bắc Chatbot
# Loads dishes (EN + VI) and restaurants from JSON files
# extracted from the .docx databases.
# ============================================================

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_json(filename):
    """Load a JSON file from the same directory as this module."""
    path = os.path.join(_BASE_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load all data at import time
DISHES_EN = _load_json("food_eng.json")   # 70 dishes in English
DISHES_VI = _load_json("food_vie.json")   # 70 dishes in Vietnamese
RESTAURANTS = _load_json("restaurants.json")  # 43 restaurants

# Build a quick lookup: dish_id -> dish data (EN and VI)
DISH_EN_BY_ID = {d["dish_id"]: d for d in DISHES_EN}
DISH_VI_BY_ID = {d["dish_id"]: d for d in DISHES_VI}

# Build a reverse index: Vietnamese dish name -> list of restaurants
# This maps each menu item to the restaurants that serve it.
MENU_TO_RESTAURANTS = {}
for rest in RESTAURANTS:
    for item in rest.get("menu", []):
        item_lower = item.lower().strip()
        if item_lower not in MENU_TO_RESTAURANTS:
            MENU_TO_RESTAURANTS[item_lower] = []
        MENU_TO_RESTAURANTS[item_lower].append(rest)

# Also build: dish_id -> list of restaurants (by matching dish Vietnamese name to menu)
DISH_ID_TO_RESTAURANTS = {}
for dish_vi in DISHES_VI:
    dish_name_vi = dish_vi["name"].lower().strip()
    matching_rests = MENU_TO_RESTAURANTS.get(dish_name_vi, [])
    DISH_ID_TO_RESTAURANTS[dish_vi["dish_id"]] = matching_rests


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth
    in kilometers using the Haversine formula.
    """
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def build_gemini_system_prompt(lang="fr"):
    """
    Build a compact system prompt for Gemini with all dish and restaurant data.
    Kept concise to stay within free-tier token limits.
    """
    rests_only = [r for r in RESTAURANTS if r.get("place type") != "street food"]
    street_only = [r for r in RESTAURANTS if r.get("place type") == "street food"]

    if lang == "en":
        prompt = """You are an expert culinary guide for Hanoi (Northern Vietnam). ALWAYS respond in ENGLISH.
Help tourists find dishes and restaurants in Hanoi.
RULES: Respond in simple Markdown (bold, lists, emojis 🍜⭐📍💰). NEVER use HTML.
When you recommend a dish, provide its name, ingredients, price, and the places serving it with their addresses and maps links.

CRITICAL RULE: When recommending places to eat, you MUST always separate them into two distinct categories:
- "Restaurants 🏛️" (places listed under === RESTAURANTS ===)
- "Street Food 🛵" (places listed under === STREET FOOD ===)
Clearly group your recommendations under these two separate headers and do not combine them in a single list!

=== DISHES ===
"""
        dishes = DISHES_EN
        for d in dishes:
            ings = ", ".join(d.get("ingredients", []))
            tags = d.get("ai_search_tags", "")
            prompt += f"[{d['dish_id']}] {d['name']} | {d['category']} | {d['price_range']} VND | Ingredients: {ings} | Tags: {tags}\n"

        prompt += "\n=== RESTAURANTS ===\n"
        for r in rests_only:
            name = r.get("restaurant_name") or "(Restaurant)"
            addr = r.get("address", "")
            menu = ", ".join(r.get("menu", []))
            rating = r.get("rating", 4.5)
            q = f"{name} {addr}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
            prompt += f"📍 {name} — {addr} (Rating: {rating}/5) [Google Maps]({maps_url}) | Menu: {menu}\n"

        prompt += "\n=== STREET FOOD ===\n"
        for r in street_only:
            name = r.get("restaurant_name") or "(Street food)"
            addr = r.get("address", "")
            menu = ", ".join(r.get("menu", []))
            rating = r.get("rating", 4.5)
            q = f"{name} {addr}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
            prompt += f"📍 {name} — {addr} (Rating: {rating}/5) [Google Maps]({maps_url}) | Menu: {menu}\n"

    elif lang == "vi":
        prompt = """Bạn là hướng dẫn viên ẩm thực Hà Nội (Miền Bắc Việt Nam). LUÔN trả lời bằng TIẾNG VIỆT.
Giúp du khách tìm kiếm món ăn và quán ăn tại Hà Nội.
QUY TẮC: Trả lời bằng Markdown đơn giản (chữ đậm, danh sách, emojis 🍜⭐📍💰). KHÔNG BAO GIỜ dùng HTML.
Khi gợi ý món ăn, hãy cung cấp tên món, nguyên liệu, giá cả và danh sách quán ăn kèm theo địa chỉ và link bản đồ.

QUY TẮC QUAN TRỌNG: Khi gợi ý các địa điểm ăn uống, bạn phải LUÔN tách biệt chúng thành hai danh mục rõ ràng:
- "Nhà hàng 🏛️" (các quán thuộc === RESTAURANTS ===)
- "Ẩm thực đường phố 🛵" (các quán thuộc === STREET FOOD ===)
Hãy nhóm các gợi ý của bạn dưới hai tiêu đề riêng biệt này và không gộp chung vào một danh sách!

=== MÓN ĂN ===
"""
        dishes = DISHES_VI
        for d in dishes:
            ings = ", ".join(d.get("ingredients", []))
            tags = d.get("ai_search_tags", "")
            prompt += f"[{d['dish_id']}] {d['name']} | {d['category']} | {d['price_range']} VND | Nguyên liệu: {ings} | Tags: {tags}\n"

        prompt += "\n=== RESTAURANTS ===\n"
        for r in rests_only:
            name = r.get("restaurant_name") or "(Nhà hàng)"
            addr = r.get("address", "")
            menu = ", ".join(r.get("menu", []))
            rating = r.get("rating", 4.5)
            q = f"{name} {addr}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
            prompt += f"📍 {name} — {addr} (Đánh giá: {rating}/5) [Google Maps]({maps_url}) | Thực đơn: {menu}\n"

        prompt += "\n=== STREET FOOD ===\n"
        for r in street_only:
            name = r.get("restaurant_name") or "(Ẩm thực đường phố)"
            addr = r.get("address", "")
            menu = ", ".join(r.get("menu", []))
            rating = r.get("rating", 4.5)
            q = f"{name} {addr}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
            prompt += f"📍 {name} — {addr} (Đánh giá: {rating}/5) [Google Maps]({maps_url}) | Thực đơn: {menu}\n"

    else: # "fr" or fallback
        prompt = """Tu es un guide culinaire expert de Hanoï (Nord du Vietnam). Réponds TOUJOURS en FRANÇAIS.
Aide les touristes à trouver des plats et restaurants à Hanoï.
RÈGLES : Réponds en Markdown simple (gras, listes, emojis 🍜⭐📍💰). JAMAIS de HTML.
Quand tu recommandes un plat, donne son nom, ses ingrédients, son prix, et les restaurants qui le servent avec leur adresse et lien Google Maps.

RÈGLE CRITIQUE : Lorsque tu recommandes des lieux pour manger, tu dois TOUJOURS les séparer en deux catégories distinctes :
- "Restaurants 🏛️" (les lieux listés sous === RESTAURANTS ===)
- "Street Food 🛵" (les lieux listés sous === STREET FOOD ===)
Groupe clairement tes recommandations sous ces deux en-têtes séparés et ne les mélange pas dans une seule liste !

=== PLATS ===
"""
        dishes = DISHES_EN  # French version of app still maps English dishes or VI names
        for d in dishes:
            ings = ", ".join(d.get("ingredients", []))
            tags = d.get("ai_search_tags", "")
            prompt += f"[{d['dish_id']}] {d['name']} | {d['category']} | {d['price_range']} VND | Ingrédients: {ings} | Tags: {tags}\n"

        prompt += "\n=== RESTAURANTS ===\n"
        for r in rests_only:
            name = r.get("restaurant_name") or "(Restaurant)"
            addr = r.get("address", "")
            menu = ", ".join(r.get("menu", []))
            rating = r.get("rating", 4.5)
            q = f"{name} {addr}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
            prompt += f"📍 {name} — {addr} (Note: {rating}/5) [Itinéraire Google Maps]({maps_url}) | Menu: {menu}\n"

        prompt += "\n=== STREET FOOD ===\n"
        for r in street_only:
            name = r.get("restaurant_name") or "(Street food)"
            addr = r.get("address", "")
            menu = ", ".join(r.get("menu", []))
            rating = r.get("rating", 4.5)
            q = f"{name} {addr}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
            prompt += f"📍 {name} — {addr} (Note: {rating}/5) [Itinéraire Google Maps]({maps_url}) | Menu: {menu}\n"

    return prompt


# ============================================================
# Photo Mapping Support
# ============================================================
import unicodedata

_PHOTO_DIR = os.path.join(_BASE_DIR, "photo")
_PHOTOS = os.listdir(_PHOTO_DIR) if os.path.exists(_PHOTO_DIR) else []

def _strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def _normalize_name(text):
    text_clean = _strip_accents(text).lower()
    return "".join(c for c in text_clean if c.isalnum())

_PHOTO_MAP = {_normalize_name(os.path.splitext(p)[0]): p for p in _PHOTOS}

_PHOTO_OVERRIDES = {
    "nganchaytoi": "Ngan cháy tỏ.jfif",
    "banhmi": "Bahn Mi.jfif"
}

def get_dish_photo(dish_name_vi):
    """
    Get the filename of the photo matching the dish name, or None.
    Normalized by removing accents, spaces, and punctuation.
    """
    if not dish_name_vi:
        return None
    name_clean = dish_name_vi.split("(")[0].strip()
    name_norm = _normalize_name(name_clean)
    
    if name_norm in _PHOTO_OVERRIDES:
        return _PHOTO_OVERRIDES[name_norm]
    
    return _PHOTO_MAP.get(name_norm)
