import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- 1. 設定網頁 ---
st.set_page_config(page_title="雙人雲端喝水神器", page_icon="💧", layout="centered")

# --- 2. 連結 Google Sheets ---
URL = "https://docs.google.com/spreadsheets/d/13xNItqw0bSwdtc3__XH4WM3pNTeHdDYcd8DlsTVUHD8/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def load_cloud_data():
    try:
        df = conn.read(spreadsheet=URL, ttl=0)
        if "使用者" not in df.columns: df["使用者"] = "老公" 
        return df
    except:
        return pd.DataFrame(columns=["日期", "使用者", "體重", "目標水量", "實際喝水", "達成率"])

# --- 3. 身分選擇 ---
st.title("💧 雙人雲端喝水神器 Pro")
user = st.radio("請選擇使用者：", ["老公", "老婆"], horizontal=True)

if 'last_user' not in st.session_state or st.session_state.last_user != user:
    st.session_state.last_user = user
    st.session_state.initialized = False

# --- 4. 初始化 ---
today_str = datetime.now().strftime("%Y-%m-%d")

if not st.session_state.get('initialized', False):
    cloud_df = load_cloud_data()
    user_records = cloud_df[cloud_df["使用者"] == user]
    user_today = user_records[user_records["日期"] == today_str]
    
    st.session_state.count = int(user_today.iloc[-1]["實際喝水"]) if not user_today.empty else 0
    st.session_state.current_weight = float(user_records.iloc[-1]["體重"]) if not user_records.empty else (90.0 if user == "老公" else 50.0)
    st.session_state.initialized = True

# --- 5. 個人狀態與勳章系統 ---
st.subheader(f"📍 {user} 的個人狀態")
weight = st.number_input(f"{user} 今日體重 (kg)", value=st.session_state.current_weight, step=0.1, format="%.1f", key=f"w_{user}")
goal = int(weight * 45)

percent_val = (st.session_state.count / goal) if goal > 0 else 0
if percent_val >= 1.0:
    st.success(f"🏅 恭喜！{user} 已達成今日目標！你是飲水達人！")
    st.balloons()
else:
    st.info(f"💡 建議飲水量：{goal} cc")

st.progress(min(percent_val, 1.0))
st.write(f"### 目前已喝：{st.session_state.count} cc ({round(percent_val*100, 1)}%)")

# --- 6. 按鈕顏色 CSS ---
st.markdown("""
<style>
div.stColumn:nth-child(1) > div > div > div > button { background-color: #B0E0E6 !important; color: black !important; }
div.stColumn:nth-child(2) > div > div > div > button { background-color: #4682B4 !important; color: white !important; }
div.stColumn:nth-child(3) > div > div > div > button { background-color: #FFD700 !important; color: black !important; }
div.stColumn:nth-child(4) > div > div > div > button { background-color: #E0E0E0 !important; }
</style>
""", unsafe_allow_html=True)

# --- 7. 加水區 ---
custom_water = st.number_input("輸入自定義容量 (cc)", value=300, step=50)
c1, c2, c3, c4 = st.columns(4)
with c1: 
    if st.button("➕350"): st.session_state.count += 350; st.rerun()
with c2: 
    if st.button("➕500"): st.session_state.count += 500; st.rerun()
with c3: 
    if st.button(f"➕{custom_water}", key="c_btn"): st.session_state.count += custom_water; st.rerun()
with c4: 
    if st.button("🧹重置"): st.session_state.count = 0; st.rerun()

if st.button(f"🚀 同步 {user} 紀錄", use_container_width=True):
    with st.spinner('同步中...'):
        new_row = {"日期": today_str, "使用者": user, "體重": weight, "目標水量": goal, "實際喝水": st.session_state.count, "達成率": round(st.session_state.count/goal, 4) if goal > 0 else 0}
        df = load_cloud_data()
        df = df[~((df["日期"] == today_str) & (df["使用者"] == user))]
        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=URL, data=updated_df)
        st.success("同步成功！")
        st.session_state.current_weight = weight

# --- 8. 📊 週報表統計圖 (指定藍紅配色) ---
st.divider()
st.subheader("📈 最近 7 天飲水趨勢")
all_data = load_cloud_data()

if not all_data.empty:
    all_data["日期"] = pd.to_datetime(all_data["日期"])
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_df = all_data[all_data["日期"] >= seven_days_ago].sort_values("日期")
    
    if not recent_df.empty:
        # 關鍵修正：使用 color_discrete_map 指定顏色
        fig = px.line(recent_df, x="日期", y="實際喝水", color="使用者",
                      markers=True, title="老公 vs 老婆 飲水競賽",
                      labels={"實際喝水": "飲水量 (cc)"},
                      color_discrete_map={"老公": "#0000FF", "老婆": "#FF0000"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("尚無足夠數據生成圖表。")

# --- 9. 歷史清單 ---
with st.expander("查看所有歷史紀錄"):
    all_data_display = all_data.copy()
    all_data_display["達成率"] = pd.to_numeric(all_data_display["達成率"], errors='coerce') * 100
    st.data_editor(all_data_display, column_config={"達成率": st.column_config.ProgressColumn("達成率", format="%.1f%%", min_value=0, max_value=100)}, use_container_width=True, hide_index=True, disabled=True)

if st.button("🔄 刷新雲端資料"): st.rerun()
