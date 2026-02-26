import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 設定網頁 ---
st.set_page_config(page_title="雲端喝水管理員", page_icon="☁️")
st.title("☁️ 雲端同步喝水系統")

# --- 連結 Google Sheets ---
# 請將下方的網址替換成你剛剛複製的 Google 試算表網址
URL = "https://docs.google.com/spreadsheets/d/13xNItqw0bSwdtc3__XH4WM3pNTeHdDYcd8DlsTVUHD8/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取雲端資料
def load_cloud_data():
    try:
        return conn.read(spreadsheet=URL)
    except:
        return pd.DataFrame(columns=["日期", "體重", "目標水量", "實際喝水", "達成率"])

# --- 介面邏輯 ---
st.subheader("📍 個人狀態")
weight = st.number_input("今日體重 (kg)", value=70.0, step=0.1)
goal = int(weight * 45)
st.info(f"💡 建議飲水量：{goal} cc")

if 'count' not in st.session_state:
    st.session_state.count = 0

# 喝水進度
display_percent = round((st.session_state.count / goal) * 100, 1) if goal > 0 else 0
st.progress(min(st.session_state.count / goal, 1.0) if goal > 0 else 0)
st.write(f"### 目前已喝：{st.session_state.count} cc ({display_percent}%)")

# 按鈕區 (縮減版範例)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("➕250cc"): st.session_state.count += 250
with c2:
    if st.button("➕500cc"): st.session_state.count += 500
with c3:
    if st.button("🧹重置"): st.session_state.count = 0

# --- 儲存到雲端 ---
if st.button("🚀 同步到 Google 試算表"):
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_row = {
        "日期": today_str,
        "體重": weight,
        "目標水量": goal,
        "實際喝水": st.session_state.count,
        "達成率": f"{display_percent}%"
    }
    
    # 讀取舊資料並加入新資料
    existing_data = load_cloud_data()
    # 簡單過濾掉重複日期的舊資料
    existing_data = existing_data[existing_data["日期"] != today_str]
    updated_data = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
    
    # 寫回 Google Sheets
    conn.update(spreadsheet=URL, data=updated_data)
    st.success("同步成功！你可以去 Google Sheets 查看了！")

# 顯示雲端現有資料
st.divider()
st.subheader("📊 雲端歷史紀錄")
cloud_history = load_cloud_data()

st.dataframe(cloud_history)
