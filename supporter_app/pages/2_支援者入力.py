# Streamlitを st という短い名前で使えるようにする
import streamlit as st

# 表形式のデータを扱うためのライブラリ
import pandas as pd

# 現在の日付と時刻を取得するための道具
from datetime import datetime

# Streamlit から Google Sheets に接続するための道具
from streamlit_gsheets import GSheetsConnection

# 重ならない一意のIDを作るための道具
import uuid

# 秒数を測るための道具
import time


# アプリ全体の基本設定
# page_title はブラウザのタブ名、layout="centered" は中央寄せレイアウト
st.set_page_config(page_title="支援者：入力", layout="centered")

# 画面の大きなタイトルを表示
st.title("支援者：入力（supporter_log）")


# Google Sheets への接続を作る
# secrets.toml などに設定された "gsheets" 接続情報を使う
conn = st.connection("gsheets", type=GSheetsConnection)


# 当事者の状態に応じて、支援者への提案文を返す関数
def suggest_support(status):
    # status が「安定」ならこの文章を返す
    if status == "安定":
        return "見守りを中心にします。"

    # status が「少し不安」ならこの文章を返す
    elif status == "少し不安":
        return "安心できる短い声かけと状況確認をします。"

    # status が「しんどい」ならこの文章を返す
    elif status == "しんどい":
        return "刺激を減らし、休息を優先します。"

    # status が「パニック」ならこの文章を返す
    elif status == "パニック":
        return "安全確保を優先し、落ち着くまで無理に関わりすぎません。"

    # どれにも当てはまらないときの予備の文章
    return "状況を確認してください。"


# ----------------------------
# session_state の初期化
# ----------------------------
# session_state は、画面の再表示が起きても一時的に値を覚えておくメモ帳のようなもの


# 直前に保存した record_id をまだ持っていなければ、None を入れて初期化
if "last_record_id" not in st.session_state:
    st.session_state.last_record_id = None

# 直前に保存した created_at をまだ持っていなければ、None を入れて初期化
if "last_created_at" not in st.session_state:
    st.session_state.last_created_at = None

# 直前の提案タイプをまだ持っていなければ、None を入れて初期化
if "last_suggestion_type" not in st.session_state:
    st.session_state.last_suggestion_type = None

# 直前に見た当事者状態をまだ持っていなければ、None を入れて初期化
if "last_seen_status" not in st.session_state:
    st.session_state.last_seen_status = None

# 提案後の安心度をまだ持っていなければ、0 を入れて初期化
if "after_relief" not in st.session_state:
    st.session_state.after_relief = 0

# 計測開始時刻をまだ持っていなければ、None を入れて初期化
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# 意思決定時間（秒）をまだ持っていなければ、None を入れて初期化
if "decision_time_sec" not in st.session_state:
    st.session_state.decision_time_sec = None


# ----------------------------
# 入力フォーム
# ----------------------------
#usersシートを読み込む
users_df = conn.read(worksheet="users",ttl=0)

#participant_idと passcode　からユーザ情報取得
def get_user(users_df,participant_id,passcode):
    participant_id = str(participant_id).strip()
    input_passcode = str(passcode).strip()

    temp_df = users_df.copy()
    temp_df["participant_id"] = temp_df["participant_id"].astype(str).str.strip()

    #passcode　を　1111.0　→　1111にそろえる
    temp_df["passcode"] = temp_df["passcode"].apply(
        lambda x: str(int(float(x))).strip() if pd.notna(x) else ""
    )

    user = temp_df[
        (temp_df["participant_id"] == participant_id) &
        (temp_df["passcode"] == input_passcode)
    ]
    return user

#デバッグ表示（確認用）
st.write("usersシート確認")
st.dataframe(users_df)

participant_id = st.text_input("参加者ID")
passcode = st.text_input("パスコード",type="password")

condition = None
user = pd.DataFrame()

if participant_id and passcode:
    user = get_user(users_df,participant_id,passcode)
    if not user.empty:
        condition = user.iloc[0]["condition"]
        supporter_log_df = conn.read(worksheet="supporter_log",ttl=0)

        success_count = 0
        if not user.empty and supporter_log_df is not None and len(supporter_log_df) > 0:
            supporter_log_df["participant_id"] = supporter_log_df["participant_id"]

            if "is_success" in supporter_log_df.columns:
                user_success_log = supporter_log_df[
                    (supporter_log_df["participant_id"] == str(participant_id).strip()) &
                    (supporter_log_df["is_success"] == True)
                ]
                success_count = len(user_success_log)
        st.metric("成功ログ数",success_count)
        st.info(f"あなたの知恵（成功ログ）が{success_count}件貯まりました")


