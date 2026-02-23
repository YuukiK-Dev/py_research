import streamlit as st
st.write("has connections:", "connections" in st.secrets)
st.write("has gsheets:", "connections" in st.secrets and "gsheets" in st.secrets["connections"])

st.set_page_config(page_title="支援者アプリ",layout="centered")

st.title("支援者アプリ(試作)")
st.write("左のメニューからページを選んでください")