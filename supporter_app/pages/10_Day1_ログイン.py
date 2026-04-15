import streamlit as st

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"]{
            display:none;
        }
    </style>
    """,
    unsafe_allow_html=True
    )

import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time


# 開始時間をいれておく箱を用意する
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None

#condition を入れておく箱を用意する
if "condition" not in st.session_state:
    st.session_state["condition"] = ""



# ------------------------------
# 画面のタイトル表示
# ------------------------------
st.title("予習型ログアプリ")
st.subheader("Day1：ログインと接続")

# ------------------------------
# Google Sheets に接続する
# ここで、スプレッドシートを読み書きできるようにする
# ------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# ------------------------------
# users シートを読む
# このシートは「本人確認専用」の表
# 使う列は
# ・participant_id
# ・passcode
# の2つ
# ------------------------------
try:
    users_df = conn.read(worksheet="users", ttl=0)
    users_df = pd.DataFrame(users_df)
except Exception:
    # 読み込みに失敗したら、ここで止める
    st.error("Google Sheets の読み込みに失敗しました")
    st.error("secrets.toml や シート名 users を確認してください")
    st.stop()

# ------------------------------
# 入力欄を表示する
# participant_id と passcode をユーザーに入れてもらう
# ------------------------------
st.write("participant_id と passcode を入力してください")

participant_id = st.text_input("participant_id")
passcode = st.text_input("passcode", type="password")

input_id = str(participant_id).strip()
input_pass = str(passcode).strip()

# ------------------------------
# ログインボタンを押したときの処理
# ------------------------------
if st.button("ログイン"):

    # --------------------------
    # 入力された文字の前後の空白を消す
    # 例： " P01 " → "P01"
    # --------------------------
    input_id = str(participant_id).strip()
    input_pass = str(passcode).strip()

    # --------------------------
    # 何も入力されていないときはエラーにする
    # --------------------------
    if input_id == "" or input_pass == "":
        st.error("participant_id と passcode の両方を入力してください")
        st.stop()

    # --------------------------
    # usersシート側のデータも文字としてそろえる
    # 空白も消しておく
    # --------------------------
    users_df["participant_id"] = users_df["participant_id"].astype(str).str.strip()
    users_df["passcode"] = users_df["passcode"].apply(
        lambda x: str(int(float(x))).strip() if pd.notna(x) else ""
    )

    # --------------------------
    # 入力した participant_id と passcode の両方が一致する行を探す
    # 一致する行が1つでもあればログイン成功
    # --------------------------
    matched_user = users_df[
        (users_df["participant_id"] == input_id) &
        (users_df["passcode"] == input_pass)
    ]

    # --------------------------
    # 一致したかどうかで結果を分ける
    # --------------------------
    if not matched_user.empty:
        st.success("ログイン成功")
        st.write("participant_id:", input_id)
        st.session_state["start_time"] = time.time()

        #userシートのcondition列から、この人の条件を取り出す
        condition = matched_user.iloc[0]["condition"]

         #conditionが空なら、この先に進ませない
        if str(condition).strip() == "":
            st.error("このIDは現在使用できません。管理者の連絡してください")
            st.stop()

        #あとで保存時に使えるように、session_stateに覚えておく
        st.session_state["condition"] = condition

       

        #いま取得できたcondition　を確認表示する
        # st.write("condition:", condition)
        # st.write("conditionの中身確認:", repr(condition))

    else:
        st.error("participant_id または passcode が違います")

    # --- ここから Day2（location入力） ---

#ログイン後の条件を表示　(分岐の準備)
st.write("あなたの条件は:",st.session_state["condition"])

   

st.subheader("Step1：場所を選択")

# ラジオボタンで場所を選ぶ
# radio = 選択式ボタン（1つだけ選べる）
location = st.radio(
    "場所を選んでください",
    ["自宅", "学校", "職場", "その他"]
)
# 今選ばれている値を確認表示
st.write("選択された場所：", location)

# --- ここまで ---

# --- ここから supporter入力 ---

st.subheader("Step1.5：支援者の種類を選択")

supporter = st.radio(
    "あなたの立場を選んでください",
    ["家族", "支援員", "教員","その他"]
    )

st.write("選択された支援者：", supporter)

# --- ここまで ---



# --- ここから Day2（status入力） ---

st.subheader("Step2：状態を選択")


# ラジオボタンで状態を選ぶ
status = st.radio(
    "子供の今の状態を選んでください",
    ["安定", "少し不安", "しんどい", "パニック"]
)

#ログありの人だけ過去ログを表示する
if st.session_state["condition"] == "ログあり":
    st.subheader("参考：過去の対応ログ")

    #条件の明示（研究的に重要）
    st.caption("※あなたは「ログあり」条件です")
    st.write(f"※「{status}」状態のうまくいった過去ログだけを表示しています")
    

    #supporter_logを読み込む
    past_log = conn.read(worksheet = "supporter_log",ttl=0)
    past_log = pd.DataFrame(past_log)

    st.write("元の件数:",len(past_log))

    
    
    

    #participant_id列を文字にそろえて空白を消す
    past_log["participant_id"] = past_log["participant_id"].astype(str).str.strip()

    #自分のログだけに絞る
    past_log = past_log[past_log["participant_id"] == input_id]
    st.write("IDで絞った後：",len(past_log))

    #今選んでいる状態と同じログだけに絞る
    past_log = past_log[past_log["seen_status"] == status]
    st.write("状態で絞った後：",len(past_log))

    #成功したログだけに絞る
    past_log = past_log[past_log["is_success"] == "はい"]
    st.write("成功で絞った後：",len(past_log))

    #成功したログの件数を表示
    st.write(f"成功ログ:{len(past_log)}件")

    #新しい順に並べる（最新が上）
    past_log = past_log.sort_values("created_at",ascending=False)

    if past_log.empty:
        # 同じ状態のログが1件もないとき
        st.info("成功した過去ログは、まだありません")
        st.write("今回は過去ログなしで判断してください")
        #最小限の支援（ログがないときだけ）
        st.write("ヒント:まずは落ち着いて状況を確認しましょう")
    else:
        #上から5件だけ表示（見やすくするため）
        st.write(past_log.head(5))

    

# 今選ばれている値を確認表示
st.write("選択された状態：", status)

# --- ここまで ---

# --- ここから Day2（action入力） ---

st.subheader("Step3：対応内容を記録")

# テキスト入力（複数行）
action = st.text_area("子供にたいして、どのような対応をしましたか")
memo = st.text_area("補足メモがあれば入力してください", height=100)

anxiety = st.radio(
    "今のあなたの「どうすればいいかわからない度（不安）」は、どのくらいですか？",
    ["0:ぜんぜん大丈夫（見通しばっちり）", "1:ちょっとドキドキする", "2:まあまあ不安", "3:かなり不安", "4:パニックになりそう！"]
    )

hesitation = st.radio(
    "子供や患者さんに対して対応に迷いはありましたか？",
    ["はい", "いいえ"]
    )

consult_need = st.radio(
    "専門機関に相談は必要ですか？",
    ["はい","いいえ"]
)

if consult_need == "はい":
    consult_who = st.radio(
        "誰に相談しますか？",
        ["家族", "支援員", "教員", "その他"]
    )
else:
    consult_who = ""

#緊急度（どれくらい急いで対応・相談する必要があるか）を選ぶ
urgency = st.radio(
    "どれくらい急いで対応・相談する必要がありますか？",
    ["低い（様子を見てもよい）","中くらい（今日中には対応したい）","高い(すぐに対応・相談したい)"]
)

#心理的負担：今回の対応がどれくらい大変だったか
mental_load = st.radio(
    "今回の対応で感じた心理的な負担はどのくらいでしたか？",
    ["1:ほとんど負担はない", "2:少し負担がある","3:ある程度負担がある", "4:かなり負担がある","5:非常に負担が大きい"]
)

is_success = st.radio(
    "今回の対応は、うまくいきましたか？",
    ["はい","いいえ"]
)

# 入力された内容を確認表示
st.write("入力された対応内容：", action)

# --- ここまで ---

# --- ここから 保存ボタン（まだSheetsには保存しない） ---

if st.button("保存"):

    # 今の時間を作る
    now = pd.Timestamp.now(tz="Asia/Tokyo").strftime("%Y-%m-%d %H:%M:%S")

    # 既存データを読み込み
    old_data = conn.read(worksheet="supporter_log", ttl=0)

    #1件ごとの記録IDを作る
    record_id = "R" + str(pd.Timestamp.now().timestamp()).replace(".","")

    #判断にかかった秒数 小数点2桁にする
    decision_time = round(time.time() - st.session_state["start_time"],2)

    #今回追加する1行を作る
    new_data = pd.DataFrame([{
        "record_id": record_id,
        "created_at": now,
        "participant_id": participant_id,
        "supporter": supporter,
        "seen_status": status,
        "action": action,
        "memo": memo,
        "location": location,
        "anxiety": int(anxiety[0]),
        "hesitation": hesitation,
        "consult_need": consult_need,
        "consult_who": consult_who,
        "urgency": urgency,
        "mental_load": int(mental_load[0]),
        "decision_time_sec": decision_time,
        "condition": st.session_state["condition"],
        "is_success": is_success,
        }])

    # 新しいデータを追加
    df = pd.concat([old_data, new_data],ignore_index=True)

    # Sheetsに書き込み
    conn.update(worksheet="supporter_log",data=df)

    st.success("保存しました！")

    # if consult_need == "はい" and consult_who=="家族":
    #     st.write("家族に相談する判断をしました")

# --- ここまで ---