# with st.form(...) の中に書いた入力欄は、最後の保存ボタンが押されるまでまとめて扱われる
with st.form("supporter_input"):

    # 「開始」ボタン
    # これを押した瞬間の時刻を start_time に保存する
    if st.form_submit_button("開始"):
        # 現在時刻を秒で取得して保存
        st.session_state.start_time = time.time()

        # 前回の計測結果が残っていると困るので、いったん空にする
        st.session_state.decision_time_sec = None

    st.info("入力を始める前に必ず「開始」を押してください（時間計測のため）")

   
    # 支援者の種類を選ぶ欄
    supporter = st.selectbox("支援者の種類", ["家族", "支援員", "教員", "その他"])

    # 当事者の状態を選ぶ欄
    seen_status = st.selectbox("当事者の状態", ["安定", "少し不安", "しんどい", "パニック"])

    # 実際に行った対応内容を入力する欄
    action = st.text_input("対応（action）")

    # 補足メモを入力する欄
    memo = st.text_area("メモ")

    # 支援者の不安度を言葉で選ぶラジオボタン
    anxiety_label = st.radio(
        "支援者の不安度",
        [
            "不安はない",
            "少し不安",
            "やや不安",
            "かなり不安",
            "とても不安",
        ],
        horizontal=True
    )

    # 不安度の言葉を数値に変換する辞書
    anxiety_map = {
        "不安はない": 0,
        "少し不安": 1,
        "やや不安": 2,
        "かなり不安": 3,
        "とても不安": 4,
    }

    # 選ばれた不安度ラベルを数値に変換
    anxiety = anxiety_map[anxiety_label]

    # 対応に困ったかどうかを選ぶ欄
    hesitation = st.radio("対応に困ったか?", ["はい", "いいえ"], horizontal=True)

    # 専門機関に相談したいと思ったかどうかを選ぶ欄
    consult_need = st.radio("専門機関に相談したいと思ったか?", ["はい", "いいえ"], horizontal=True)

    # 緊急度を選ぶ欄
    urgency = st.selectbox("緊急度", [0, 1, 2], index=0)

    # 今回の研究で使う心理的負担を1〜5で選ぶ欄
    mental_load_label = st.radio(
        "この対応を決めるときの負担",
        ["1", "2", "3", "4", "5"],
        horizontal=True
    )

    # 文字列の "1"〜"5" を整数の 1〜5 に変換
    mental_load = int(mental_load_label)

    is_success = st.checkbox("✅ 今回の対応は納得感があり、うまくいった（成功）")

    # フォーム全体を保存するボタン
      # フォーム全体を保存するボタン
    submitted = st.form_submit_button("保存")

    if submitted:

         # ② 開始ボタンが押されているか確認
        if st.session_state.start_time is None:
            st.error("先に「開始」を押してください")
            st.stop()

       
        if user.empty:
            st.error("参加者IDまたはパスコードが正しくありません")
            st.stop()

        # ③ action が空欄なら止める
        if action.strip() == "":
            st.error("対応（action）は空欄にできません")
            st.stop()

        # ④ 意思決定時間を計算
        end_time = time.time()
        decision_time = round(end_time - st.session_state.start_time, 2)
        st.session_state.decision_time_sec = decision_time

        # ⑤ 保存用の値を作る
        now = datetime.now()
        record_id = uuid.uuid4().hex

        # ⑥ 今回の入力内容を1行の表データにまとめる
        new_row = pd.DataFrame([{
            "record_id": record_id,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "participant_id": participant_id,
            "supporter": supporter,
            "seen_status": seen_status,
            "action": action.strip(),
            "memo": memo.strip(),
            "anxiety": int(anxiety),
            "hesitation": hesitation,
            "consult_need": consult_need,
            "urgency": int(urgency),
            "mental_load": mental_load,
            "decision_time_sec": st.session_state.decision_time_sec,
            "condition": condition,
            "is_success": is_success,
        }])

        # ⑦ 既存の supporter_log シートを読み込む
        current = conn.read(worksheet="supporter_log", ttl=0)

        if current is None or len(current) == 0:
            combined = new_row
        else:
            current = current.loc[:, ~current.columns.duplicated()]

            for col in new_row.columns:
                if col not in current.columns:
                    current[col] = pd.NA

            for col in current.columns:
                if col not in new_row.columns:
                    new_row[col] = pd.NA

            new_row = new_row[current.columns]
            combined = pd.concat([current, new_row], ignore_index=True)

        # ⑧ supporter_log を更新
        conn.update(worksheet="supporter_log", data=combined)

        # ⑨ 提案タイプの決定
        if anxiety >= 3:
            suggestion_type = "HIGH_SUPPORT"
        elif hesitation == "はい":
            suggestion_type = "GUIDANCE"
        else:
            suggestion_type = "NORMAL"

        # ⑩ session_state に保存
        st.session_state.last_record_id = record_id
        st.session_state.last_created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.last_suggestion_type = suggestion_type
        st.session_state.last_seen_status = seen_status
        st.session_state.after_relief = 0

        # ⑪ 保存成功表示
        st.success("保存しました（supporter_log）")
        st.dataframe(new_row)


