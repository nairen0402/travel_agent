# app.py

import streamlit as st
import re
import base64
import os
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
    
    st.markdown("#### 🎨 旅遊主題")
    themes = ["美食之旅", "文化體驗", "購物天堂", "溫泉度假", 
              "賞櫻行程", "滑雪之旅", "親子旅遊", "浪漫之旅"]
    selected_theme = st.selectbox("選擇主題", themes, key="theme_select")
    
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
    
    st.markdown("#### ⭐ 我的最愛")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            st.markdown(f"💖 {fav['location']} ({fav['days']}天)")
    else:
        st.info("尚無收藏行程")

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
        query = st.text_input("💭 特殊需求", value=selected_theme, 
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
                    search_query = f"日本{location}旅遊景點" # 加上「日本」前綴
                    st.session_state.google_places = search_places_python(search_query)
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
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔄 系統狀態", st.session_state.result["state"])
        with col2:
            st.metric("💰 總預算", f"NT$ {budget * people:,}")
        with col3:
            st.metric("📆 行程天數", f"{days} 天 {days-1} 夜")
        with col4:
            st.metric("👥 旅遊人數", f"{people} 人")
        
        st.markdown("---")
        st.markdown("### 💡 系統分析")
        st.info(st.session_state.result["reason"])
        
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
            
            for idx, place in enumerate(st.session_state.google_places, 1):
                display_google_place(place, idx)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 儲存行程"):
                data_to_save = {
                    "location": location, "days": days, "people": people, "budget": budget,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "accommodation": accommodation, "interests": interests,
                    "daily_plan": daily_plans,
                    "full_response": st.session_state.result["response"],
                    "google_places": st.session_state.google_places  # 新增：儲存 Google Places 資訊
                }
                json_str = json.dumps(data_to_save, ensure_ascii=False, indent=2)
                st.download_button("📥 下載 JSON", data=json_str,
                    file_name=f"japan_trip_{location}_{days}days_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json")
        
        with col2:
            if st.button("⭐ 加入最愛"):
                st.session_state.favorites.append({
                    "location": location, "days": days, "budget": budget,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                st.success("✅ 已加入最愛！")
        
        with col3:
            if st.button("📤 分享行程"):
                daily_text = ""
                for day, plan in daily_plans.items():
                    daily_text += f"{day}\n{plan.strip()}\n\n"
                
                # 加入 Google Places 資訊到分享內容
                google_text = ""
                if st.session_state.google_places:
                    google_text = "\n\n🌟 推薦景點：\n"
                    for idx, place in enumerate(st.session_state.google_places, 1):
                        google_text += f"{idx}. {place['name']} (⭐{place['rating']})\n"
                        google_text += f"   {place['address']}\n\n"
                
                share_text = f"""🗾 日本旅遊行程分享

📍 地點：{location}
📆 天數：{days} 天
👥 人數：{people} 人
💰 預算：{"NT$" + format(budget, ",") if budget > 0 else "未提供"}
🏨 住宿：{accommodation}
🎨 興趣：{', '.join(interests)}

✨ 每天行程規劃：
{daily_text}{google_text}"""
                st.text_area("📋 分享內容（可直接複製）", value=share_text.strip(), height=350)
                st.success("✅ 分享內容已產生！")
        
        with col4:
            if st.button("🔄 重新規劃"):
                st.session_state.result = None
                st.session_state.google_places = None
                st.rerun()
    else:
        
        st.info("👆 請填寫旅遊資訊後，點擊「開始規劃行程」按鈕")
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== Tab 2: 預算計算 ====================
with tab2:
    
    st.markdown('<div class="card-title">📊 預算計算機</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 預算項目")
        flight_budget = st.number_input("✈️ 機票（每人）", value=15000, step=1000, key="flight")
        hotel_budget = st.number_input("🏨 住宿（每晚/人）", value=2000, step=500, key="hotel")
        food_budget = st.number_input("🍱 餐飲（每天/人）", value=1500, step=500, key="food")
        transport_budget = st.number_input("🚇 交通（每天/人）", value=800, step=100, key="transport")
        activity_budget = st.number_input("🎡 活動（每天/人）", value=1000, step=500, key="activity")
        shopping_budget = st.number_input("🛍️ 購物（總計/人）", value=5000, step=1000, key="shopping")
    
    with col2:
        st.markdown("#### 📈 預算分析")
        calc_days = st.number_input("計算天數", value=5, step=1, key="calc_days")
        calc_people = st.number_input("計算人數", value=2, step=1, key="calc_people")
        
        # 計算總預算
        per_person_total = (
            flight_budget + 
            (hotel_budget * calc_days) +
            (food_budget * calc_days) +
            (transport_budget * calc_days) +
            (activity_budget * calc_days) +
            shopping_budget
        )
        
        total_budget = per_person_total * calc_people
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; color: white; text-align: center;">
            <h2>💰 總預算</h2>
            <h1 style="font-size: 3rem; margin: 1rem 0;">NT$ {total_budget:,}</h1>
            <p>每人：NT$ {per_person_total:,}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 預算分布
        st.markdown("#### 📊 預算分布")
        budget_data = {
            "✈️ 機票": flight_budget,
            "🏨 住宿": hotel_budget * calc_days,
            "🍱 餐飲": food_budget * calc_days,
            "🚇 交通": transport_budget * calc_days,
            "🎡 活動": activity_budget * calc_days,
            "🛍️ 購物": shopping_budget
        }
        
        for item, amount in budget_data.items():
            percentage = (amount / per_person_total) * 100
            st.write(f"*{item}*: NT$ {amount:,} ({percentage:.1f}%)")
            st.progress(percentage / 100)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== Tab 3: 熱門目的地 ====================
with tab3:
    st.markdown('<div class="card-title">🗺️ 日本熱門目的地導覽</div>', unsafe_allow_html=True)

    img_base64 = get_base64_image("assets/JAPAN.jpg")

    if img_base64:
        

        
        map_html = f"""
        <style>
            .map-wrapper {{
                position: relative;
                display: inline-block;
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
            }}
            .map-image {{
                width: 100%;
                height: auto;
                display: block;
            }}
            .m-btn {{
                position: absolute;
                transform: translate(-50%, -50%);
                padding: 6px 12px;
                background: white;
                border: 2px solid #ff4d4d;
                border-radius: 15px;
                font-size: 13px;
                font-weight: bold;
                color: #333;
                text-decoration: none; /* 移除超連結下劃線 */
                display: flex;
                align-items: center;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                white-space: nowrap;
                z-index: 10;
                transition: all 0.2s ease;
            }}
            .m-btn:hover {{
                background: #ff4d4d;
                color: white;
                transform: translate(-50%, -50%) scale(1.05);
            }}
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

        
        components.html(map_html, height=750)
        
        st.info("💡 點擊地圖上的城市按鈕，將在新分頁開啟該地區的詳細旅遊資訊網站。")
    else:
        st.error("❌ 找不到 assets/JAPAN.jpg 檔案")
# ==================== Tab 4: 旅遊資訊 ====================
with tab4:
    
    st.markdown('<div class="card-title">ℹ️ 實用旅遊資訊</div>', unsafe_allow_html=True)
    
    info_tab1, info_tab2 = st.tabs(["📝 簽證資訊", "💱 匯率查詢"])
    
    with info_tab1:
        st.markdown("""
        ### 🇹🇼 台灣旅客赴日簽證規定
        
        #### ✅ 免簽證入境
        - **停留期限**：90 天以內免簽證
        - **適用對象**：持有效台灣護照之國民
        
        #### 📋 入境所需文件
        1. 有效護照（效期需超過停留天數）
        2. 回程機票或離境機票
        3. 足夠旅費證明
        4. Visit Japan Web 登錄（建議事先完成）
        
        #### ⚠️ 注意事項
        - 不可從事有報酬的活動
        - 入境時可能被要求出示住宿證明
        - 建議攜帶旅遊保險證明
        
        #### 📱 入境數位化工具
        - **Visit Japan Web**：整合入境審查、海關申報
        - 建議於出發前完成線上登記
        
        #### 🏥 健康相關
        - 目前無強制疫苗接種要求
        - 建議投保旅遊平安險及醫療險
        """)
    
    with info_tab2:
        st.markdown("### 💱 即時匯率計算器（台幣 ↔ 日圓）")

        # API 打開註解，暫時不使用匯率功能
        
        
        # try:
        #     exchange_rate = get_twd_jpy_rate()
        #     st.success(f"即時匯率：1 TWD ≈ {exchange_rate:.4f} JPY")
        # except Exception as e:
        #     st.error("⚠️ 無法取得即時匯率")
        #     st.exception(e)

        # col1, col2 = st.columns(2)

        # with col1:
        #     st.markdown("#### 台幣 → 日圓")
        #     twd_amount = st.number_input(
        #         "輸入台幣金額",
        #         value=10000,
        #         step=1000
        #     )

        #     if exchange_rate:
        #         jpy_amount = twd_amount * exchange_rate

        #         st.markdown(f"""
        #         <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        #                     padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
        #             <h3>💴 約等於</h3>
        #             <h1 style="font-size: 2.5rem;">¥ {jpy_amount:,.0f}</h1>
        #         </div>
        #         """, unsafe_allow_html=True)

        # with col2:
        #     if exchange_rate:
        #         st.info(f"""
        #       *📈 即時匯率資訊***
                
        #         🔄 1 TWD = {exchange_rate:.4f} JPY  
        #         🔄 1 JPY = {1/exchange_rate:.4f} TWD  

        #         🕒 更新時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}

        #         ⚠️實際換匯以銀行公告為準*
        #         """)

    
    
    
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
