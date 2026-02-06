import streamlit as st

# アプリのタイトル
st.title("🤝 支援者サポート・プロトタイプ")

# サイドバーで役割を切り替え
role = st.sidebar.radio("あなたの役割を選択してください", ["支援者", "当事者（お兄様）"])

if role == "支援者":
    st.header("支援者向けメニュー")
    status = st.selectbox(
        "今の状況を選んでください",
        ["落ち着いている", "パニックが起きそう", "こだわりが強く出ている", "何かに困っていそう"]
    )

    if st.button("対応のヒントを見る"):
        if status == "パニックが起きそう":
            st.warning("【対応案】刺激の少ない静かな場所へ誘導し、声をかけすぎず見守りましょう。")
        elif status == "落ち着いている":
            st.success("【対応案】今の安定した環境を維持しましょう。具体的な褒め言葉をかけるのも良いですね。")
        else:
            st.info("【対応案】焦らず、まずは本人の視線の先にあるものを観察してみましょう。")

else:
    st.header("当事者（お兄様）向けメニュー")
    st.write("今の気分を教えてね")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("いー感じ 😄"): st.balloons()
    with col2:
        if st.button("ふつう 😐"): st.write("落ち着いているね")
    with col3:
        if st.button("しんどい 😡"): st.write("無理しないでね")