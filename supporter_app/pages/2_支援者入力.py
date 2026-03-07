import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import uuid

st.set_page_config(page_title="支援者：入力", layout="centered")
st.title("支援者：入力（supporter_log）")

conn = st.connection("gsheets", type=GSheetsConnection)

def suggest_support(status):
    if status == "安定":
        return "見守りを中心にします。"
    elif status == "少し不安":
        return "安心できる短い声かけと状況確認をします。"
    elif status == "しんどい":
        return "刺激を減らし、休息を優先します。"
    elif status == "パニック":
        return "安全確保を優先し、落ち着くまで無理に関わりすぎません。"
    return "状況を確認してください。"

if "last_record_id" not in st.session_state:
    st.session_state.last_record_id = None
if "last_created_at" not in st.session_state:
    st.session_state.last_created_at = None
if "last_suggestion_type" not in st.session_state:
    st.session_state.last_suggestion_type = None
if "last_seen_status" not in st.session_state:
    st.session_state.last_seen_status = None
if "after_relief" not in st.session_state:
    st.session_state.after_relief = 0

with st.form("supporter_input"):
    supporter = st.selectbox("支援者の種類", ["家族", "支援員", "教員", "その他"])
    seen_status = st.selectbox("当事者の状態", ["安定", "少し不安", "しんどい","パニック"])
    action = st.text_input("対応（action）")
    memo = st.text_area("メモ")
    anxiety=st.slider("支援者の不安度 (0=なし~4=強い)",0,4,0)
    hesitation=st.radio("対応に困ったか?",["はい","いいえ"],horizontal=True)
    consult_need=st.radio("専門機関に相談したいと思ったか?",["はい","いいえ"],horizontal=True)
    urgency = st.selectbox("緊急度", [0, 1, 2], index=0)

    submitted = st.form_submit_button("保存")

if submitted:
    # 最低限の入力チェック（必要なものだけ）
    if action.strip() == "":
        st.error("対応（action）は空欄にできません")
        st.stop()

    now = datetime.now()
    record_id = uuid.uuid4().hex #一意のID

    new_row = pd.DataFrame([{
        "record_id": record_id,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "supporter": supporter,
        "seen_status": seen_status,
        "action": action.strip(),
        "memo": memo.strip(),
        "anxiety": int(anxiety),
        "hesitation": hesitation,
        "consult_need": consult_need,
        "urgency": int(urgency),
    }])

    # 既存を読み込んで追記 → 全体を書き戻す（writeが無い環境向け）
    current = conn.read(worksheet="supporter_log", ttl=0)
    if current is None or len(current) == 0:
        combined = new_row
    else:
         # 重複列対策（現状のままでOK）
        current = current.loc[:, ~current.columns.duplicated()]

         # もし過去データに record_id が無い場合に備えて列補完
        for col in new_row.columns:
            if col not in current.columns:
                current[col] = pd.NA
        combined = pd.concat([current, new_row], ignore_index=True)

    conn.update(worksheet="supporter_log", data=combined)


    #分岐：提案タイプを決める
    if anxiety >= 3:
        suggestion_type = "HIGH_SUPPORT"
    elif hesitation == "はい":
        suggestion_type = "GUIDANCE"
    else:
        suggestion_type = "NORMAL"
    
   
# 画面に残す（これが肝）
    st.session_state.last_record_id = record_id
    st.session_state.last_created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.last_suggestion_type = suggestion_type
    st.session_state.last_seen_status = seen_status
    st.session_state.after_relief = 0
    

    st.success("保存しました（supporter_log）")
    st.dataframe(new_row)



# --- 提案＋安心度＋提案ログ保存（submittedの外）---
if st.session_state.last_record_id is not None:
    st.markdown("### 提案")

    suggestion_type = st.session_state.last_suggestion_type
    seen_status = st.session_state.last_seen_status
    suggestion_text = suggest_support(seen_status)

    if suggestion_type == "HIGH_SUPPORT":
        st.warning(suggestion_text)
        st.caption("まずは一人で抱え込まないことが大切です。信頼できる人や専門機関への共有も検討してみましょう")
    elif suggestion_type == "GUIDANCE":
        st.info(suggestion_text)
        st.caption("対応手順を1つずつ整理してみましょう。まずは当事者の状態を言語化してみましょう")
    else:
        st.success(suggestion_text)
        st.caption("落ち着いて対応できています。引き続き様子を見ましょう")

    
    after_relief = st.slider(
        "この提案で少し安心できましたか？",
        0,4,
        key = "after_relief"
    )

    if st.button("提案ログを保存",key="save_suggestion"):
        suggestion_row = pd.DataFrame([{
            "record_id": st.session_state.last_record_id,
            "created_at": st.session_state.last_created_at,
            "seen_status":st.session_state.last_seen_status,
            "suggestion_type": st.session_state.last_suggestion_type,
            "suggestion_text":suggestion_text,
            "after_relief": int(st.session_state.after_relief),
        }])

        current_suggestion = conn.read(worksheet="suggestion_log", ttl=0)
        if current_suggestion is None or len(current_suggestion) == 0:
            combined_suggestion = suggestion_row
        else:
            current_suggestion = current_suggestion.loc[:, ~current_suggestion.columns.duplicated()]
            for col in suggestion_row.columns:
                if col not in current_suggestion.columns:
                    current_suggestion[col] = pd.NA
            combined_suggestion = pd.concat([current_suggestion, suggestion_row], ignore_index=True)

        conn.update(worksheet="suggestion_log", data=combined_suggestion)

        st.success("保存しました（suggestion_log）")

        # 状態クリア → 次の入力へ
        st.session_state.last_record_id = None
        st.session_state.last_created_at = None
        st.session_state.last_suggestion_type = None
        st.session_state.last_seen_status = None
        st.session_state.pop("after_relief",None)
        st.rerun()
    

   


st.markdown("---")
st.subheader("困りごとサポート（試作）")

trouble=st.selectbox(
        "今の困りごとは",
        ["対応方法がわからない"]
    )

if trouble=="対応方法がわからない":
    st.info("大丈夫です。まずは当事者の「今の状態」を一言で書いてみましょう")