import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- 1. 設定網頁 ---
st.set_page_config(page_title="雙人雲端喝水神器", page_icon="💧", layout="centered")

# --- 2. 視覺美化 CSS (含全家福背景與毛玻璃效果) ---
bg_img_url = "https://lh3.googleusercontent.com/pw/AP1GczPQAeEyydw0HzXGq3cyXWggu8_yrupGiYDBYBhcYhtvubDIdpS5pG7NNYc1R59y57HU6SspjCl4BGwNxdTkWxni3jrDHqcbFNaysEdDR8ntrB2vmCGm=w2400"
st.markdown(f"""
<style>
/* 全網頁背景設定 */
.stApp {{
    background-image: url("{bg_img_url}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

/* 毛玻璃主區塊：半透明白色底，文字清晰且有質感 */
.main .block-container {{
    background-color: rgba(255, 255, 255, 0.9); 
    padding: 40px;
    border-radius: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    margin-top: 20px;
    margin-bottom: 20px;
}}

/* 按鈕配色優化 */
div.stColumn:nth-child(1) > div > div > div > button {{ background-color: #B0E0E6 !important; color: black !important; border: none !important; font-weight: bold; }}
div.stColumn:nth-child(2) > div > div > div > button {{ background-color: #4682B4 !important; color: white !important; border: none !important; font-weight: bold; }}
div.stColumn:nth-child(3) > div > div > div > button {{ background-color: #FFD700 !important; color: black !important; border: none !important; font-weight: bold; }}
div.stColumn:nth-child(4) > div > div > div > button {{ background-color: #E0E0E0 !important; border: none !important; }}

/* 讓標題在背景下更醒目 */
h1, h2, h3 {{
    color: #1E3A5F;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
}}
</style>
""", unsafe_allow_html=True)

# --- 3. 連結 Google Sheets ---
URL = "https://docs.google.com/spreadsheets/d/13xNItqw0bSwdtc3__XH4WM3pNTeHdDYcd8DlsTVUHD8/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def load_cloud_data():
    try:
        df = conn.read(spreadsheet=URL, ttl=0)
        if "使用者" not in df.columns: df["使用者"] = "老公" 
        return df
    except:
        return pd.DataFrame(columns=["日期", "使用者", "體重", "目標水量", "實際喝水", "達成率"])

# --- 4. 身分選擇 ---
st.title("💧 雙人雲端喝水神器 Pro")
user = st.radio("請選擇使用者：", ["老公", "老婆"], horizontal=True)

if 'last_user' not in st.session_state or st.session_state.last_user != user:
    st.session_state.last_user = user
    st.session_state.initialized = False

# --- 5. 初始化 ---
today_str = datetime.now().strftime("%Y-%m-%d")

if not st.session_state.get('initialized', False):
    cloud_df = load_cloud_data()
    user_records = cloud_df[cloud_df["使用者"] == user]
    user_today = user_records[user_records["日期"] == today_str]
    
    st.session_state.count = int(user_today.iloc[-1]["實際喝水"]) if not user_today.empty else 0
    st.session_state.current_weight = float(user_records.iloc[-1]["體重"]) if not user_records.empty else (90.0 if user == "老公" else 50.0)
    st.session_state.initialized = True

# --- 6. 個人狀態與勳章 ---
st.subheader(f"📍 {user} 的個人狀態")
weight = st.number_input(f"{user} 今日體重 (kg)", value=st.session_state.current_weight, step=0.1, format="%.1f", key=f"w_{user}")
goal = int(weight * 45)

percent_val = (st.session_state.count / goal) if goal > 0 else 0
if percent_val >= 1.0:
    st.success(f"🏅 恭喜！{user} 已達成今日目標！")
    st.balloons()
else:
    st.info(f"💡 建議飲水量：{goal} cc")

st.progress(min(percent_val, 1.0))
st.write(f"### 目前已喝：{st.session_state.count} cc ({round(percent_val*100, 1)}%)")

# --- 7. 加水區 ---
st.divider()
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

if st.button(f"🚀 同步 {user} 紀錄到雲端", use_container_width=True):
    with st.spinner('同步中...'):
        new_row = {"日期": today_str, "使用者": user, "體重": weight, "目標水量": goal, "實際喝水": st.session_state.count, "達成率": round(st.session_state.count/goal, 4) if goal > 0 else 0}
        df = load_cloud_data()
        df = df[~((df["日期"] == today_str) & (df["使用者"] == user))]
        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(spreadsheet=URL, data=updated_df)
        st.success("同步成功！🎈")
        st.session_state.current_weight = weight

# --- 8. 歷史紀錄 ---
st.divider()
st.subheader("📊 雲端歷史紀錄")
all_data = load_cloud_data()
if not all_data.empty:
    all_data_display = all_data.copy()
    all_data_display["達成率"] = pd.to_numeric(all_data_display["達成率"], errors='coerce') * 100
    st.data_editor(all_data_display, column_config={"達成率": st.column_config.ProgressColumn("達成率", format="%.1f%%", min_value=0, max_value=100)}, use_container_width=True, hide_index=True, disabled=True)

# --- 9. 趨勢圖 (優化日期顯示) ---
st.divider()
st.subheader("📈 最近 7 天飲水趨勢")
if not all_data.empty:
    all_data["日期"] = pd.to_datetime(all_data["日期"])
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_df = all_data[all_data["日期"] >= seven_days_ago].sort_values("日期")
    
    if not recent_df.empty:
        fig = px.line(
            recent_df, 
            x="日期", 
            y="實際喝水", 
            color="使用者", 
            markers=True, 
            color_discrete_map={"老公": "#0000FF", "老婆": "#FF0000"},
            labels={"實際喝水": "飲水量 (cc)", "日期": "日期"}
        )
        
        # --- 關鍵修正：強制 X 軸格式 ---
        fig.update_xaxes(
            dtick="D1",              # 強制每一天顯示一個刻度
            tickformat="%m/%d",      # 只顯示 月/日 (例如 02/26)
            tickangle=0              # 讓文字保持水平，不轉彎
        )
        
        st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 刷新雲端資料"): st.rerun()



