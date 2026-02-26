import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. 設定網頁 ---
st.set_page_config(page_title="雙人雲端喝水管理員", page_icon="💧", layout="centered")

# --- 2. 連結 Google Sheets ---
URL = "https://docs.google.com/spreadsheets/d/13xNItqw0bSwdtc3__XH4WM3pNTeHdDYcd8DlsTVUHD8/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def load_cloud_data():
    try:
        return conn.read(spreadsheet=URL, ttl=0)
    except:
        return pd.DataFrame(columns=["日期", "使用者", "體重", "目標水量", "實際喝水", "達成率"])

# --- 3. 身分選擇 ---
st.title("💧 雙人雲端喝水系統")
user = st.radio("請選擇使用者：", ["老公", "老婆"], horizontal=True)

# 當切換使用者時，重置初始化狀態以重新讀取資料
if 'last_user' not in st.session_state or st.session_state.last_user != user:
    st.session_state.last_user = user
    st.session_state.initialized = False

# --- 4. 初始化：根據身分讀取進度 ---
today_str = datetime.now().strftime("%Y-%m-%d")

if not st.session_state.get('initialized', False):
    cloud_df = load_cloud_data()
    # 篩選今天的日期且是當前選擇的使用者
    user_today = cloud_df[(cloud_df["日期"] == today_str) & (cloud_df["使用者"] == user)]
    
    if not user_today.empty:
        st.session_state.count = int(user_today.iloc[-1]["實際喝水"])
    else:
        st.session_state.count = 0
    st.session_state.initialized = True

# --- 5. 個人狀態設定 ---
# 設定預設體重：老公 90, 老婆 50 (老婆體重可自行修改)
default_weight = 90.0 if user == "老公" else 50.0

st.subheader(f"📍 {user} 的個人狀態")
weight = st.number_input(f"{user} 今日體重 (kg)", value=default_weight, step=0.1, key=f"weight_{user}")
goal = int(weight * 45)
st.info(f"💡 {user} 的建議飲水量：{goal} cc")

# 喝水進度計算
display_percent = round((st.session_state.count / goal) * 100, 1) if goal > 0 else 0
st.progress(min(st.session_state.count / goal, 1.0) if goal > 0 else 0)
st.write(f"### 目前已喝：{st.session_state.count} cc ({display_percent}%)")

# --- 6. 按鈕顏色 CSS ---
st.markdown("""
<style>
div.stColumn:nth-child(1) > div > div > div > button { background-color: #B0E0E6 !important; color: black !important; border: none !important; }
div.stColumn:nth-child(2) > div > div > div > button { background-color: #4682B4 !important; color: white !important; border: none !important; }
div.stColumn:nth-child(3) > div > div > div > button { background-color: #FFD700 !important; color: black !important; border: none !important; }
div.stColumn:nth-child(4) > div > div > div > button { background-color: #E0E0E0 !important; color: black !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 7. 加水區 ---
st.divider()
custom_water = st.number_input("輸入自定義容量 (cc)", value=300, step=50)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("➕350"): 
        st.session_state.count += 350
        st.rerun()
with c2:
    if st.button("➕500"): 
        st.session_state.count += 500
        st.rerun()
with c3:
    if st.button(f"➕{custom_water}", key="custom_btn"): 
        st.session_state.count += custom_water
        st.rerun()
with c4:
    if st.button("🧹重置"): 
        st.session_state.count = 0
        st.rerun()

# --- 8. 儲存到雲端 ---
if st.button(f"🚀 同步 {user} 的紀錄到雲端", use_container_width=True):
    with st.spinner('同步中...'):
        new_row = {
            "日期": today_str,
            "使用者": user,
            "體重": weight,
            "目標水量": goal,
            "實際喝水": st.session_state.count,
            "達成率": round(st.session_state.count / goal, 4) if goal > 0 else 0
        }
        existing_data = load_cloud_data()
        # 移除當天、當前使用者的舊紀錄，避免重複
        if not existing_data.empty:
            mask = (existing_data["日期"] == today_str) & (existing_data["使用者"] == user)
            existing_data = existing_data[~mask]
        
        updated_data = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=URL, data=updated_data)
        st.success(f"{user} 的紀錄同步成功！🎈")

# --- 9. 雲端歷史紀錄 ---
st.divider()
st.subheader("📊 雲端歷史紀錄 (全體)")
cloud_history = load_cloud_data()

if not cloud_history.empty:
    cloud_history["達成率"] = pd.to_numeric(cloud_history["達成率"], errors='coerce') * 100
    st.data_editor(
        cloud_history,
        column_config={
            "達成率": st.column_config.ProgressColumn("達成率", format="%.1f%%", min_value=0, max_value=100),
            "使用者": st.column_config.TextColumn("使用者"),
        },
        use_container_width=True, hide_index=True, disabled=True
    )

if st.button("🔄 刷新雲端資料"):
    st.rerun()
