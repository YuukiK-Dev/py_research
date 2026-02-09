import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# --- 1. ページの設定 ---
st.set_page_config(page_title="連携支援アプリ", layout="centered")

# --- 2. スプレッドシートへの接続設定 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. データの読み込み ---
try:
    # ワークシート名を「シート1」に指定
    df = conn.read(worksheet="シート1")
except Exception:
    df = pd.DataFrame(columns=["date", "time", "user_type", "status"])

st.title("🤝 支援者・当事者 連携アプリ")

# --- 4. 役割の選択 ---
role = st.sidebar.radio("あなたの役割を選択してください", ["支援者", "当事者"])

# 日本時間を取得（寝屋川の記録時間を正確にするため）
tokyo_tz = pytz.timezone('Asia/Tokyo')
now = datetime.now(tokyo_tz)

# --- 5. メインメニュー ---
if role == "支援者":
    st.header("👨‍🏫 支援者向けメニュー")
    status_choice = st.selectbox(
        "今の状況を選んでください",
        ["落ち着いている", "パニックが起きそう", "こだわりが強く出ている", "何かに困っていそう"]
    )
    if st.button("記録する"):
        new_row = pd.DataFrame([{
            "date": now.strftime("%Y/%m/%d"),
            "time": now.strftime("%H:%M:%S"),
            "user_type": "支援者",
            "status": status_choice
        }])
        conn.update(worksheet="シート1", data=pd.concat([df, new_row], ignore_index=True))
        st.success("お疲れ様です。記録を完了しました")

else:
    st.header("😊 お兄様 向けメニュー")
    st.write("今の気分を教えてね")
    # 4つのカラムを作成してボタンを並べる
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("いー感じ 😄", use_container_width=True):
            new_row = pd.DataFrame([{"date": now.strftime("%Y/%m/%d"), "time": now.strftime("%H:%M:%S"), "user_type": "当事者", "status": "いー感じ"}])
            conn.update(worksheet="シート1", data=pd.concat([df, new_row], ignore_index=True))
            st.balloons()
    with col2:
        if st.button("ふつう 😐", use_container_width=True):
            new_row = pd.DataFrame([{"date": now.strftime("%Y/%m/%d"), "time": now.strftime("%H:%M:%S"), "user_type": "当事者", "status": "ふつう"}])
            conn.update(worksheet="シート1", data=pd.concat([df, new_row], ignore_index=True))
    with col3:
        if st.button("しんどい 😡", use_container_width=True):
            new_row = pd.DataFrame([{"date": now.strftime("%Y/%m/%d"), "time": now.strftime("%H:%M:%S"), "user_type": "当事者", "status": "しんどい"}])
            conn.update(worksheet="シート1", data=pd.concat([df, new_row], ignore_index=True))
    with col4:
        if st.button("ねむい 😴", use_container_width=True):
            new_row = pd.DataFrame([{"date": now.strftime("%Y/%m/%d"), "time": now.strftime("%H:%M:%S"), "user_type": "当事者", "status": "ねむい"}])
            conn.update(worksheet="シート1", data=pd.concat([df, new_row], ignore_index=True))

# --- 6. 履歴 ---
st.divider()
st.header("📊 活動の記録")
try:
    current_logs = conn.read(worksheet="シート1")
    if not current_logs.empty:
        if st.checkbox("最新の履歴を表示する"):
            st.dataframe(current_logs.tail(10), use_container_width=True, hide_index=True)
except:
    st.write("データの読み込みに失敗しました。")
