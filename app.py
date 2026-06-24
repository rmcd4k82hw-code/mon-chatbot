import streamlit as st
import json
import os
import urllib.parse
from db import (
    DISHES_EN, DISHES_VI, RESTAURANTS,
    DISH_EN_BY_ID, DISH_VI_BY_ID,
    DISH_ID_TO_RESTAURANTS, MENU_TO_RESTAURANTS,
    build_gemini_system_prompt,
    haversine_distance,
    get_dish_photo
)

# ============================================================
# Page config
# ============================================================
st.set_page_config(
    page_title="Hương Vị Bắc — Culinary Chatbot",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# LOCALIZATION — Minimal UI strings
# ============================================================
LOC = {
    "fr": {
        "lang_label": "🌐 Langue de l'interface",
        "api_header": "🔑 Clé API Gemini",
        "api_help": "Obtenez une clé gratuite sur [Google AI Studio](https://aistudio.google.com/apikey)",
        "api_placeholder": "Collez votre clé API ici",
        "api_missing": "⚠️ Veuillez entrer votre clé API Gemini dans la barre latérale pour activer le chatbot.",
        "title": "🍲 Hương Vị Bắc",
        "subtitle": "Guide culinaire intelligent — Nord du Vietnam",
        "tab_chat": "💬 Chatbot",
        "tab_dishes": "🍲 Encyclopédie",
        "chat_placeholder": "Ex: Je veux manger quelque chose avec du boeuf et des nouilles...",
        "welcome": "Xin chào ! Bonjour ! 👋\n\nJe suis votre guide culinaire pour le Nord du Vietnam. Dites-moi quels ingrédients ou plats vous font envie, et je vous recommanderai les meilleurs restaurants de Hanoï !",
        "clear": "🗑️ Effacer le chat",
        "thinking": "Réflexion en cours...",
        "error_api": "❌ Erreur API : ",
        "category_labels": {
            "NOODLE_SOUP": "🍜 Soupes de nouilles",
            "STREETFOOD": "🥟 Street food & Snacks",
            "DRINKS_DESSERTS": "🍧 Boissons & Desserts",
            "SPECIALTY": "🌟 Spécialités",
            "MAIN_COURSE": "🥘 Plats principaux"
        },
        "ingredients_label": "Ingrédients",
        "taste_label": "Profil gustatif",
        "price_label": "Prix",
        "tags_label": "Tags",
        "restaurants_serving": "Restaurants servant ce plat",
        "diag_button": "🔍 Diagnostiquer la clé",
        "diag_success": "✅ Modèles disponibles :",
        "diag_fail": "❌ Erreur :",
        "model_label": "🤖 Modèle Gemini",
        "tab_map": "🗺️ Carte & Lieux",
        "sort_label": "Trier les restaurants par :",
        "sort_rating": "Note ⭐ (décroissante)",
        "sort_distance": "Distance 📍 (croissante)",
        "location_label": "📍 Ma position (Simulation) :",
        "location_center": "Lac Hoan Kiem (Centre)",
        "location_opera": "Opéra de Hanoï",
        "location_temple": "Temple de la Littérature",
        "location_bridge": "Pont Long Bien",
        "location_custom": "Coordonnées personnalisées...",
        "lat_label": "Latitude",
        "lon_label": "Longitude",
        "suggestions_label": "💡 Suggestions rapides :",
        "maps_link_text": "🗺️ Itinéraire Google Maps",
    },
    "en": {
        "lang_label": "🌐 Interface language",
        "api_header": "🔑 Gemini API Key",
        "api_help": "Get a free key on [Google AI Studio](https://aistudio.google.com/apikey)",
        "api_placeholder": "Paste your API key here",
        "api_missing": "⚠️ Please enter your Gemini API key in the sidebar to activate the chatbot.",
        "title": "🍲 Hương Vị Bắc",
        "subtitle": "Intelligent culinary guide — Northern Vietnam",
        "tab_chat": "💬 Chatbot",
        "tab_dishes": "🍲 Encyclopedia",
        "chat_placeholder": "E.g., I want to eat something with beef and noodles...",
        "welcome": "Xin chào! Hello! 👋\n\nI'm your culinary guide for Northern Vietnam. Tell me what ingredients or dishes you crave, and I'll recommend the best restaurants in Hanoi!",
        "clear": "🗑️ Clear chat",
        "thinking": "Thinking...",
        "error_api": "❌ API Error: ",
        "category_labels": {
            "NOODLE_SOUP": "🍜 Noodle Soups",
            "STREETFOOD": "🥟 Street Food & Snacks",
            "DRINKS_DESSERTS": "🍧 Drinks & Desserts",
            "SPECIALTY": "🌟 Specialties",
            "MAIN_COURSE": "🥘 Main Courses"
        },
        "ingredients_label": "Ingredients",
        "taste_label": "Taste profile",
        "price_label": "Price",
        "tags_label": "Tags",
        "restaurants_serving": "Restaurants serving this dish",
        "diag_button": "🔍 Diagnose Key",
        "diag_success": "✅ Available models:",
        "diag_fail": "❌ Error:",
        "model_label": "🤖 Gemini Model",
        "tab_map": "🗺️ Map & Places",
        "sort_label": "Sort restaurants by:",
        "sort_rating": "Rating ⭐ (highest)",
        "sort_distance": "Distance 📍 (nearest)",
        "location_label": "📍 My Position (Simulation):",
        "location_center": "Hoan Kiem Lake (Center)",
        "location_opera": "Hanoi Opera House",
        "location_temple": "Temple of Literature",
        "location_bridge": "Long Bien Bridge",
        "location_custom": "Custom coordinates...",
        "lat_label": "Latitude",
        "lon_label": "Longitude",
        "suggestions_label": "💡 Quick suggestions:",
        "maps_link_text": "🗺️ View on Google Maps",
    },
    "vi": {
        "lang_label": "🌐 Ngôn ngữ giao diện",
        "api_header": "🔑 Khóa API Gemini",
        "api_help": "Lấy khóa miễn phí tại [Google AI Studio](https://aistudio.google.com/apikey)",
        "api_placeholder": "Dán khóa API của bạn ở đây",
        "api_missing": "⚠️ Vui lòng nhập khóa API Gemini vào thanh bên để kích hoạt chatbot.",
        "title": "🍲 Hương Vị Bắc",
        "subtitle": "Cẩm nang ẩm thực thông minh — Miền Bắc Việt Nam",
        "tab_chat": "💬 Chatbot",
        "tab_dishes": "🍲 Bách khoa toàn thư",
        "chat_placeholder": "Ví dụ: Tôi muốn ăn gì đó có thịt bò và phở...",
        "welcome": "Xin chào! 👋\n\nTôi là hướng dẫn viên ẩm thực của bạn tại miền Bắc Việt Nam. Hãy cho tôi biết bạn thích nguyên liệu hay món ăn gì, tôi sẽ gợi ý quán ăn ngon nhất Hà Nội!",
        "clear": "🗑️ Xóa lịch sử",
        "thinking": "Đang suy nghĩ...",
        "error_api": "❌ Lỗi API: ",
        "category_labels": {
            "NOODLE_SOUP": "🍜 Bún phở",
            "STREETFOOD": "🥟 Ăn vặt đường phố",
            "DRINKS_DESSERTS": "🍧 Đồ uống & Tráng miệng",
            "SPECIALTY": "🌟 Đặc sản",
            "MAIN_COURSE": "🥘 Món chính"
        },
        "ingredients_label": "Nguyên liệu",
        "taste_label": "Hương vị",
        "price_label": "Giá",
        "tags_label": "Tags",
        "restaurants_serving": "Quán ăn phục vụ món này",
        "diag_button": "🔍 Chẩn đoán khóa",
        "diag_success": "✅ Các mô hình có sẵn:",
        "diag_fail": "❌ Lỗi:",
        "model_label": "🤖 Mô hình Gemini",
        "tab_map": "🗺️ Bản đồ & Địa điểm",
        "sort_label": "Sắp xếp quán ăn theo:",
        "sort_rating": "Đánh giá ⭐ (cao nhất)",
        "sort_distance": "Khoảng cách 📍 (gần nhất)",
        "location_label": "📍 Vị trí của tôi (Mô phỏng):",
        "location_center": "Hồ Hoàn Kiếm (Trung tâm)",
        "location_opera": "Nhà hát Lớn Hà Nội",
        "location_temple": "Văn Miếu - Quốc Tử Giám",
        "location_bridge": "Cầu Long Biên",
        "location_custom": "Tọa độ tùy chỉnh...",
        "lat_label": "Vĩ độ",
        "lon_label": "Kinh độ",
        "suggestions_label": "💡 Gợi ý nhanh:",
        "maps_link_text": "🗺️ Xem trên Google Maps",
    },
}

# ============================================================
# SIDEBAR
# ============================================================
# Language selector
lang_choice = st.sidebar.selectbox(
    "🌐",
    ["Français", "English", "Tiếng Việt"],
    label_visibility="collapsed"
)
lang_map = {"Français": "fr", "English": "en", "Tiếng Việt": "vi"}
lang = lang_map[lang_choice]
L = LOC[lang]

st.sidebar.markdown(f"### {L['api_header']}")
st.sidebar.markdown(L["api_help"])
api_key = st.sidebar.text_input(
    L["api_placeholder"],
    type="password",
    label_visibility="collapsed"
).strip()

# Validate key is pure ASCII (no emojis, hidden characters, etc.)
is_ascii = True
if api_key:
    try:
        api_key.encode('ascii')
    except UnicodeEncodeError:
        is_ascii = False

if api_key and not is_ascii:
    st.sidebar.error("⚠️ La clé contient des caractères invalides (émojis, espaces spéciaux, etc.). Veuillez la copier-coller proprement.")

if api_key and is_ascii:
    if st.sidebar.button(L["diag_button"]):
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            models = list(client.models.list())
            st.sidebar.markdown(f"### {L['diag_success']}")
            
            test_models = ["gemini-2.0-flash-lite", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.5-flash"]
            available_names = [m.name.replace("models/", "") for m in models]
            models_to_test = [m for m in test_models if m in available_names]
            
            st.sidebar.markdown("**Statut des modèles :**")
            for model_name in models_to_test:
                try:
                    client.models.generate_content(
                        model=model_name,
                        contents="Hi"
                    )
                    st.sidebar.write(f"🟢 `{model_name}` : **Actif (Quota OK)**")
                except Exception as e:
                    err_msg = str(e)
                    if "limit: 0" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        st.sidebar.write(f"🔴 `{model_name}` : **Quota dépassé (Limite: 0)**")
                    elif "503" in err_msg or "UNAVAILABLE" in err_msg:
                        st.sidebar.write(f"⚠️ `{model_name}` : **Temporairement indisponible (503)**")
                    else:
                        st.sidebar.write(f"⚠️ `{model_name}` : **Erreur** (`{err_msg[:40]}...`)")
            
            with st.sidebar.expander("Tous les modèles disponibles"):
                for m in models:
                    name = m.name.replace("models/", "")
                    st.sidebar.write(f"- `{name}`")
        except Exception as e:
            st.sidebar.error(f"{L['diag_fail']} {str(e)}")

# Model selection selectbox
model_options = ["gemini-2.0-flash-lite", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.5-flash"]
selected_model = st.sidebar.selectbox(
    L["model_label"],
    model_options,
    index=0
)

st.sidebar.markdown("---")

# User position simulation
pos_options = {
    L["location_center"]: (21.0285, 105.8522),
    L["location_opera"]: (21.0245, 105.8576),
    L["location_temple"]: (21.0293, 105.8361),
    L["location_bridge"]: (21.0423, 105.8596),
    L["location_custom"]: None
}
selected_pos_name = st.sidebar.selectbox(
    L["location_label"],
    list(pos_options.keys()),
    index=0
)

if selected_pos_name == L["location_custom"]:
    user_lat = st.sidebar.number_input(L["lat_label"], value=21.0285, format="%.6f")
    user_lon = st.sidebar.number_input(L["lon_label"], value=105.8522, format="%.6f")
else:
    coords = pos_options[selected_pos_name]
    user_lat, user_lon = coords[0], coords[1]

st.session_state.user_lat = user_lat
st.session_state.user_lon = user_lon

# Compute distances for all restaurants from user_lat, user_lon
for r in RESTAURANTS:
    r_lat = r.get("latitude")
    r_lon = r.get("longitude")
    if r_lat is not None and r_lon is not None:
        r["distance"] = round(haversine_distance(user_lat, user_lon, r_lat, r_lon), 2)
    else:
        r["distance"] = 9999.0

# Sorting option
sort_options_map = {
    L["sort_rating"]: "rating",
    L["sort_distance"]: "distance"
}
selected_sort_name = st.sidebar.selectbox(
    L["sort_label"],
    list(sort_options_map.keys()),
    index=0
)
selected_sort = sort_options_map[selected_sort_name]
st.session_state.selected_sort = selected_sort

st.sidebar.markdown("---")

if st.sidebar.button(L["clear"]):
    st.session_state.messages = []
    st.rerun()

# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

def get_gemini_response(user_message, chat_history, language, model_name):
    """Send message to Gemini and return the response text with auto-retry and helpful tips."""
    import time
    max_retries = 3
    delay = 1.0
    for attempt in range(max_retries):
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # Build the system prompt with all database knowledge
            system_prompt = build_gemini_system_prompt(language)

            # Build conversation history for the chat
            history = []
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            # Start chat with history and configuration
            chat = client.chats.create(
                model=model_name,
                history=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            response = chat.send_message(user_message)

            return response.text

        except Exception as e:
            err_str = str(e)
            is_retryable = "503" in err_str or "504" in err_str or "429" in err_str or "UNAVAILABLE" in err_str or "RESOURCE_EXHAUSTED" in err_str or "spikes in demand" in err_str.lower()
            if is_retryable and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
                continue
            else:
                hint = ""
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    hint = "\n\n💡 **Conseil** : Le modèle choisi est temporairement surchargé. Essayez de sélectionner un autre modèle dans la barre latérale (ex: `gemini-2.0-flash-lite` ou `gemini-2.5-flash-lite`) qui sont souvent plus disponibles." if language == "fr" else \
                           "\n\n💡 **Tip**: The selected model is temporarily overloaded. Try choosing a different model from the sidebar (e.g., `gemini-2.0-flash-lite` or `gemini-2.5-flash-lite`) which are usually more available." if language == "en" else \
                           "\n\n💡 **Gợi ý**: Mô hình đã chọn hiện đang quá tải. Hãy thử chọn một mô hình khác trong thanh bên (ví dụ: `gemini-2.0-flash-lite` hoặc `gemini-2.5-flash-lite`)."
                elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    hint = "\n\n💡 **Conseil** : Quota d'API dépassé pour ce modèle. Veuillez patienter quelques secondes ou essayer un autre modèle (ex: `gemini-2.0-flash-lite` ou `gemini-2.5-flash-lite`)." if language == "fr" else \
                           "\n\n💡 **Tip**: API quota exceeded for this model. Please wait a few seconds or try another model (e.g., `gemini-2.0-flash-lite` or `gemini-2.5-flash-lite`)." if language == "en" else \
                           "\n\n💡 **Gợi ý**: Đã vượt quá giới hạn yêu cầu (quota). Vui lòng đợi vài giây hoặc thử mô hình khác (ví dụ: `gemini-2.0-flash-lite` hoặc `gemini-2.5-flash-lite`)."
                
                return f"{L['error_api']}{err_str}{hint}"



def extract_mentioned_dishes(text, dishes_vi):
    """Scan the text for any mentions of Vietnamese dish names and return the matching dish objects."""
    mentioned = []
    text_lower = text.lower()
    for d in dishes_vi:
        # Get the main name without parenthesis (e.g. "Bún chả" from "Bún chả (Grilled Pork)")
        name_vi = d["name"].lower()
        name_clean = name_vi.split("(")[0].strip()
        if name_clean in text_lower:
            mentioned.append(d)
    return mentioned


# ============================================================
# MAIN LAYOUT
# ============================================================
st.markdown(f"# {L['title']}")
st.caption(L["subtitle"])

tab_chat, tab_dishes, tab_map = st.tabs([L["tab_chat"], L["tab_dishes"], L["tab_map"]])

# ============================================================
# TAB 1: CHATBOT
# ============================================================
with tab_chat:
    if not api_key:
        st.warning(L["api_missing"])

    # Show welcome message if chat is empty
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(L["welcome"])

        st.markdown(f"#### {L['suggestions_label']}")
        suggestions_list = {
            "fr": [
                ("🍜 Recommander un Pho", "Je cherche un bon Phở Bò près de ma position."),
                ("🥟 Street Food populaire", "Quels sont les meilleurs snacks de street food dans le quartier ?"),
                ("⭐ Mieux notés", "Quels sont les restaurants de spécialités les mieux notés ?"),
                ("☕ Café à l'œuf local", "Où puis-je boire un café aux œufs (Cà phê trứng) ?")
            ],
            "en": [
                ("🍜 Recommend a Pho", "I am looking for a good Phở Bò near my location."),
                ("🥟 Popular Street Food", "What are the best street food snacks in the neighborhood?"),
                ("⭐ Highest Rated", "Which specialty restaurants are the highest rated?"),
                ("☕ Local Egg Coffee", "Where can I drink egg coffee (Cà phê trứng)?")
            ],
            "vi": [
                ("🍜 Gợi ý món Phở", "Tôi muốn tìm quán Phở Bò ngon gần vị trí của tôi."),
                ("🥟 Ăn vặt nổi tiếng", "Những món ăn vặt đường phố nào ngon nhất ở khu vực này?"),
                ("⭐ Đánh giá tốt nhất", "Quán ăn đặc sản nào được đánh giá cao nhất?"),
                ("☕ Cà phê trứng", "Tôi có thể uống Cà phê trứng ở đâu ngon?")
            ]
        }
        
        clicked_prompt = None
        col1, col2 = st.columns(2)
        with col1:
            for label, prompt in suggestions_list[lang][:2]:
                if st.button(label, use_container_width=True):
                    clicked_prompt = prompt
        with col2:
            for label, prompt in suggestions_list[lang][2:]:
                if st.button(label, use_container_width=True):
                    clicked_prompt = prompt
                    
        if clicked_prompt:
            st.session_state.messages.append({"role": "user", "content": clicked_prompt})
            if not api_key:
                assistant_msg = L["api_missing"]
                st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
            elif not is_ascii:
                assistant_msg = "⚠️ La clé API entrée contient des caractères invalides (émojis, espaces masqués, etc.). Veuillez copier-coller proprement une clé valide."
                st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
            else:
                with st.spinner(L["thinking"]):
                    response_text = get_gemini_response(
                        clicked_prompt,
                        st.session_state.messages[:-1],
                        lang,
                        selected_model
                    )
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()

    # Create scrollable container for chat history
    chat_container = st.container(height=500)

    # Display chat history inside the container
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    mentioned = extract_mentioned_dishes(msg["content"], DISHES_VI)
                    if mentioned:
                        unique_mentioned = []
                        seen_ids = set()
                        for d in mentioned:
                            if d["dish_id"] not in seen_ids:
                                photo_file = get_dish_photo(d["name"])
                                if photo_file:
                                    unique_mentioned.append((d, photo_file))
                                    seen_ids.add(d["dish_id"])
                        if unique_mentioned:
                            expander_title = "📷 Photos des plats" if lang == "fr" else "📷 Photos of dishes" if lang == "en" else "📷 Ảnh các món ăn"
                            with st.expander(expander_title):
                                cols = st.columns(min(len(unique_mentioned), 4))
                                for idx, (d, photo_file) in enumerate(unique_mentioned):
                                    col = cols[idx % len(cols)]
                                    with col:
                                        st.image(f"photo/{photo_file}", caption=d["name"], use_container_width=True)

    # Chat input
    if user_input := st.chat_input(L["chat_placeholder"]):
        # Display user message inside the container
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        if not api_key:
            assistant_msg = L["api_missing"]
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(assistant_msg)
            st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
        elif not is_ascii:
            assistant_msg = "⚠️ La clé API entrée contient des caractères invalides (émojis, espaces masqués, etc.). Veuillez copier-coller proprement une clé valide."
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(assistant_msg)
            st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
        else:
            # Call Gemini
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner(L["thinking"]):
                        response_text = get_gemini_response(
                            user_input,
                            st.session_state.messages[:-1],  # history without the just-added user msg
                            lang,
                            selected_model
                        )
                    st.markdown(response_text)
                    
                    # Display photos of mentioned dishes
                    mentioned = extract_mentioned_dishes(response_text, DISHES_VI)
                    if mentioned:
                        unique_mentioned = []
                        seen_ids = set()
                        for d in mentioned:
                            if d["dish_id"] not in seen_ids:
                                photo_file = get_dish_photo(d["name"])
                                if photo_file:
                                    unique_mentioned.append((d, photo_file))
                                    seen_ids.add(d["dish_id"])
                        if unique_mentioned:
                            expander_title = "📷 Photos des plats" if lang == "fr" else "📷 Photos of dishes" if lang == "en" else "📷 Ảnh các món ăn"
                            with st.expander(expander_title):
                                cols = st.columns(min(len(unique_mentioned), 4))
                                for idx, (d, photo_file) in enumerate(unique_mentioned):
                                    col = cols[idx % len(cols)]
                                    with col:
                                        st.image(f"photo/{photo_file}", caption=d["name"], use_container_width=True)
            st.session_state.messages.append({"role": "assistant", "content": response_text})

# ============================================================
# TAB 2: DISH ENCYCLOPEDIA
# ============================================================
with tab_dishes:
    # Choose which language data to display
    dishes_data = DISHES_EN if lang == "en" else DISHES_VI

    # Group dishes by category
    categories_order = ["NOODLE_SOUP", "MAIN_COURSE", "STREETFOOD", "SPECIALTY", "DRINKS_DESSERTS"]
    cat_labels = L["category_labels"]

    for cat in categories_order:
        cat_dishes = [d for d in dishes_data if d.get("category") == cat]
        if not cat_dishes:
            continue

        st.markdown(f"## {cat_labels.get(cat, cat)}")

        for dish in cat_dishes:
            dish_id = dish["dish_id"]
            # Get the other language version for bilingual display
            dish_other = DISH_EN_BY_ID.get(dish_id) if lang != "en" else DISH_VI_BY_ID.get(dish_id)
            en_name = DISH_EN_BY_ID.get(dish_id, {}).get("name", "")

            with st.expander(f"**{dish['name']}** — {en_name if lang != 'en' else DISH_VI_BY_ID.get(dish_id, {}).get('name', '')}"):
                # Check for photo
                dish_vi_name = DISH_VI_BY_ID.get(dish_id, {}).get("name", "")
                photo_file = get_dish_photo(dish_vi_name)
                
                if photo_file:
                    col_info, col_img = st.columns([2, 1])
                    with col_info:
                        # Description
                        st.markdown(dish.get("detailed_description", ""))
                        
                        # Info columns
                        col1, col2 = st.columns(2)
                        with col1:
                            ingredients = dish.get("ingredients", [])
                            if ingredients:
                                st.markdown(f"**{L['ingredients_label']}:** {', '.join(ingredients)}")
                            taste = dish.get("taste_profile", "")
                            if taste:
                                st.markdown(f"**{L['taste_label']}:** {taste}")
                        with col2:
                            price = dish.get("price_range", "")
                            if price:
                                st.markdown(f"**{L['price_label']}:** {price} VND")
                            tags = dish.get("ai_search_tags", "")
                            if tags:
                                st.markdown(f"**{L['tags_label']}:** {tags}")
                    with col_img:
                        st.image(f"photo/{photo_file}", use_container_width=True)
                else:
                    # Description
                    st.markdown(dish.get("detailed_description", ""))
                    
                    # Info columns
                    col1, col2 = st.columns(2)
                    with col1:
                        ingredients = dish.get("ingredients", [])
                        if ingredients:
                            st.markdown(f"**{L['ingredients_label']}:** {', '.join(ingredients)}")
                        taste = dish.get("taste_profile", "")
                        if taste:
                            st.markdown(f"**{L['taste_label']}:** {taste}")
                    with col2:
                        price = dish.get("price_range", "")
                        if price:
                            st.markdown(f"**{L['price_label']}:** {price} VND")
                        tags = dish.get("ai_search_tags", "")
                        if tags:
                            st.markdown(f"**{L['tags_label']}:** {tags}")

                # Show which restaurants serve this dish
                serving_rests = DISH_ID_TO_RESTAURANTS.get(dish_id, [])
                if serving_rests:
                    if selected_sort == "rating":
                        sorted_serving = sorted(serving_rests, key=lambda x: (-x.get("rating", 0.0), x.get("distance", 9999.0)))
                    else:
                        sorted_serving = sorted(serving_rests, key=lambda x: (x.get("distance", 9999.0), -x.get("rating", 0.0)))

                    st.markdown(f"**{L['restaurants_serving']}:**")
                    for rest in sorted_serving:
                        r_name = rest.get("restaurant_name") or "Street food zone"
                        r_addr = rest.get("address", "")
                        r_rating = rest.get("rating", 4.5)
                        r_dist = rest.get("distance", 0.0)
                        q = f"{r_name} {r_addr}"
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
                        st.markdown(f"- 📍 **{r_name}** — {r_addr} (⭐ {r_rating} | 🚗 {r_dist} km) — [🗺️ Maps]({maps_url})")

# ============================================================
# TAB 3: CARTE & RESTAURANTS
# ============================================================
with tab_map:
    import pandas as pd
    import pydeck as pdk

    # Sort all restaurants based on selected sorting criteria
    if selected_sort == "rating":
        sorted_rests = sorted(RESTAURANTS, key=lambda x: (-x.get("rating", 0.0), x.get("distance", 9999.0)))
    else:
        sorted_rests = sorted(RESTAURANTS, key=lambda x: (x.get("distance", 9999.0), -x.get("rating", 0.0)))

    st.subheader(L["tab_map"])
    
    # Create DataFrame for restaurants map markers
    map_data = []
    for r in RESTAURANTS:
        r_lat = r.get("latitude")
        r_lon = r.get("longitude")
        if r_lat is not None and r_lon is not None:
            map_data.append({
                "name": r.get("restaurant_name", "Street food"),
                "lat": r_lat,
                "lon": r_lon,
                "rating": r.get("rating", 4.5),
                "distance": r.get("distance", 0.0),
                "address": r.get("address", "")
            })
            
    if map_data:
        df_rests = pd.DataFrame(map_data)
        df_user = pd.DataFrame([{"lat": user_lat, "lon": user_lon, "name": "Moi" if lang == "fr" else "Me" if lang == "en" else "Tôi"}])
        
        # Pydeck layers
        layer_rests = pdk.Layer(
            "ScatterplotLayer",
            data=df_rests,
            get_position="[lon, lat]",
            get_color=[230, 50, 50, 180],  # Red for restaurants
            get_radius=80,
            pickable=True,
        )
        
        layer_user = pdk.Layer(
            "ScatterplotLayer",
            data=df_user,
            get_position="[lon, lat]",
            get_color=[30, 120, 250, 225],  # Blue for user
            get_radius=140,
            pickable=True,
        )
        
        # View state centered on user
        view_state = pdk.ViewState(
            latitude=user_lat,
            longitude=user_lon,
            zoom=13.5,
            pitch=0
        )
        
        # Render map
        st.pydeck_chart(pdk.Deck(
            map_style=None,  # Use default pydeck style
            initial_view_state=view_state,
            layers=[layer_rests, layer_user],
            tooltip={
                "html": "<b>{name}</b><br/>{address}<br/>⭐ {rating} / 5<br/>📍 {distance} km",
                "style": {"backgroundColor": "#333", "color": "white"}
            }
        ))
    
    # List restaurants in beautiful card layout
    st.markdown("---")
    st.markdown("### " + ("Restaurants recommandés" if lang == "fr" else "Recommended Restaurants" if lang == "en" else "Quán ăn gợi ý"))
    
    # Show restaurants in a 2-column grid
    col_left, col_right = st.columns(2)
    
    for idx, r in enumerate(sorted_rests):
        col = col_left if idx % 2 == 0 else col_right
        
        name = r.get("restaurant_name") or "Street food"
        addr = r.get("address", "")
        rating = r.get("rating", 4.5)
        dist = r.get("distance", 0.0)
        menu_items = ", ".join(r.get("menu", []))
        
        stars = "⭐" * int(rating) + ("½" if rating % 1 >= 0.5 else "")
        q = f"{name} {addr}"
        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q)}"
        
        with col:
            st.markdown(f"""
            <div style="
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            ">
                <h4 style="margin: 0 0 5px 0;">{name}</h4>
                <div style="font-size: 0.9em; margin-bottom: 8px; color: gray;">
                    <span>{stars} <b>{rating}</b>/5</span> | 
                    <span>📍 <b>{dist} km</b></span>
                </div>
                <p style="margin: 0 0 10px 0; font-size: 0.9em; line-height: 1.4;">
                    🏢 <i>{addr}</i>
                </p>
                <div style="margin-bottom: 12px; font-size: 0.85em;">
                    <a href="{maps_url}" target="_blank" style="text-decoration: none; color: #1E88E5; font-weight: bold;">
                        {L['maps_link_text']}
                    </a>
                </div>
                <div style="font-size: 0.85em; background-color: rgba(128, 128, 128, 0.05); padding: 8px; border-radius: 5px;">
                    🍜 {menu_items}
                </div>
            </div>
            """, unsafe_allow_html=True)
