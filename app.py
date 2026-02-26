import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. 設定網頁 ---
st.set_page_config(page_title="雲端喝水管理員", page_icon="💧", layout="centered")
st.title("💧 雲端同步喝水系統")

# --- 2. 連結 Google Sheets ---
URL = "https://docs.google.com/spreadsheets/d/13xNItqw0bSwdtc3__XH4WM3pNTeHdDYcd8DlsTVUHD8/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def load_cloud_data():
    try:
        return conn.read(spreadsheet=URL, ttl=0)
    except:
        return pd.DataFrame(columns=["日期", "體重", "目標水量", "實際喝水", "達成率"])

# --- 3. 初始化：App 開啟時同步 ---
today_str = datetime.now().strftime("%Y-%m-%d")

if 'initialized' not in st.session_state:
    cloud_df = load_cloud_data()
    if not cloud_df.empty and today_str in cloud_df["日期"].values:
        today_record = cloud_df[cloud_df["日期"] == today_str].iloc[-1]
        st.session_state.count = int(today_record["實際喝水"])
    else:
        st.session_state.count = 0
    st.session_state.initialized = True

# --- 4. 介面邏輯 ---
st.subheader("📍 個人狀態")
weight = st.number_input("今日體重 (kg)", value=90.0, step=0.1)
goal = int(weight * 45)
st.info(f"💡 建議飲水量：{goal} cc")

# 喝水進度計算
display_percent = round((st.session_state.count / goal) * 100, 1) if goal > 0 else 0
st.progress(min(st.session_state.count / goal, 1.0) if goal > 0 else 0)
st.write(f"### 目前已喝：{st.session_state.count} cc ({display_percent}%)")

# --- 5. 加水區 (補回自定義功能) ---
st.divider()
custom_water = st.number_input("輸入自定義容量 (cc)", value=300, step=50)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("➕250"): 
        st.session_state.count += 250
        st.rerun()
with c2:
    if st.button("➕500"): 
        st.session_state.count += 500
        st.rerun()
with c3:
    if st.button(f"➕{custom_water}"): 
        st.session_state.count += custom_water
        st.rerun()
with c4:
    if st.button("🧹重置"): 
        st.session_state.count = 0
        st.rerun()

# --- 6. 儲存到雲端 ---
if st.button("🚀 同步到 Google 試算表", use_container_width=True):
    with st.spinner('同步中...'):
        new_row = {
            "日期": today_str,
            "體重": weight,
            "目標水量": goal,
            "實際喝水": st.session_state.count,
            "達成率": round(st.session_state.count / goal, 4) if goal > 0 else 0
        }
        existing_data = load_cloud_data()
        if not existing_data.empty:
            existing_data = existing_data[existing_data["日期"] != today_str]
        updated_data = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=URL, data=updated_data)
        st.success("同步成功！🎈")

# --- 7. 雲端歷史紀錄 ---
st.divider()
st.subheader("📊 雲端歷史紀錄")

cloud_history = load_cloud_data()

if not cloud_history.empty:
    cloud_history["達成率"] = pd.to_numeric(cloud_history["達成率"], errors='coerce')
    # 維持物理換算顯示，解決 0.6% Bug
    cloud_history["達成率"] = cloud_history["達成率"] * 100
    
    st.data_editor(
        cloud_history,
        column_config={
            "達成率": st.column_config.ProgressColumn(
                "達成率",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True,
        hide_index=True,
        disabled=True
    )
else:
    st.write("目前尚無雲端紀錄。")

if st.button("🔄 刷新雲端資料"):
    st.rerun()
