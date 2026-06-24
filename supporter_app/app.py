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
    st.switch_page("pages/10_support_record.py")