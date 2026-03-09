import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta  # 確保有導入 timedelta
import plotly.express as px

# --- 1. 設定網頁與背景 ---
st.set_page_config(page_title="家庭健康管理神器", page_icon="❤️", layout="centered")

# 背景照片
bg_img_url = "https://lh3.googleusercontent.com/pw/AP1GczPQAeEyydw0HzXGq3cyXWggu8_yrupGiYDBYBhcYhtvubDIdpS5pG7NNYc1R59y57HU6SspjCl4BGwNxdTkWxni3jrDHqcbFNaysEdDR8ntrB2vmCGm=w2400"

st.markdown(f"""
<style>
.stApp {{ background-image: url("{bg_img_url}"); background-size: cover; background-position: center; background-attachment: fixed; }}
.main .block-container {{ background-color: rgba(255, 255, 255, 0.9); padding: 30px; border-radius: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
[data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.8); }}
</style>
""", unsafe_allow_html=True)

# --- 2. 連結 Google Sheets ---
URL = "https://docs.google.com/spreadsheets/d/13xNItqw0bSwdtc3__XH4WM3pNTeHdDYcd8DlsTVUHD8/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(spreadsheet=URL, ttl=0)
        for col in ["類別", "使用者", "日期", "實際喝水", "達成率", "高壓", "低壓", "時間段"]:
            if col not in df.columns: df[col] = None
        return df
    except:
        return pd.DataFrame()

# --- 3. 時區修正邏輯 (台灣時區 UTC+8) ---
# 強制抓取台灣當前日期
tw_now = datetime.utcnow() + timedelta(hours=8)
today_str = tw_now.strftime("%Y-%m-%d")

# --- 4. 側邊欄選單 ---
with st.sidebar:
    st.title("🏠 健康選單")
    page = st.selectbox("切換功能：", ["💧 喝水紀錄", "❤️ 血壓紀錄"])
    st.divider()
    user = st.radio("選擇使用者：", ["老公", "老婆"], horizontal=True)

# ==================== 頁面 A：喝水紀錄 ====================
if page == "💧 喝水紀錄":
    st.title(f"💧 {user} 喝水追蹤")
    
    df = load_data()
    user_today = df[(df["日期"] == today_str) & (df["使用者"] == user) & (df["類別"] == "喝水")]
    
    if 'water_count' not in st.session_state or st.session_state.get('last_user_w') != user:
        st.session_state.water_count = int(user_today.iloc[-1]["實際喝水"]) if not user_today.empty else 0
        st.session_state.last_user_w = user

    user_records = df[(df["使用者"] == user) & (df["類別"] == "喝水")]
    last_weight = float(user_records.iloc[-1]["體重"]) if not user_records.empty else (90.0 if user == "老公" else 50.0)
    weight = st.number_input("今日體重 (kg)", value=last_weight, step=0.1, format="%.1f")
    goal = int(weight * 40)
    
    percent = (st.session_state.water_count / goal) if goal > 0 else 0
    st.progress(min(percent, 1.0))
    st.write(f"### 目前已喝：{st.session_state.water_count} cc ({round(percent*100, 1)}%)")

    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("➕350"): st.session_state.water_count += 350; st.rerun()
    with c2: 
        if st.button("➕500"): st.session_state.count = st.session_state.water_count + 500; st.session_state.water_count += 500; st.rerun()
    with c3: 
        custom = st.number_input("自定義", value=300, step=50, label_visibility="collapsed")
        if st.button(f"➕{custom}", key="custom_w_btn"): st.session_state.water_count += custom; st.rerun()
    with c4: 
        if st.button("🧹重置"): st.session_state.water_count = 0; st.rerun()

    if st.button("🚀 同步喝水紀錄", use_container_width=True):
        new_row = {"日期": today_str, "使用者": user, "體重": weight, "目標水量": goal, "實際喝水": st.session_state.water_count, "達成率": round(percent, 4), "類別": "喝水"}
        df = df[~((df["日期"] == today_str) & (df["使用者"] == user) & (df["類別"] == "喝水"))]
        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=URL, data=updated_df)
        st.success(f"同步成功！日期：{today_str} 🎈")

    st.divider()
    st.subheader("📊 喝水歷史紀錄")
    if not df.empty:
        water_df = df[df["類別"] == "喝水"].copy()
        water_df["達成率"] = pd.to_numeric(water_df["達成率"], errors='coerce') * 100
        st.data_editor(
            water_df[["日期", "使用者", "實際喝水", "達成率"]].sort_values("日期", ascending=False),
            column_config={"達成率": st.column_config.ProgressColumn("達成率", format="%.1f%%", min_value=0, max_value=100)},
            use_container_width=True, hide_index=True, disabled=True
        )

# ==================== 頁面 B：血壓紀錄 ====================
elif page == "❤️ 血壓紀錄":
    st.title(f"❤️ {user} 血壓日誌")
    st.info(f"📅 記錄日期：{today_str}") # 讓使用者確認日期
    period = st.radio("紀錄時段：", ["早晨", "夜晚"], horizontal=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: sys = st.number_input("高壓 (SYS)", 80, 200, 120)
    with col2: dia = st.number_input("低壓 (DIA)", 40, 130, 80)
    with col3: pulse = st.number_input("心跳", 40, 200, 70)

    if st.button("🚀 同步血壓紀錄", use_container_width=True):
        new_row = {"日期": today_str, "使用者": user, "時間段": period, "高壓": sys, "低壓": dia, "心跳": pulse, "類別": "血壓"}
        df = load_data()
        df = df[~((df["日期"] == today_str) & (df["使用者"] == user) & (df["時間段"] == period) & (df["類別"] == "血壓"))]
        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=URL, data=updated_df)
        st.success(f"血壓已存檔！日期：{today_str}")

    st.divider()
    st.subheader("📊 血壓歷史紀錄表")
    df = load_data()
    if not df.empty:
        bp_df = df[(df["類別"] == "血壓") & (df["使用者"] == user)].sort_values(["日期", "時間段"], ascending=False)
        st.dataframe(bp_df[["日期", "時間段", "高壓", "低壓", "心跳"]], use_container_width=True, hide_index=True)

if st.button("🔄 刷新數據"): st.rerun()
