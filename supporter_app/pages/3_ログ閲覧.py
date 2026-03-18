import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("ログ閲覧")

conn =  st.connection("gsheets",type=GSheetsConnection)

supporter_log  = conn.read(worksheet="supporter_log")

supporter_log["datetime"] = supporter_log["date"] + " " + supporter_log["time"]
supporter_log["datetime"] = pd.to_datetime(supporter_log["datetime"])
supporter_log = supporter_log.sort_values("datetime",ascending=False)

suggestion_log  = conn.read(worksheet="suggestion_log")

supporter_type = st.selectbox(
    "支援者別で絞り込む",
    ["すべて","家族","施設職員","その他"]

)



if supporter_type != "すべて":
    supporter_log = supporter_log[supporter_log["supporter"] == supporter_type]



st.subheader("支援者行動ログ")
st.dataframe(supporter_log)

st.subheader("提案ログ")
st.dataframe(suggestion_log)