# ----------------------------
# ログあり条件のときの表示
# ----------------------------
# 今は仮の表示だけ
# 将来ここに「過去ログ参照」処理を入れる
if condition == "ログあり":
    st.subheader("過去ログ参照")
    st.write("過去事例1：落ち込みが強い → 無理に促さず見守り → 後で会話できた")
    st.write("過去事例2：反応が鈍い → 声かけを短くした → 拒否感が少なかった")


# ----------------------------
# 提案＋安心度＋提案ログ保存
# ----------------------------
# 直前に supporter_log が保存されている場合だけ、提案表示を行う
if st.session_state.last_record_id is not None:

    # 小見出しを表示
    st.markdown("### 提案")

    # session_state から直前の提案タイプと状態を取り出す
    suggestion_type = st.session_state.last_suggestion_type
    seen_status = st.session_state.last_seen_status

    # 状態に応じた提案文を作る
    suggestion_text = suggest_support(seen_status)

    # 提案タイプに応じて表示の見た目を変える
    if suggestion_type == "HIGH_SUPPORT":
        st.warning(suggestion_text)
        st.caption("まずは一人で抱え込まないことが大切です。信頼できる人や専門機関への共有も検討してみましょう")

    elif suggestion_type == "GUIDANCE":
        st.info(suggestion_text)
        st.caption("対応手順を1つずつ整理してみましょう。まずは当事者の状態を言語化してみましょう")

    else:
        st.success(suggestion_text)
        st.caption("落ち着いて対応できています。引き続き様子を見ましょう")

    # 提案を見たあと、どれくらい安心できたかを選ぶ欄
    after_relief_label = st.radio(
        "この提案で少し安心できましたか？",
        ["とても安心できた", "少し安心できた", "どちらともいえない", "あまり安心できない", "全く安心できない"],
        horizontal=True
    )

    # 安心度ラベルを数値に変換する辞書
    after_relief_map = {
        "とても安心できた": 4,
        "少し安心できた": 3,
        "どちらともいえない": 2,
        "あまり安心できない": 1,
        "全く安心できない": 0,
    }

    # 選ばれた安心度を数値に変換
    after_relief = after_relief_map[after_relief_label]

    # 提案ログを保存するボタン
    if st.button("提案ログを保存", key="save_suggestion"):

        # 提案ログとして1行のデータを作る
        suggestion_row = pd.DataFrame([{
            # supporter_log とひもづけるための record_id
            "record_id": st.session_state.last_record_id,

            # 元の保存日時
            "created_at": st.session_state.last_created_at,

            # 元の当事者状態
            "seen_status": st.session_state.last_seen_status,

            # 提案タイプ
            "suggestion_type": st.session_state.last_suggestion_type,

            # 提案文そのもの
            "suggestion_text": suggestion_text,

            # 安心度（数値）
            "after_relief": int(after_relief),

            # 安心度（ラベル）
            "after_relief_label": after_relief_label,
        }])

        # 既存の suggestion_log シートを読み込む
        current_suggestion = conn.read(worksheet="suggestion_log", ttl=0)

        # suggestion_log が空なら、そのまま使う
        if current_suggestion is None or len(current_suggestion) == 0:
            combined_suggestion = suggestion_row

        # suggestion_log にすでにデータがある場合
        else:
            # 重複列を除く
            current_suggestion = current_suggestion.loc[:, ~current_suggestion.columns.duplicated()]

            # 不足している列を補う
            for col in suggestion_row.columns:
                if col not in current_suggestion.columns:
                    current_suggestion[col] = pd.NA

            # 既存データの下に今回の提案ログを追加
            combined_suggestion = pd.concat([current_suggestion, suggestion_row], ignore_index=True)

        # suggestion_log シート全体を更新
        conn.update(worksheet="suggestion_log", data=combined_suggestion)

        # 保存成功メッセージ
        st.success("保存しました（suggestion_log）")

        # 次の入力に備えて、提案関係の session_state をクリアする
        st.session_state.last_record_id = None
        st.session_state.last_created_at = None
        st.session_state.last_suggestion_type = None
        st.session_state.last_seen_status = None
        st.session_state.pop("after_relief", None)

        # 画面を再読み込みして表示を更新
        st.rerun()


# 区切り線を表示
st.markdown("---")

# 小見出しを表示
st.subheader("困りごとサポート（試作）")

# 今の困りごとを選ぶ欄
trouble = st.selectbox(
    "今の困りごとは",
    ["対応方法がわからない"]
)

# 選ばれた困りごとに応じてメッセージを出す
if trouble == "対応方法がわからない":
    st.info("大丈夫です。まずは当事者の「今の状態」を一言で書いてみましょう")