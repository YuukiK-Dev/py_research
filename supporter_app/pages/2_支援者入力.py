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
# 条件選択
# ----------------------------
# 研究用の比較条件を選ぶ
# 「ログなし」か「ログあり」のどちらか1つを選ぶ
condition = st.radio("条件", ["ログなし", "ログあり"])


# ----------------------------
# 入力フォーム
# ----------------------------
# with st.form(...) の中に書いた入力欄は、最後の保存ボタンが押されるまでまとめて扱われる
with st.form("supporter_input"):

    # 「開始」ボタン
    # これを押した瞬間の時刻を start_time に保存する
    if st.form_submit_button("開始"):
        # 現在時刻を秒で取得して保存
        st.session_state.start_time = time.time()

        # 前回の計測結果が残っていると困るので、いったん空にする
        st.session_state.decision_time_sec = None

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

    # フォーム全体を保存するボタン
    submitted = st.form_submit_button("保存")


# ----------------------------
# 保存ボタンが押された後の処理
# ----------------------------
if submitted:

    # 開始ボタンが押されていて start_time が入っている場合だけ時間を計測する
    if st.session_state.start_time is not None:
        # 保存した瞬間の時刻を取得
        end_time = time.time()

        # 終了時刻 - 開始時刻 で、意思決定にかかった秒数を計算
        # round(..., 2) で小数点2桁までに丸める
        decision_time = round(end_time - st.session_state.start_time, 2)

        # 計算した秒数を session_state に保存
        st.session_state.decision_time_sec = decision_time

    # action が空欄だけのときはエラーを表示して処理を止める
    if action.strip() == "":
        st.error("対応（action）は空欄にできません")
        st.stop()

    # 今の日時を取得
    now = datetime.now()

    # 1件ごとに重ならない record_id を作る
    record_id = uuid.uuid4().hex

    # 今回の入力内容を1行の表データにまとめる
    new_row = pd.DataFrame([{
        # 一意のID
        "record_id": record_id,

        # 保存日時（年月日＋時分秒）
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),

        # 日付だけ
        "date": now.strftime("%Y-%m-%d"),

        # 時刻だけ
        "time": now.strftime("%H:%M:%S"),

        # 支援者の種類
        "supporter": supporter,

        # 当事者の状態
        "seen_status": seen_status,

        # 対応内容（前後の空白を除去して保存）
        "action": action.strip(),

        # メモ内容（前後の空白を除去して保存）
        "memo": memo.strip(),

        # 数値化した不安度
        "anxiety": int(anxiety),

        # 不安度のラベル
        "anxiety_label": anxiety_label,

        # 困ったかどうか
        "hesitation": hesitation,

        # 専門機関に相談したいと思ったか
        "consult_need": consult_need,

        # 緊急度
        "urgency": int(urgency),

        # 意思決定にかかった秒数
        "decision_time_sec": st.session_state.decision_time_sec,

        # 研究条件（ログあり / ログなし）
        "condition": condition,

        # 心理的負担（1〜5）
        "mental_load": mental_load,
    }])

    # 既存の supporter_log シートを読み込む
    current = conn.read(worksheet="supporter_log", ttl=0)

    # もしシートが空なら、新しい1行だけをそのまま使う
    if current is None or len(current) == 0:
        combined = new_row

    # すでにデータがある場合
    else:
        # 重複している列名があれば除く
        current = current.loc[:, ~current.columns.duplicated()]

        # 新しい行にある列が、古いデータ側に無いときは列を追加しておく
        for col in new_row.columns:
            if col not in current.columns:
                current[col] = pd.NA

        # 既存データの下に新しい1行を追加
        combined = pd.concat([current, new_row], ignore_index=True)

    # supporter_log シート全体を更新する
    conn.update(worksheet="supporter_log", data=combined)

    # ----------------------------
    # 提案タイプの決定
    # ----------------------------
    # 不安度が高い場合は HIGH_SUPPORT
    if anxiety >= 3:
        suggestion_type = "HIGH_SUPPORT"

    # 不安度はそこまで高くないが、対応に困っているなら GUIDANCE
    elif hesitation == "はい":
        suggestion_type = "GUIDANCE"

    # それ以外は NORMAL
    else:
        suggestion_type = "NORMAL"

    # 後で提案表示に使うため、必要な値を session_state に保存しておく
    st.session_state.last_record_id = record_id
    st.session_state.last_created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.last_suggestion_type = suggestion_type
    st.session_state.last_seen_status = seen_status
    st.session_state.after_relief = 0

    # 保存成功メッセージを表示
    st.success("保存しました（supporter_log）")

    # 今回保存した1行を画面に表示
    st.dataframe(new_row)


# ----------------------------
# ログあり条件のときの表示
# ----------------------------
# 今は仮の表示だけ
# 将来ここに「過去ログ参照」処理を入れる
if condition == "ログあり":
    st.write("過去ログ表示（ここに既存のログ表示処理）")


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