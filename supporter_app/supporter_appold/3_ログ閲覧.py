import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("ログ閲覧")

participant_id = st.text_input("あなたのIdを入力してください")
passcode = st.text_input("パスコードを入力してください",type="password")
conn =  st.connection("gsheets",type=GSheetsConnection)

users_df = conn.read(worksheet="users",ttl=0)

#認証用の関数
#participant_idとpasscodeがusersシートにあるか確認する
def authenticate_user(users_df, participant_id, passcode):
    #入力値の前後空白を除去
    participant_id = str(participant_id).strip()
    
    #participant_id が一致する行だけを取り出す
    user = users_df[users_df["participant_id"].astype(str).str.strip() == participant_id]

    #そのIDが存在しなければ認証失敗
    if user.empty:
        return False
    
    try:
        saved_passcode = int(float(user.iloc[0]["passcode"]))
        input_passcode = int(str(passcode).strip())
    except ValueError:
        return False
    
    return saved_passcode == input_passcode

 # ① participant_id と passcode の認証
if not authenticate_user(users_df, participant_id, passcode):
    st.error("参加者IDまたはパスコードが正しくありません")
    st.stop()


#ここから下は、認証OKの人だけ
#ログ読み込み
supporter_log  = conn.read(worksheet="supporter_log",ttl=0)

#自分のデータだけ抽出
supporter_logs=supporter_log[
    supporter_log["participant_id"] == participant_id
].copy()

#memoは、非表示
if "memo" in supporter_log.columns:
    supporter_log = supporter_log.drop(columns=["memo"])

#並び替え
supporter_log = supporter_log.sort_values("created_at",ascending=False)


supporter_type = st.selectbox(
    "支援者別で絞り込む",
    ["すべて","家族","施設職員","その他"]

)



if supporter_type != "すべて":
    supporter_log = supporter_log[supporter_log["supporter"] == supporter_type]


#表示
st.subheader("あなたの支援ログ")
st.dataframe(supporter_log)

#提案ログも同様に制限
suggestion_log = conn.read(worksheet="suggestion_log",ttl=0)

suggestion_log = suggestion_log[
    suggestion_log["record_id"].isin(supporter_log["record_id"])
]

st.subheader("提案ログ")
st.dataframe(suggestion_log)