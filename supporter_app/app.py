import streamlit as st
st.set_page_config(page_title="支援者アプリ",layout="centered")
st.markdown(
        """
        <style>
            /*1.サイドバーのナビを見つけて*/
            [data-testid = "stSidebarNav"]{
                 /*2.表示を消す*/
                display:none            
            }
        </style>
        """,
        unsafe_allow_html=True
)



# st.write("has connections:", "connections" in st.secrets)
# st.write("has gsheets:", "connections" in st.secrets and "gsheets" in st.secrets["connections"])


st.title("支援者アプリ(試作)")
st.write("下のボタンから入力を開始してください")

if st.button("入力を開始する"):
    # ------------------------------
    # 入力開始時に、前回のログイン状態や入力内容をリセットする
    # これにより、必ずログイン画面から始められるようにする
    # ------------------------------
    st.session_state["is_logged_in"] = False
    st.session_state["participant_id"] = ""
    st.session_state["condition"] = ""
    st.session_state["start_time"] = None

    # 前回の入力内容もリセットする
    st.session_state["support_category"] = "選択してください"
    st.session_state["ai_advice_requested"] = False
    st.session_state["ai_advice_text"] = ""
    st.session_state["ai_advice_source"] = ""
    st.session_state["ai_error_message"] = ""
    st.session_state["action_text"] = ""
    st.session_state["record_saved"] = False

    # ログイン画面を含む入力ページへ移動する
    st.switch_page("pages/10_support_record.py")