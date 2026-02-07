import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- データベースの準備機能 ---
def init_db():
    # research_data.db というファイル名でデータベースを作成・接続
    conn = sqlite3.connect('research_data.db')
    c = conn.cursor()
    # テーブル（表）を作成：日付、役割、内容
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            timestamp TEXT,
            role TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

# データを保存する関数
def add_log(role, content):
    conn = sqlite3.connect('research_data.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO activity_logs (timestamp, role, content) VALUES (?, ?, ?)', 
              (now, role, content))
    conn.commit()
    conn.close()

# データを読み出す関数
def get_logs():
    conn = sqlite3.connect('research_data.db')
    df = pd.read_sql_query('SELECT * FROM activity_logs ORDER BY timestamp ASC', conn)
    conn.close()
    return df

# --- アプリのメイン処理 ---
init_db()  # 起動時にデータベースを初期化

st.title("🤝 支援者・当事者 連携プロトタイプ")

role = st.sidebar.radio("あなたの役割を選択してください", ["支援者", "当事者（お兄様）"])

if role == "支援者":
    st.header("支援者向けメニュー")
    status = st.selectbox(
        "今の状況を選んでください",
        ["落ち着いている", "パニックが起きそう", "こだわりが強く出ている", "何かに困っていそう"]
    )

    if st.button("記録してヒントを見る"):
        # データベースに保存
        add_log("支援者", f"状況: {status}")
        
        # アドバイスの表示（ここはIncrement 1と同じ）
        if status == "パニックが起きそう":
            st.warning("【対応案】静かな場所へ誘導しましょう。")
        else:
            st.info("【対応案】まずは本人の様子を静かに観察しましょう。")
        st.success("状況を記録しました。")

else:
    st.header("当事者 向けメニュー")
    st.write("今の気分を教えてね")
    col1, col2, col3 = st.columns(3)
    
    # 各ボタンが押されたらデータを保存する
    with col1:
        if st.button("いー感じ 😄"):
            add_log("当事者", "気分: 良い気分")
            st.balloons()
    with col2:
        if st.button("ふつう 😐"):
            add_log("当事者", "気分: 普通")
            st.write("記録したよ！")
    with col3:
        if st.button("しんどい 😡"):
            add_log("当事者", "気分: 乗り気ではない")
            st.write("無理しないでね。記録したよ。")

# --- 履歴の表示セクション（支援者9割のサポート機能） ---
st.markdown("---")
st.header("📊 活動の記録")
if st.checkbox("履歴を表示する"):
    logs_df = get_logs()
    if not logs_df.empty:
        st.dataframe(logs_df) # 表形式で表示
    else:
        st.write("まだ記録がありません。")

# ---グラフ視覚化セクション（Increment 3）---
st.markdown("---")
st.header("📈 状況の分析")

if st.checkbox("グラフで分析する"):
    logs_df=get_logs()
    if not logs_df.empty:
        #「気分」や「状況：」という文字を消して、純粋な値だけにする（データ整形）
        logs_df['clean_content'] = logs_df['content'].str.replace('気分: ','').str.replace('状況: ','')
        #役割ごとに集計 
        role_to_analyze=st.selectbox("分析する対象を選んでください",["当事者","支援者"])        
        filtered_df=logs_df[logs_df['role'] == role_to_analyze]

        if not filtered_df.empty:
            counts = filtered_df['clean_content'].value_counts()

            st.bar_chart(counts)
            st.write(f"{role_to_analyze}の記録内訳（合計 {len(filtered_df)}件)")
        else:
            st.write("この役割のデータはまだありません")
    else:
        st.write("データが不足しているため、分析できません")