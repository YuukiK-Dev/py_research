import streamlit as st from streamlit_gsheets import GSheetsConnection import pandas as pd from datetime import datetime import pytz

--- 1. ページの設定 ---
st.set_page_config(page_title="連携支援アプリ", layout="centered")

--- 2. スプレッドシートへの接続設定 ---
Secretsに登録した合鍵を使ってGoogleシートに接続します
conn = st.connection("gsheets", type=GSheetsConnection)

--- 3. データの読み込み ---
try: # 「状況確認シート」という名前のシートを読み込みます df = conn.read(worksheet="状況確認シート") except Exception: # まだデータがない場合は、正しい見出しで空の枠を作成します df = pd.DataFrame(columns=["date", "time", "user_type", "status"])

st.title("🤝 支援者・当事者 連携アプリ")

--- 4. 役割の選択（サイドバー） ---
role = st.sidebar.radio("あなたの役割を選択してください", ["支援者", "当事者"])

日本時間を取得（寝屋川の記録時間を正確にするため）
tokyo_tz = pytz.timezone('Asia/Tokyo') now = datetime.now(tokyo_tz)

--- 5. メインメニュー ---
if role == "支援者": st.header("👨‍🏫 支援者向けメニュー") status_choice = st.selectbox( "今の状況を選んでください", ["落ち着いている", "パニックが起きそう", "こだわりが強く出ている", "何かに困っていそう"] )

else: st.header("😊 お兄様 向けメニュー") st.write("今の気分を教えてね") col1, col2, col3 = st.columns(3)

--- 6. 履歴と分析（共通） ---
st.divider() st.header("📊 活動の記録")

常に最新の状態を見せるために再読み込み
try: current_logs = conn.read(worksheet="状況確認シート") if not current_logs.empty: if st.checkbox("最新の履歴を表示する"): st.dataframe(current_logs.tail(10), use_container_width=True, hide_index=True)

except: st.write("データの読み込みに失敗しました。")
