# app.py

import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import re
import base64
import os
import requests
from services.orchestrator import run_pipeline
import json
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from services.chat_service import chat_with_ai, get_quick_answer
from online import search_places_python  # 新增：匯入 Google Places 搜尋功能

# 頁面配置
st.set_page_config(
    page_title="日本旅遊規劃助手",
    page_icon="🗾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式（保持原樣）
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    .title-container {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .title-container-with-bg {
        position: relative;
        background: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        text-align: center;
        margin-bottom: 2rem;
        overflow: hidden;
        min-height: 200px;
    }
    
    .title-container-with-bg .bg-image {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        opacity: 0.65;
        z-index: 1;
    }
    
    .title-container-with-bg .title-content {
        position: relative;
        z-index: 2;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .subtitle {
        color: #666;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    .input-card, .result-card, .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Google Places 景點卡片樣式 */
    .place-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .place-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .place-name {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .place-rating {
        color: #f59e0b;
        font-weight: bold;
    }
    
    .place-info {
        color: #666;
        font-size: 0.95rem;
        margin: 0.3rem 0;
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
        color: #444 !important;
        border: none;
        border-radius: 50px;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(161, 196, 253, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 15px rgba(161, 196, 253, 0.5);
        border-color: #ffb7c5;
    }
    
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    label {
        font-weight: 600;
        color: #333;
        font-size: 1rem;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #667eea;
    }
    
    .stAlert {
        border-radius: 10px;
    }
    
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    .card-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .destination-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .history-item {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 載入背景圖函數 ====================
def get_base64_image(image_path):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, image_path)
        with open(full_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        return None

# 初始化 session state
if "result" not in st.session_state:
    st.session_state.result = None
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "selected_destination" not in st.session_state:
    st.session_state.selected_destination = "東京"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_input_key" not in st.session_state:
    st.session_state.chat_input_key = 0
if "google_places" not in st.session_state:
    st.session_state.google_places = None

def split_daily_plans(text: str, days: int) -> dict:
    """只擷取真正的 Day1 ~ DayN 行程內容"""
    plans = {}
    if not text:
        return plans

    day_pattern = r"(Day\s*\d+|第\s*\d+\s*天)"
    lines = text.splitlines()
    current_day = None
    collecting = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(day_pattern, line):
            current_day = line.replace(" ", "")
            plans[current_day] = ""
            collecting = True
            continue
        if not collecting:
            continue
        if line.startswith("##") and "行程" not in line:
            break
        if current_day:
            plans[current_day] += line + "\n"

    filtered = {}
    for i in range(1, days + 1):
        key = f"Day{i}"
        if key in plans:
            filtered[key] = plans[key].strip()
    return filtered


def display_full_map(attractions, hotels, restaurants):
    """
    在地圖上顯示所有分類的點，並用顏色區分：
    景點(紅)、住宿(藍)、餐廳(橘)
    """
    # 找一個起始中心點（以景點的第一筆為優先）
    all_data = (attractions or []) + (hotels or []) + (restaurants or [])
    if not all_data:
        st.warning("暫無地點數據可顯示。")
        return

    # 設定中心點
    center_lat = all_data[0].get('lat', 35.6812)
    center_lng = all_data[0].get('lng', 139.7671)
    
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13, control_scale=True)

    # 定義顯示配置 [資料, 顏色, 圖示]
    configs = [
        (attractions, "red", "info-sign"),
        (hotels, "blue", "home"),
        (restaurants, "orange", "cutlery")
    ]

    for data_list, color, icon in configs:
        if data_list:
            for place in data_list:
                lat, lng = place.get('lat'), place.get('lng')
                if lat and lng:
                    popup_html = f"""
                        <div style='width: 180px; font-family: sans-serif;'>
                            <b style='color:#333;'>{place['name']}</b><br>
                            <span style='color:#f39c12;'>⭐ {place['rating']}</span><br>
                            <a href="{place['google_maps_link']}" target="_blank" style='text-decoration:none; color:#3498db;'>在地圖開啟</a>
                        </div>
                    """
                    folium.Marker(
                        location=[lat, lng],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=place['name'],
                        icon=folium.Icon(color=color, icon=icon)
                    ).add_to(m)

    st_folium(m, width="100%", height=450, returned_objects=[])
    
def display_google_place(place, index):
    """顯示單個 Google Places 景點資訊"""
    st.markdown(f"""
    <div class="place-card">
        <div class="place-name">📍 {index}. {place['name']}</div>
        <div class="place-rating">⭐ 評分：{place['rating']} ({place['user_ratings_total']} 則評論)</div>
        <div class="place-info">📍 地址：{place['address']}</div>
        <div class="place-info">📝 簡介：{place['summary']}</div>
        <div class="place-info">📞 電話：{place['phone']}</div>
        <div class="place-info">💰 價位：{place['price_level']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 顯示連結按鈕
    col1, col2 = st.columns(2)
    with col1:
        if place['website'] != '無網站':
            st.link_button("🔗 官方網站", place['website'], use_container_width=True)
    with col2:
        if place['google_maps_link']:
            st.link_button("🗺️ Google 地圖", place['google_maps_link'], use_container_width=True)

# ==================== 側邊欄 ====================
with st.sidebar:
    st.markdown("### 🎯 快速選項")
    
    st.markdown("#### 🔥 熱門目的地")
    popular_destinations = {
        "東京": "🗼", "大阪": "🏯", "京都": "⛩️", "北海道": "❄️",
        "沖繩": "🏝️", "福岡": "🍜", "名古屋": "🏰", "神戶": "🌃"
    }
    
    for dest, emoji in popular_destinations.items():
        if st.button(f"{emoji} {dest}", key=f"dest_{dest}"):
            st.session_state.selected_destination = dest
            st.rerun()
    
    
    
    st.markdown("---")
    
    st.markdown("#### 📜 搜尋歷史")
    if st.session_state.search_history:
        for i, history in enumerate(reversed(st.session_state.search_history[-5:])):
            with st.expander(f"🕒 {history['time']}"):
                st.write(f"📍 {history['location']}")
                st.write(f"💰 NT$ {history['budget']:,}")
                st.write(f"📅 {history['days']} 天")
                if st.button("重新載入", key=f"reload_{i}"):
                    st.session_state.selected_destination = history['location']
                    st.rerun()
    else:
        st.info("尚無搜尋記錄")
    
    st.markdown("---")
    
    # st.markdown("#### ⭐ 我的最愛")
    # if st.session_state.favorites:
    #     for fav in st.session_state.favorites:
    #         st.markdown(f"💖 {fav['location']} ({fav['days']}天)")
    # else:
    #     st.info("尚無收藏行程")

# ==================== 主要內容 ====================
torii_image = get_base64_image("assets/torii.png")

if torii_image:
    st.markdown(f"""
    <div class="title-container-with-bg">
        <div class="bg-image" style="background-image: url('data:image/png;base64,{torii_image}');"></div>
        <div class="title-content">
            <div class="main-title">🗾 日本旅遊規劃助手</div>
            <div class="subtitle">透過 AI 為您客製化專屬的日本之旅</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="title-container">
        <div class="main-title">🗾 日本旅遊規劃助手</div>
        <div class="subtitle">透過 AI 為您客製化專屬的日本之旅</div>
    </div>
    """, unsafe_allow_html=True)

# 分頁導航
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✈️ 規劃行程", "📊 預算計算", "🗺️ 熱門目的地", "ℹ️ 旅遊資訊", "💬 AI 客服"
])

# ==================== Tab 1: 規劃行程 ====================
with tab1:
    st.markdown('<div class="card-title">✈️ 規劃旅遊行程</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location = st.text_input("🗺️ 目的地", 
            value=st.session_state.selected_destination,
            placeholder="例如：東京、大阪、京都")
        start_date = st.date_input("📅 出發日期",
            value=datetime.now() + timedelta(days=30))
    
    with col2:
        budget = st.number_input("💰 預算（台幣/人）", min_value=0, value=20000, step=1000)
        end_date = st.date_input("📅 回程日期",
            value=datetime.now() + timedelta(days=33))
    
    with col3:
        people = st.number_input("👥 旅遊人數", min_value=1, value=2, step=1)
        accommodation = st.selectbox("🏨 住宿偏好",
            ["經濟型旅館", "商務旅館", "溫泉旅館", "高級飯店", "民宿"])
    
    days = (end_date - start_date).days + 1
    
    st.markdown("#### 🎯 旅遊偏好")
    col1, col2 = st.columns(2)
    with col1:
        default_query = st.session_state.get('selected_theme', "")
        query = st.text_input("💭 特殊需求", value=default_query, 
            placeholder="例如：親子旅遊、情侶之旅")
    with col2:
        interests = st.multiselect("🎨 興趣標籤",
            ["美食導向", "購物行程", "文化歷史", "自然風景", "戶外行程", "室內景點", "深度探索", "輕鬆隨走"],
            default=["美食導向", "室內景點"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 開始規劃行程", use_container_width=True):
            with st.spinner("正在為您規劃最佳行程..."):
                real_budget = budget if budget > 0 else None
                
                # 執行 AI 行程規劃
                st.session_state.result = run_pipeline(
                    location=location, budget=real_budget, days=days, people=people,
                    query=f"{query}，興趣：{', '.join(interests)}，住宿偏好：{accommodation}")
                
                # 同時執行 Google Places 搜尋
                try:
                    # 1. 搜尋景點 (使用原本的需求 query)
                    attr_query = f"日本 {location} {query} 旅遊景點"
                    st.session_state.google_places = search_places_python(attr_query, result_count=4)

                    # 2. 搜尋住宿 (針對住宿偏好)
                    hotel_query = f"日本 {location} {accommodation if accommodation else '飯店'}"
                    st.session_state.google_hotels = search_places_python(hotel_query, result_count=4)

                    # 3. 搜尋餐廳 (針對興趣標籤中的美食)
                    food_tags = ", ".join(interests) if interests else "必吃美食"
                    cafe_query = f"日本 {location} {food_tags} 餐廳"
                    st.session_state.google_restaurants = search_places_python(cafe_query, result_count=4)
                except Exception as e:
                    st.session_state.google_places = None
                    st.warning(f"Google Places 搜尋失敗：{e}")
                
                st.session_state.search_history.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "location": location, "budget": budget, "days": days,
                    "people": people, "query": query})
    
    if st.session_state.result:
        # st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🎯 規劃結果</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 總預算", f"NT$ {budget * people:,}")
        with col2:
            st.metric("📆 行程天數", f"{days} 天 {days-1} 夜")
        with col3:
            st.metric("👥 旅遊人數", f"{people} 人")
        
        
        
        st.markdown("### 🎊 AI 推薦行程")
        daily_plans = split_daily_plans(st.session_state.result["response"], days)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                    padding: 1.5rem; border-radius: 15px; border-left: 5px solid #667eea;">
            {st.session_state.result["response"]}
        </div>
        """, unsafe_allow_html=True)
        
        # ==================== 新增：Google Places 推薦景點 ====================
        if st.session_state.google_places:
            st.markdown("---")
            st.markdown("### 🌟 Google 推薦熱門景點")
            st.info(f"💡 以下為 Google 搜尋到的 {location} 熱門景點資訊")
            
            
           
        # 檢查是否有任何一類 Google 搜尋結果
        has_places = st.session_state.get('google_places')
        has_hotels = st.session_state.get('google_hotels')
        has_food = st.session_state.get('google_restaurants')

        if has_places or has_hotels or has_food:
            st.markdown("---")
            st.markdown(f"### 🗾 {location} 在地推薦資訊")
            
            # --- 1. 顯示整合式地圖 ---
            st.write("#### 📍 互動式分佈地圖")
            # 呼叫我們新寫的整合地圖函式 (傳入三種數據)
            display_full_map(
                st.session_state.get('google_places'),
                st.session_state.get('google_hotels'),
                st.session_state.get('google_restaurants')
            )
            
            st.markdown("<br>", unsafe_allow_html=True) # 增加間距

            # --- 2. 使用 Tabs 分類詳細資訊清單 ---
            st.write("#### 📋 詳細資訊清單")
            tab_attr, tab_hotel, tab_food = st.tabs(["🏛️ 必去景點", "🏨 推薦住宿", "🍱 在地美食"])

            with tab_attr:
                if has_places:
                    st.info(f"💡 以下為 Google 推薦的 {location} 熱門景點")
                    for idx, place in enumerate(st.session_state.google_places, 1):
                        display_google_place(place, idx)
                else:
                    st.write("⚠️ 暫無景點資訊，請嘗試重新規劃。")

            with tab_hotel:
                if has_hotels:
                    st.info(f"💡 以下為根據您的需求推薦的 {location} 住宿")
                    for idx, place in enumerate(st.session_state.google_hotels, 1):
                        display_google_place(place, idx)
                else:
                    st.write("⚠️ 暫無住宿資訊。")

            with tab_food:
                if has_food:
                    st.info(f"💡 以下為您推薦的 {location} 在地美食餐廳")
                    for idx, place in enumerate(st.session_state.google_restaurants, 1):
                        display_google_place(place, idx)
                else:
                    st.write("⚠️ 暫無餐廳資訊。")

        st.markdown('</div>', unsafe_allow_html=True)
        
#         st.markdown("---")
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             if st.button("💾 儲存行程"):
#                 data_to_save = {
#                     "location": location, "days": days, "people": people, "budget": budget,
#                     "start_date": start_date.strftime("%Y-%m-%d"),
#                     "end_date": end_date.strftime("%Y-%m-%d"),
#                     "accommodation": accommodation, "interests": interests,
#                     "daily_plan": daily_plans,
#                     "full_response": st.session_state.result["response"],
#                     "google_places": st.session_state.google_places  # 新增：儲存 Google Places 資訊
#                 }
#                 json_str = json.dumps(data_to_save, ensure_ascii=False, indent=2)
#                 st.download_button("📥 下載 JSON", data=json_str,
#                     file_name=f"japan_trip_{location}_{days}days_{datetime.now().strftime('%Y%m%d')}.json",
#                     mime="application/json")
        
#         with col2:
#             if st.button("⭐ 加入最愛"):
#                 st.session_state.favorites.append({
#                     "location": location, "days": days, "budget": budget,
#                     "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
#                 st.success("✅ 已加入最愛！")
        
#         with col3:
#             if st.button("📤 分享行程"):
#                 daily_text = ""
#                 for day, plan in daily_plans.items():
#                     daily_text += f"{day}\n{plan.strip()}\n\n"
                
#                 # 加入 Google Places 資訊到分享內容
#                 google_text = ""
#                 if st.session_state.google_places:
#                     google_text = "\n\n🌟 推薦景點：\n"
#                     for idx, place in enumerate(st.session_state.google_places, 1):
#                         google_text += f"{idx}. {place['name']} (⭐{place['rating']})\n"
#                         google_text += f"   {place['address']}\n\n"
                
#                 share_text = f"""🗾 日本旅遊行程分享

# 📍 地點：{location}
# 📆 天數：{days} 天
# 👥 人數：{people} 人
# 💰 預算：{"NT$" + format(budget, ",") if budget > 0 else "未提供"}
# 🏨 住宿：{accommodation}
# 🎨 興趣：{', '.join(interests)}

# ✨ 每天行程規劃：
# {daily_text}{google_text}"""
#                 st.text_area("📋 分享內容（可直接複製）", value=share_text.strip(), height=350)
#                 st.success("✅ 分享內容已產生！")
        
#         with col4:
#             if st.button("🔄 重新規劃"):
#                 st.session_state.result = None
#                 st.session_state.google_places = None
#                 st.rerun()
#     else:
        
#         st.info("👆 請填寫旅遊資訊後，點擊「開始規劃行程」按鈕")
#         st.markdown('</div>', unsafe_allow_html=True)

# ==================== Tab 2: 預算計算 ====================
with tab2:
    st.markdown("""
        <style>
            .budget-card {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                border-left: 5px solid #764ba2;
            }
            .metric-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                border-radius: 20px;
                color: white;
                text-align: center;
                box-shadow: 0 10px 20px rgba(118, 75, 162, 0.3);
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card-title">📊 智慧預算分析儀</div>', unsafe_allow_html=True)
    
    # 建立主要欄位：左邊輸入，右邊顯示結果
    main_col1, main_col2 = st.columns([1, 1], gap="large")
    
    with main_col1:
        st.markdown("#### ⚙️ 設定基準")
        c1, c2 = st.columns(2)
        with c1:
            calc_days = st.number_input("📅 旅行天數", min_value=1, value=5, step=1, key="calc_days")
        with c2:
            calc_people = st.number_input("👥 旅行人數", min_value=1, value=2, step=1, key="calc_people")
            
        st.markdown("#### 💰 預算分配 (單人)")
        # 使用 Expander 摺疊細項，讓介面更整潔
        with st.container():
            
            flight_budget = st.slider("✈️ 機票預算", 5000, 50000, 15000, 500, key="flight")
            hotel_budget = st.slider("🏨 每日住宿/人", 500, 10000, 2000, 500, key="hotel")
            food_budget = st.slider("🍱 每日餐飲/人", 500, 5000, 1500, 100, key="food")
            
            with st.expander("更多雜項設定"):
                transport_budget = st.number_input("🚇 每日交通/人", value=800, step=100, key="transport")
                activity_budget = st.number_input("🎡 每日活動/人", value=1000, step=100, key="activity")
                shopping_budget = st.number_input("🛍️ 購物總預算/人", value=5000, step=1000, key="shopping")
            st.markdown('</div>', unsafe_allow_html=True)

    with main_col2:
        # 計算數值
        total_stay = (hotel_budget + food_budget + transport_budget + activity_budget) * calc_days
        per_person_total = flight_budget + total_stay + shopping_budget
        total_group_budget = per_person_total * calc_people
        
        # 顯示大總結卡片
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); 
                padding: 30px; 
                border-radius: 20px; 
                color: #2c3e50; 
                text-align: center; 
                box-shadow: 0 10px 20px rgba(161, 196, 253, 0.3);
            ">
                <p style="font-size: 1.2rem; font-weight: 500; opacity: 0.9; margin-bottom: 0;">總預估支出</p>
                <h1 style="font-size: 3.5rem; margin: 0.5rem 0; color: #1a5276;">NT$ {total_group_budget:,}</h1>
                <div style="display: flex; justify-content: space-around; margin-top: 15px; border-top: 1px solid rgba(44, 62, 80, 0.1); padding-top: 15px;">
                    <div>
                        <p style="margin:0; opacity:0.7; font-size: 0.9rem;">每人平均</p>
                        <p style="font-size: 1.3rem; font-weight: bold; margin:0; color: #2980b9;">${per_person_total:,}</p>
                    </div>
                    <div>
                        <p style="margin:0; opacity:0.7; font-size: 0.9rem;">平均每日/人</p>
                        <p style="font-size: 1.3rem; font-weight: bold; margin:0; color: #2980b9;">${(per_person_total/calc_days):,.0f}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(" ")
        st.markdown("#### 📊 支出比例分析")
        
        # 準備數據
        items = {
            "✈️ 機票": flight_budget,
            "🏨 住宿": hotel_budget * calc_days,
            "🍱 餐飲": food_budget * calc_days,
            "其他 (交通/活動/購物)": (transport_budget + activity_budget) * calc_days + shopping_budget
        }
        
        # 視覺化進度條
        for label, amt in items.items():
            pct = (amt / per_person_total)
            st.write(f"**{label}** <span style='float:right; color:#764ba2;'>NT$ {amt:,}</span>", unsafe_allow_html=True)
            st.progress(pct)

    


# ==================== Tab 3: 熱門目的地 ====================
with tab3:
    st.markdown('<div class="card-title">🗺️ 日本熱門目的地導覽</div>', unsafe_allow_html=True)

    # 注入 CSS 確保右側所有城市圖片高度統一為 120px，並自動裁切比例
    st.markdown("""
        <style>
        [data-testid="stImage"] img {
            height: 120px;
            object-fit: cover;
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

    col_map, col_info = st.columns([1.2, 1], gap="medium")

    with col_map:
        img_base64 = get_base64_image("assets/JAPAN.jpg")
        if img_base64:
            map_html = f"""
            <style>
                .map-wrapper {{ position: relative; width: 100%; max-width: 500px; margin: 0 auto; }}
                .map-image {{ width: 100%; height: auto; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .m-btn {{
                    position: absolute; transform: translate(-50%, -50%);
                    padding: 6px 12px; background: white; border: 2px solid #ff4d4d;
                    border-radius: 15px; font-size: 13px; font-weight: bold;
                    color: #333; text-decoration: none; display: flex;
                    align-items: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                    z-index: 10; transition: all 0.2s ease;
                }}
                .m-btn:hover {{ background: #ff4d4d; color: white; transform: translate(-50%, -50%) scale(1.05); }}
            </style>
            <div class="map-wrapper">
                <img src="data:image/jpeg;base64,{img_base64}" class="map-image">
                <a href="https://www.gltjp.com/zh-hant/search/cse/#gsc.q=%E5%8C%97%E6%B5%B7%E9%81%93" target="_blank" class="m-btn" style="top: 15%; left: 78%;">❄️ 北海道</a>
                <a href="https://www.gltjp.com/zh-hant/search/cse/#gsc.q=%E6%9D%B1%E4%BA%AC" target="_blank" class="m-btn" style="top: 53%; left: 64%;">🗼 東京</a>
                <a href="https://www.gltjp.com/zh-hant/search/cse/#gsc.q=%E5%90%8D%E5%8F%A4%E5%B1%8B" target="_blank" class="m-btn" style="top: 58%; left: 62%;">🏰 名古屋</a>
                <a href="https://www.gltjp.com/zh-hant/search/cse/#gsc.q=%E4%BA%AC%E9%83%BD" target="_blank" class="m-btn" style="top: 58%; left: 50%;">⛩️ 京都</a>
                <a href="https://www.gltjp.com/zh-hant/search/cse/#gsc.q=%E5%A4%A7%E9%98%AA" target="_blank" class="m-btn" style="top: 63%; left: 47%;">🏯 大阪</a>
                <a href="https://www.gltjp.com/zh-hant/search/cse/#gsc.q=%E7%A6%8F%E5%B2%A1" target="_blank" class="m-btn" style="top: 66%; left: 32%;">🍜 福岡</a>
                <a href="https://www.gltjp.com/zh-hant/search/cse/#gsc.q=%E6%B2%96%E7%B9%A9" target="_blank" class="m-btn" style="top: 85%; left: 23%;">🏝️ 沖繩</a>
            </div>
            """
            components.html(map_html, height=550)
            st.info("💡 點擊地圖按鈕可快速跳轉至右側詳細介紹。")
        else:
            st.error("❌ 找不到 assets/JAPAN.jpg 檔案")

    with col_info:
        st.markdown("#### 🏮 城市深度探索")
        
        # 建立豐富化的城市資料清單
        city_data = [
            {
                "id": "Hokkaido", "name": "北海道", "icon": "❄️", "img": "assets/Hokkaido.jpg", 
                "desc": "**北國大地的自然詩篇。** 夏有富良野薰衣草花海，冬有二世谷頂級粉雪。除了函館百萬夜景，更不能錯過帝王蟹與鮮甜哈密瓜。"
            },
            {
                "id": "Tokyo", "name": "Tokyo 東京", "icon": "🗼", "img": "assets/Tokyo.jpg", 
                "desc": "**全球潮流與傳統的交界。** 在淺草寺感受江戶風情，轉身投入澀谷十字路口的繁華。這裡是購物天堂，也是擁有最多米其林星星的美食之都。"
            },
            {
                "id": "Nagoya", "name": "Nagoya 名古屋", "icon": "🏰", "img": "assets/Nagoya.jpg", 
                "desc": "**戰國歷史與工業核心。** 探訪壯麗的名古屋城，或前往吉卜力公園展開奇幻旅程。必嚐味噌炸豬排與獨特的鰻魚飯三吃。"
            },
            {
                "id": "Kyoto", "name": "Kyoto 京都", "icon": "⛩️", "img": "assets/Kyoto.jpg", 
                "desc": "**靜謐古樸的千年首都。** 漫步於金閣寺的靜謐身影與伏見稻荷的千本鳥居。這裡有最道地的懷石料理與茶道體驗，四季皆美。"
            },
            {
                "id": "Osaka", "name": "Osaka 大阪", "icon": "🏯", "img": "assets/Osaka.jpg", 
                "desc": "**活力十足的熱情商都。** 走訪宏偉的大阪城，在環球影城狂歡。道頓堀的看板燈火輝煌，章魚燒與大阪燒構築成「天下廚房」的美味印象。"
            },
            {
                "id": "Fukuoka", "name": "Fukuoka 福岡", "icon": "🍜", "img": "assets/Fukuoka.jpg", 
                "desc": "**緊鄰港灣的亞洲門戶。** 擁有充滿人情味的屋台文化與全日本最正宗的豚骨拉麵。博多運河城與太宰府天滿宮是深受旅客喜愛的必去景點。"
            },
            {
                "id": "Okinawa", "name": "Okinawa 沖繩", "icon": "🏝️", "img": "assets/Okinawa.jpg", 
                "desc": "**絕美碧海的度假天堂。** 探索美麗海水族館的巨型鯨鯊，漫步在古宇利島的白沙灘。體驗獨特的琉球王國歷史與清爽的海葡萄料理。"
            }
        ]

        # 渲染城市卡片
        for city in city_data:
            with st.container(border=True):
                c_img, c_txt = st.columns([1, 1.8])
                with c_img:
                    if os.path.exists(city["img"]):
                        st.image(city["img"], use_container_width=True)
                    else:
                        st.warning(f"缺少 {city['img']}")
                with c_txt:
                    st.markdown(f"<div id='{city['id']}'><b>{city['icon']} {city['name']}</b></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 14px; color: #555; line-height: 1.4;'>{city['desc']}</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
# ==================== Tab 4: 旅遊資訊 ====================
with tab4:
    
    st.markdown('<div class="card-title">ℹ️ 實用旅遊資訊</div>', unsafe_allow_html=True)
    
    info_tab1, info_tab2 = st.tabs(["📝 簽證資訊", "💱 匯率查詢"])
    
    with info_tab1:
    
        st.markdown("""
        <div style="background-color: #e3f2fd; padding: 20px; border-radius: 15px; border-left: 5px solid #2196f3; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #1565c0;">🇹🇼 台灣旅客赴日簽證與入境指南</h2>
            <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #546e7a;">適用持中華民國護照國民</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1], gap="medium")

        with col1:
            st.markdown("###  入境基本規定")
            st.markdown("""
                <style>
                .pink-box {
                    background-color: #fff0f3; /* 極淡粉色背景 */
                    padding: 1.5rem;
                    border-radius: 12px;
                    border-left: 5px solid #ff8fa3; /* 深粉色左側邊框 */
                    margin-bottom: 1rem;
                }
                .pink-box-content {
                    color: #a4133c; /* 深紅色文字，確保易讀性 */
                    font-size: 1.1rem;
                    margin: 0;
                }
                </style>
            """, unsafe_allow_html=True)

            
            st.markdown("""
            <div class="pink-box">
                <p class="pink-box-content">
                    <strong>90天免簽證!</strong><br><br>
                    以觀光、商務、探親等目的赴日，停留 90 天內不需申請簽證。
                </p>
            </div>
            """, unsafe_allow_html=True)
                        
            with st.expander("📌 必備文件清單", expanded=True):
                st.markdown("""
                - **有效護照**：效期建議 6 個月以上。
                - **離境機票**：回程或前往第三國之機票證明。
                - **住宿資訊**：第一晚飯店名稱、地址、電話。
                - **足夠經費**：雖然少查，但建議保留信用卡或現金備用。
                """)
            
            st.info("💡過海關時若被問及職業，建議據實以告，並準備好回程行程表。")

        with col2:
            st.markdown("###  數位工具:VJW")
            st.markdown("""
            **Visit Japan Web (VJW)**
            這是目前入境日本最重要的線上申請系統，整合了「入境審查」與「海關申報」。
            """)
            
            st.link_button("🌐 前往 Visit Japan Web 官網", "https://vjw-lp.digital.go.jp/zh-hant/")
            
            with st.container(border=True):
                st.markdown("""
                **VJW 登記三步驟：**
                1. 註冊帳號並登錄本人與同行家人資料。
                2. 登錄預計抵達日期與航班。
                3. 截圖產生的 **QR Code** (入境與海關各一個)。
                """)

        st.divider()

        # 下方橫向資訊區
        st.markdown("### 🔗 官方資訊連結")
        l_col1, l_col2, l_col3 = st.columns(3)
        
        with l_col1:
            st.markdown("""
            **🇯🇵 日本官方管道**
            - [日本交流協會(台北)](https://www.koryu.or.jp/tw/visa/taipei/)
            - [日本觀光局(JNTO)入境須知](https://www.japan.travel/tw/plan/visa-info/)
            """)
            
        with l_col2:
            st.markdown("""
            **🇹🇼 台灣官方管道**
            - [外交部領事事務局 - 日本資訊](https://www.boca.gov.tw/sp-foof-countrycp-03-31-01f70-02-1.html)
            - [駐日代表處(重要求助)](https://www.taiwanembassy.org/jp/index.html)
            """)
            
        with l_col3:
            st.markdown("""
            **🏥 健康與安全**
            - [Visit Japan Web 操作手冊](https://vjw-lp.digital.go.jp/zh-hant/howto/)
            - [日本漫遊 - 常用藥品與規定](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/kojinyunyu/index.html)
            """)

        # 警告區塊
        st.warning("""
        **⚠️ 注意事項**
        - **禁止從事有報酬活動**：免簽證期間嚴禁打工或任何領取薪水的商業活動。
        - **入境保險**：強烈建議投保包含海外突發疾病的旅遊險，日本醫療費用極高。
        - **海關規定**：菸酒類、貴重金屬（超過20萬日圓）需據實申報。
        """)
    
    with info_tab2:
        # 頂部標題自定義樣式
        st.markdown('<div class="card-title">💱 匯率換算</div>', unsafe_allow_html=True)

        # 定義匯率獲取函數 (內建 API 呼叫)
        def get_twd_jpy_rate():
            try:
                API_KEY = "a99af38c680c4cacbae3753952018062"
                url = "https://api.currencyfreaks.com/latest"
                params = {"apikey": API_KEY, "symbols": "TWD,JPY"}
                res = requests.get(url, params=params, timeout=10)
                if res.status_code != 200:
                    return 4.65  # 發生錯誤時回傳參考匯率
                data = res.json()
                rates = data["rates"]
                return float(rates["JPY"]) / float(rates["TWD"])
            except:
                return 4.65

        # 執行匯率抓取
        exchange_rate = get_twd_jpy_rate()
        jpy_to_twd = 1 / exchange_rate

        # --- 頂部匯率資訊看板 ---
        st.markdown(f"""
            <div style="background: #e3f2fd; padding: 20px; border-radius: 15px; border-left: 5px solid #2196f3; margin-bottom: 25px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin:0; color: #1565c0;">即時參考匯率</h4>
                        <p style="margin:0; font-size: 0.9rem; color: #546e7a;">🕒 更新時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.5rem; font-weight: bold; color: #1e88e5;">1 TWD ≈ {exchange_rate:.4f} JPY</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- 換算功能區 ---
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown("#### 🇹🇼 台幣 -> 日圓")
            twd_input = st.number_input("輸入台幣金額 (TWD)", min_value=0, value=10000, step=100, key="info_twd_in")
            
            # 使用淡藍色漸層卡片 (配合前述設計)
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); 
                            padding: 2rem; border-radius: 20px; color: #1a5276; text-align: center; 
                            box-shadow: 0 10px 20px rgba(161, 196, 253, 0.3); margin-top: 10px;">
                    <p style="margin: 0; font-size: 1.1rem; opacity: 0.8;">💴 您可換得約</p>
                    <h1 style="margin: 0.5rem 0; font-size: 3rem; color: #0d47a1;">¥ {twd_input * exchange_rate:,.0f}</h1>
                    <p style="margin: 0; font-size: 0.9rem; font-weight: bold;">( 匯率基準：{exchange_rate:.4f} )</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("#### 🇯🇵 日圓 -> 台幣")
            jpy_input = st.number_input("輸入日圓金額 (JPY)", min_value=0, value=10000, step=1000, key="info_jpy_in")
            
            # 使用灰色調漸層區分反向換算
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                            padding: 2rem; border-radius: 20px; color: #2c3e50; text-align: center; 
                            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05); margin-top: 10px;">
                    <p style="margin: 0; font-size: 1.1rem; opacity: 0.8;">🇹🇼 折合台幣約</p>
                    <h1 style="margin: 0.5rem 0; font-size: 3rem; color: #2c3e50;">$ {jpy_input * jpy_to_twd:,.0f}</h1>
                    <p style="margin: 0; font-size: 0.9rem; font-weight: bold;">( 匯率基準：{jpy_to_twd:.4f} )</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 下方提示區
        with st.expander("💡 換匯小建議"):
            st.markdown(f"""
            1. **分批換匯**：日幣匯率波動大，建議分批購入平攤成本。
            2. **雙幣卡優勢**：若有雙幣信用卡，可直接刷日幣幣別扣款，避開即時匯率風險。
            3. **ATM 提領**：日本 7-11 等便利商店 ATM 支援海外金融卡提領，急需現金時很方便。
            ---
            *註：本工具顯示之匯率僅供參考，實際換匯請依銀行公告之「現鈔賣出」匯率為準。*
            """)

        st.markdown('</div>', unsafe_allow_html=True)

# ==================== Tab 5: AI 客服（新功能）====================
with tab5:
    st.markdown('<div class="card-title">💬 AI 旅遊顧問</div>', unsafe_allow_html=True)
    
    st.info("💡 有任何日本旅遊問題均可在此尋問!")
    
    # 常見問題快捷按鈕
    st.markdown("#### 🔥 熱門問題")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 簽證問題", use_container_width=True, key="quick_visa"):
            # 加入使用者問題
            st.session_state.chat_history.append({
                "role": "user",
                "content": "台灣人去日本需要簽證嗎？"
            })
            # 加入快速回答
            answer = get_quick_answer("visa")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })
            st.rerun()
    
    with col2:
        if st.button("💱 換匯建議", use_container_width=True, key="quick_currency"):
            st.session_state.chat_history.append({
                "role": "user",
                "content": "在哪裡換日圓最划算？"
            })
            answer = get_quick_answer("currency")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })
            st.rerun()
    
    with col3:
        if st.button("📱 網路方案", use_container_width=True, key="quick_wifi"):
            st.session_state.chat_history.append({
                "role": "user",
                "content": "日本上網該買 SIM 卡還是租 WiFi 機？"
            })
            answer = get_quick_answer("wifi")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })
            st.rerun()
    
    with col4:
        if st.button("🎒 行李建議", use_container_width=True, key="quick_luggage"):
            st.session_state.chat_history.append({
                "role": "user",
                "content": "去日本該準備什麼行李？"
            })
            answer = get_quick_answer("luggage")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })
            st.rerun()
    
    st.markdown("---")
    
    # 顯示聊天歷史
    st.markdown("#### 💭 對話記錄")
    
    # 聊天容器（使用 container 讓對話可以捲動）
    chat_container = st.container()
    
    with chat_container:
        if len(st.session_state.chat_history) == 0:
            st.info("您好！我是日本旅遊 AI 顧問，有任何問題都可以問我喔！")
        else:
            for i, msg in enumerate(st.session_state.chat_history):
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; 
                                margin: 0.5rem 0; text-align: right; border-left: 4px solid #2196F3;">
                        <strong>👤 您</strong><br/>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #f5f5f5; padding: 1rem; border-radius: 10px; 
                                margin: 0.5rem 0; border-left: 4px solid #667eea;">
                        <strong>🤖 AI 顧問</strong><br/>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
    
    # 如果有對話，顯示清除按鈕
    if len(st.session_state.chat_history) > 0:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            if st.button("🗑️ 清除對話", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        with col3:
            if st.button("📥 匯出對話", use_container_width=True):
                # 組合對話內容
                chat_text = "=== 日本旅遊 AI 顧問對話記錄 ===\n\n"
                for msg in st.session_state.chat_history:
                    role = "您" if msg["role"] == "user" else "AI 顧問"
                    chat_text += f"{role}：\n{msg['content']}\n\n"
                chat_text += f"\n匯出時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                st.download_button(
                    label="📥 下載對話記錄",
                    data=chat_text,
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    st.markdown("---")
    
    # 輸入區域
    st.markdown("#### ✍️ 提問")
    
    # 使用表單來處理輸入
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "請輸入您的問題...",
            height=100,
            placeholder="例如：東京三日遊推薦行程、大阪必吃美食、京都賞楓最佳時間...",
            key=f"chat_input_{st.session_state.chat_input_key}"
        )
        
        col1, col2 = st.columns([4, 1])
        with col2:
            submit_button = st.form_submit_button("傳送", use_container_width=True)
    
    # 處理發送
    if submit_button and user_input and user_input.strip():
        # 加入使用者訊息
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input.strip()
        })
        
        # 顯示思考中
        with st.spinner("🤔 AI 正在思考中..."):
            try:
                # 呼叫 AI 取得回應
                ai_response = chat_with_ai(
                    user_message=user_input.strip(),
                    chat_history=st.session_state.chat_history[:-1]  # 不包含剛加入的使用者訊息
                )
                
                # 加入 AI 回應
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                # 更新輸入框 key 以清空內容
                st.session_state.chat_input_key += 1
                
                # 重新載入頁面以顯示新訊息
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
                st.info("💡 請稍後再試，或點擊上方的快捷問題按鈕")
    
    # 使用提示
    with st.expander("💡 使用提示"):
        st.markdown("""
        ### 如何使用 AI 旅遊顧問？
        
        1. **快速提問**：點擊上方的熱門問題按鈕
        2. **自由提問**：在下方輸入框輸入任何問題
        3. **持續對話**：AI 會記住對話內容，可以追問
        4. **清除對話**：點擊「清除對話」開始新的話題
        5. **匯出記錄**：可以下載對話記錄留存
        
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
# 頁腳
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: black; padding: 1rem;">
    <p style="font-size: 1.2rem;">🌸 日本旅遊 AI 助手 | 讓旅行更簡單 🌸</p>
    <p style="font-size: 0.9rem; opacity: 0.8;">theory of computation</p>
    
</div>
""", unsafe_allow_html=True)
