import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 設定網頁 ---
st.set_page_config(page_title="雲端喝水管理員", page_icon="☁️")
st.title("☁️ 雲端同步喝水系統")

# --- 連結 Google Sheets ---
# 使用 Secrets 中的設定，URL 盡量從 Secrets 讀取更安全
URL = "https://docs.google.com/spreadsheets/d/13xNItqw0bSwdtc3__XH4WM3pNTeHdDYcd8DlsTVUHD8/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取雲端資料的函式
def load_cloud_data():
    try:
        # ttl=0 代表不使用暫存，每次都抓最新的資料
        return conn.read(spreadsheet=URL, ttl=0)
    except:
        return pd.DataFrame(columns=["日期", "體重", "目標水量", "實際喝水", "達成率"])

# --- 初始化：同步雲端數據到 App ---
today_str = datetime.now().strftime("%Y-%m-%d")

# 第一次執行或重新整理時，從雲端抓取今天的進度
if 'initialized' not in st.session_state:
    cloud_df = load_cloud_data()
    if not cloud_df.empty and today_str in cloud_df["日期"].values:
        # 找到今天那一行，並取得「實際喝水」的數值
        today_record = cloud_df[cloud_df["日期"] == today_str].iloc[-1]
        st.session_state.count = int(today_record["實際喝水"])
    else:
        st.session_state.count = 0
    st.session_state.initialized = True

# --- 介面邏輯 ---
st.subheader("📍 個人狀態")
weight = st.number_input("今日體重 (kg)", value=90.0, step=0.1)
goal = int(weight * 45)
st.info(f"💡 建議飲水量：{goal} cc")

# 喝水進度計算
display_percent = round((st.session_state.count / goal) * 100, 1) if goal > 0 else 0
st.progress(min(st.session_state.count / goal, 1.0) if goal > 0 else 0)
st.write(f"### 目前已喝：{st.session_state.count} cc ({display_percent}%)")

# 按鈕區
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("➕250cc"): 
        st.session_state.count += 250
        st.rerun() # 點擊後立即更新畫面
with c2:
    if st.button("➕500cc"): 
        st.session_state.count += 500
        st.rerun()
with c3:
    if st.button("🧹重置"): 
        st.session_state.count = 0
        st.rerun()

# --- 儲存到雲端 ---
if st.button("🚀 同步到 Google 試算表"):
    with st.spinner('正在同步中...'):
        new_row = {
            "日期": today_str,
            "體重": weight,
            "目標水量": goal,
            "實際喝水": st.session_state.count,
            "達成率": f"{display_percent}%"
        }
        
        # 讀取現有資料
        existing_data = load_cloud_data()
        
        # 移除舊的今日紀錄（避免重複），更新為新的
        if not existing_data.empty:
            existing_data = existing_data[existing_data["日期"] != today_str]
        
        updated_data = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
        
        # 寫回 Google Sheets
        conn.update(spreadsheet=URL, data=updated_data)
        st.success("同步成功！手機與 PC 數據已一致。")

# 顯示雲端現有資料
st.divider()
st.subheader("📊 雲端歷史紀錄")
if st.button("🔄 刷新雲端資料"):
    st.rerun()

cloud_history = load_cloud_data()

# 修改後的顯示方式：
cloud_history = load_cloud_data()

# 使用 column_config 來格式化顯示百分比
st.data_editor(
    cloud_history,
    column_config={
        "達成率": st.column_config.ProgressColumn(
            "達成率",
            help="每日喝水達成率",
            format="%.1f%%",
            min_value=0,
            max_value=1
        )
    },
    use_container_width=True,
    hide_index=True,
    disabled=True
)



