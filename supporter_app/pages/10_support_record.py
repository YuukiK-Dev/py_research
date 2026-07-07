import streamlit as st

import openai
from openai import OpenAI


st.markdown(
    """
    <style>
        /* サイドバーのページ一覧を非表示にする */
        [data-testid="stSidebarNav"]{
            display:none;
        }

        /* Step1カード全体：グリーン */
        div.st-key-step1_card {
            background-color: #eaf7ea !important;
            border: 2px solid #8fd19e !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 14px rgba(80, 160, 100, 0.16) !important;
            padding: 18px !important;
            margin-bottom: 24px !important;
        }

        /* Step2カード全体：黄色 */
        div.st-key-step2_card {
            background-color: #fff7cc !important;
            border: 2px solid #facc15 !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 14px rgba(180, 140, 20, 0.14) !important;
            padding: 18px !important;
            margin-bottom: 24px !important;
        }

        /* Step3カード全体：水色 */
        div.st-key-step3_card {
            background-color: #e0f2fe !important;
            border: 2px solid #7dd3fc !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 14px rgba(56, 189, 248, 0.16) !important;
            padding: 18px !important;
            margin-bottom: 24px !important;
        }

        /* Step4カード全体：オレンジ */
        div.st-key-step4_card {
            background-color: #ffedd5 !important;
            border: 2px solid #fb923c !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 14px rgba(251, 146, 60, 0.16) !important;
            padding: 18px !important;
            margin-bottom: 24px !important;
        }

        /* Step5カード全体：むらさき */
        div.st-key-step5_card {
            background-color: #f3e8ff !important;
            border: 2px solid #c084fc !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 14px rgba(168, 85, 247, 0.16) !important;
            padding: 18px !important;
            margin-bottom: 24px !important;
        }

        /* Step6カード全体：ミント */
        div.st-key-step6_card {
            background-color: #dcfce7 !important;
            border: 2px solid #22c55e !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 14px rgba(34, 197, 94, 0.16) !important;
            padding: 18px !important;
            margin-bottom: 24px !important;
        }

        /* Step7カード全体：保存用のやさしいピンク */
        div.st-key-step7_card {
            background-color: #ffe4ef !important;
            border: 2px solid #f472b6 !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 14px rgba(244, 114, 182, 0.18) !important;
            padding: 18px !important;
            margin-bottom: 24px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
SHOW_AI_DEBUG = False

# 基本の対応例を画面に表示するかどうかを切り替える設定
# True : API未接続・開発中は表示する
# False : AI接続後・実証時は表示しない
SHOW_BASIC_ADVICE = True


# 開始時間をいれておく箱を用意する
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None

#condition を入れておく箱を用意する
if "condition" not in st.session_state:
    st.session_state["condition"] = ""

# ログインできたどうかを覚えておく箱を用意する
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

# ログインしたIDを覚えておく箱を用意する
if "participant_id" not in st.session_state:
    st.session_state["participant_id"] = ""

#困りごとのカテゴリーを入れておく箱
if "support_category" not in st.session_state:
    st.session_state["support_category"] = "選択してください"

# AI対応例の作成ボタンが押されたかを覚えておく箱
if "ai_advice_requested" not in st.session_state:
    st.session_state["ai_advice_requested"] = False

# AI対応例の本文を一時保存しておく箱
if "ai_advice_text" not in st.session_state:
    st.session_state["ai_advice_text"] = ""

#対応内容の入力を覚えておく箱
if "action_text" not in st.session_state:
    st.session_state["action_text"] = ""

#AI対応例がどこから作られたかを覚えておく箱
#例 : openai / basic_fallback
if "ai_advice_source" not in st.session_state:
    st.session_state["ai_advice_source"] = ""

#AI生成に失敗したときの理由を一時保存しておく箱
if "ai_error_message" not in st.session_state:
    st.session_state["ai_error_message"] = ""

#保存が完了したかを覚えて億箱
if "record_saved" not in st.session_state:
    st.session_state["record_saved"] = False


# ------------------------------
# 画面のタイトル表示
# ------------------------------
if not st.session_state["is_logged_in"]:
    st.title("AI支援ナビ")
    st.subheader("個別最適化支援アプリ")

# ------------------------------
# Google Sheets に接続する
# ここで、スプレッドシートを読み書きできるようにする
# ------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# ------------------------------
# ------------------------------
# users シートを読む
# ログインしていないときだけ、本人確認用に読み込む
# ------------------------------
if not st.session_state["is_logged_in"]:
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
# ログインしていないときだけ、IDとパスワード入力欄を表示する
# ------------------------------
if not st.session_state["is_logged_in"]:

    st.write("配付されたIDと配付されたパスワードを入力してください")

    participant_id = st.text_input("配付されたID")
    passcode = st.text_input("配付されたパスワード", type="password")

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
            st.error("配付されたIDと配付されたパスワードの両方を入力してください")
            st.stop()
            st.title("AI支援ナビ")
            st.caption("過去ログとAIヒントを参考に、次の対応を考えやすくする支援アプリです。")

            st.markdown(
            """
            <div style="
                border: 1.5px solid #f9a8d4;
                border-radius: 16px;
                padding: 12px 16px;
                margin: 10px 0 18px 0;
                background-color: #fff7fb;
                color: #374151;
            ">
                <b>ログインできました。</b><br>
                この画面では、Step1からStep7まで上から順番に入力します。<br>
                まずは「入力の全体の流れ」を確認してから、Step1へ進んでください。
            </div>
            """,
            unsafe_allow_html=True
        )

        # ------------------------------
        # ログイン後のヘッダー表示
        # ログイン後も、何のアプリか・何をする画面かが分かるようにする
        # ------------------------------
        st.title("AI支援ナビ")
        st.caption("過去ログとAIヒントを参考に、次の対応を考えやすくする支援アプリです。")

        st.markdown(
            """
            <div style="
                border: 1.5px solid #f9a8d4;
                border-radius: 16px;
                padding: 12px 16px;
                margin: 10px 0 18px 0;
                background-color: #fff7fb;
                color: #374151;
            ">
                <b>ログインできました。</b><br>
                この画面では、Step1からStep7まで上から順番に入力します。<br>
                まずは「はじめに：このアプリの使い方」を確認してから、Step1へ進んでください。
            </div>
            """,
            unsafe_allow_html=True
        )

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

        if not matched_user.empty:
            # st.success("ログイン成功")
            # st.write("ログインID:", input_id)

            st.session_state["start_time"] = time.time()

            # ログイン成功状態にする
            st.session_state["is_logged_in"] = True

            # ログインしたIDを保存する
            st.session_state["participant_id"] = input_id

            # usersシートのcondition列から、この人の条件を取り出す
            condition = matched_user.iloc[0]["condition"]

            # conditionが空なら、この先に進ませない
            if str(condition).strip() == "":
                st.error("このIDは現在使用できません。管理者へ連絡してください")
                st.stop()

            # あとで保存時に使えるように、session_stateに覚えておく
            # 前後の空白を消して、ログあり/ログなし判定を安定させる
            st.session_state["condition"] = str(condition).strip()

            # ログイン情報を保存できましたので、画面を再度読み込みしてstep1へ進む
            st.rerun()

        else:
            st.error("ID または パスワード が違います")

#ログインしていない場合は、ここで止める
if not st.session_state["is_logged_in"]:
    st.info("配布されたIDとパスワードを入力して、ログインしてください")
    st.stop()

    

    # --- ここから Day2（location入力） ---

#ログイン後の条件を表示　(分岐の準備)
# [必須]ログあり/ ログなし条件は、研究比較に必要な項目
#協力者には条件名や計測情報を見せないため、表示はしない
# st.info(f"現在の入力モードは： {st.session_state['condition']}")
# st.caption("※ログイン後から保存ボタンを押すまでの時間は、自動で記録されます")

# ------------------------------
# 入力の進行状況を計算する
# ------------------------------
progress_step = 2
progress_label = "Step3を選んでください"

if st.session_state["support_category"] != "選択してください":
    progress_step = 3
    progress_label = "Step4の対応内容へ"

if st.session_state["action_text"].strip() != "":
    progress_step = 5
    progress_label = "Step5を入力中"

if st.session_state["support_category"] == "支援者自身が疲れている":
    progress_step = 5
    progress_label = "Step5を入力中"

if st.session_state["ai_advice_text"].strip() != "":
    progress_step = 6
    progress_label = "Step7で保存へ"

if st.session_state["record_saved"]:
    progress_step = 7
    progress_label = "保存完了"

progress_percent = int(progress_step / 7 * 100)



st.markdown(
    f"""
<div style="position: fixed; top: 120px; left: calc(50% + 390px); z-index: 9999; background-color: #ffffff; border: 1.5px solid #f472b6; border-radius: 18px; padding: 12px 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.14); font-size: 13px; color: #374151; font-weight: bold; width: 150px;">
    <div style="margin-bottom: 6px;">入力状況</div>
    <div style="font-size: 12px; margin-bottom: 8px;">{progress_label}</div>
    <div style="width: 100%; height: 8px; background-color: #fce7f3; border-radius: 999px; overflow: hidden; margin-bottom: 6px;">
        <div style="width: {progress_percent}%; height: 100%; background-color: #f472b6; border-radius: 999px;"></div>
    </div>
    <div style="font-size: 11px; color: #6b7280;">{progress_step} / 7</div>
</div>
    """,
    unsafe_allow_html=True
)

# ------------------------------
# はじめに：入力の全体の流れ
# 利用者が最初に全体像をつかめるようにする説明カード
# ------------------------------
with st.container(border=True):
    st.markdown("#### はじめに：入力の全体の流れ")

    st.markdown(
        """
        このアプリは、支援場面の状況を上から順番に記録していくアプリです。

        まず、基本情報を選び、現在の状態、困りごと、対応内容、
        不安や負担感を入力します。

        最後にAIヒントを確認し、入力内容を保存します。

        詳しい入力内容は、各Stepの「ここで入力すること」を確認してください。
        """
    )

    st.markdown(
        """
        <div style="
            border: 1px solid #fbcfe8;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 12px 0 4px 0;
            background-color: #fff7fb;
            color: #374151;
        ">
            <b>入力の順番</b><br>
            Step1：基本情報<br>
            Step2：現在の状態<br>
            Step3：AI支援ナビ<br>
            Step4：対応内容の記録<br>
            Step5：不安・負担感・対応結果<br>
            Step6：AIからの対応ヒント<br>
            Step7：入力内容を保存
        </div>
        """,
        unsafe_allow_html=True
    )




# ------------------------------
# Step1：基本情報
# 場所と支援者の立場を入力するカード
# ------------------------------
with st.container(border=True,key="step1_card"):

    st.markdown(
    """
    <div style="
        background-color: #fff0f6;
        border: 1.5px solid #f9a8d4;
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 16px;
    ">
        <div style="
            font-size: 24px;
            font-weight: bold;
            color: #374151;
        ">
            🌸 Step1：基本情報
        </div>
        <div style="
            font-size: 14px;
            color: #6b7280;
            margin-top: 6px;
        ">
            まず、今回の支援場面について、場所とあなたの立場を選んでください。
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

    st.markdown(
        """
        <div style="
            border: 1px solid #fbcfe8;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0 16px 0;
            background-color: #fff7fb;
            color: #374151;
        ">
            <b>ここで入力すること</b><br>
            どこで、どの立場で支援している場面なのかを記録します。
        </div>
        """,
        unsafe_allow_html=True
    )

    col_location, col_supporter = st.columns(2)

    with col_location:
        location = st.radio(
            "📍 場所を選んでください",
            ["自宅", "学校", "職場", "その他"]
        )

    with col_supporter:
        supporter = st.radio(
            "👤 あなたの立場を選んでください",
            ["家族", "支援員", "教員", "その他"]
        )



# ------------------------------
# Step2：現在の状態
# 子供や利用者さんの状態を選ぶカード
# ------------------------------
with st.container(border=True,key="step2_card"):

    st.markdown("### 🌼 Step2：現在の状態")
    st.caption("今、子供や利用者さんがどのような状態かを選んでください。")

    st.markdown(
        """
        <div style="
            border: 1px solid #fde68a;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0 16px 0;
            background-color: #fffbeb;
            color: #374151;
        ">
            <b>ここで入力すること</b><br>
            今の様子に一番近い状態を1つ選びます。
            迷う場合は、完全に一致していなくても近いものを選んでください。
        </div>
        """,
        unsafe_allow_html=True
    )

    status = st.radio(
        "🌱 子供や利用者さんの今の状態を選んでください",
        ["安定", "少し不安", "しんどい", "パニック"]
    )


#ログありの人だけ過去ログを表示する
if st.session_state["condition"] == "ログあり":
    with st.expander("参考：過去の対応ログ",expanded=False):

        #条件の明示（研究的に重要）
        # st.caption("※あなたは「ログあり」条件です")
        st.info(
            f"過去ログは、以前の似た場面で参考になった対応を見返すための情報です。\n\n"
            f"今は「{status}」に近い状態で、以前うまくいった対応例を表示しています。\n\n"
            "まったく同じ対応をする必要はありません。今回の状況に合わせて、参考にしてください。"
        )
        

        #supporter_logを読み込む
        past_log = conn.read(worksheet = "supporter_log",ttl=0)
        past_log = pd.DataFrame(past_log)

     
        #participant_id列を文字にそろえて空白を消す
        past_log["participant_id"] = past_log["participant_id"].astype(str).str.strip()

        #seen_status列を文字にそろえて空白を消す
        past_log["seen_status"] = past_log["seen_status"].astype(str).str.strip()

        # is_success列を文字にそろえて空白を消す
        past_log["is_success"] = past_log["is_success"].astype(str).str.strip()

        #自分のログだけに絞る
        past_log = past_log[past_log["participant_id"] == st.session_state["participant_id"]]
    

        #今選んでいる状態と同じログだけに絞る
        past_log = past_log[past_log["seen_status"] == status]
        
        #参考にできるログだけに絞る
        #「うまくいったと思う」「少しうまくいったと思う」を成功寄りのログとして扱う
        success_values = [
            "うまくいったと思う",
            "少しうまくいったと思う"
        ]

        past_log = past_log[past_log["is_success"].isin(success_values)]
        

        #成功したログの件数を表示
        st.write(f"参考にできる対応例が {len(past_log)} 件あります")

        #新しい順に並べる（最新が上）
        past_log = past_log.sort_values("created_at",ascending=False)

        if past_log.empty:
            # 同じ状態のログが1件もないとき
            st.info("参考にできる過去の対応例は、まだありません\n\n(ここは、保存していただくと次回より表示されるようになります)")
            st.write("表示された状況を見て、どう対応するかを入力してください")
            #最小限の支援（ログがないときだけ）
            st.write("ヒント:まずは落ち着いて,様子を確認しましょう")
        else:
            #上から5件だけ表示（協力者に読みやすい形で表示する
            for _, row in past_log.head(5).iterrows():
                st.markdown("---")
                st.write("日時：", row["created_at"])
                st.write("状態：", row["seen_status"])
                st.write("対応例：", row["action"])
                st.write("その時の負担感：", row["mental_load"])
                


    

# 今選ばれている値を確認表示
# st.write("選択された状態：", status)

# --- ここまで ---

# --- ここから Day2（action入力） ---

# ------------------------------
# Step3：AI支援ナビ
# 困りごとのカテゴリを選ぶカード
# ------------------------------
with st.container(border=True, key="step3_card"):

    st.markdown("### 🤖 Step3：AI支援ナビ")
    st.caption("今の困りごとを整理し、対応のヒントを選びやすくするためのステップです。")

    st.markdown(
        """
        <div style="
            border: 1px solid #bae6fd;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0 16px 0;
            background-color: #f0f9ff;
            color: #374151;
        ">
            <b>ここで入力すること</b><br>
            今の困りごとをカテゴリに分けて、対応を考えやすくします。
            AIに答えを任せるのではなく、支援者が次の対応を考えるための手がかりを整理します。
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💬 声かけに迷う", use_container_width=True):
            st.session_state["support_category"] = "声かけに迷う"
            st.session_state["ai_advice_requested"] = False
            st.session_state["ai_advice_text"] = ""
            st.session_state["ai_advice_source"] = ""
            st.session_state["ai_error_message"] = ""

    with col2:
        if st.button("🌊 感情が高ぶっている", use_container_width=True):
            st.session_state["support_category"] = "感情が高ぶっている"
            st.session_state["ai_advice_requested"] = False
            st.session_state["ai_advice_text"] = ""
            st.session_state["ai_advice_source"] = ""
            st.session_state["ai_error_message"] = ""

    col3, col4 = st.columns(2)

    with col3:
        if st.button("📅 予定変更で混乱している", use_container_width=True):
            st.session_state["support_category"] = "予定変更で混乱している"
            st.session_state["ai_advice_requested"] = False
            st.session_state["ai_advice_text"] = ""
            st.session_state["ai_advice_source"] = ""
            st.session_state["ai_error_message"] = ""

    with col4:
        if st.button("🏠 外出を嫌がっている", use_container_width=True):
            st.session_state["support_category"] = "外出を嫌がっている"
            st.session_state["ai_advice_requested"] = False
            st.session_state["ai_advice_text"] = ""
            st.session_state["ai_advice_source"] = ""
            st.session_state["ai_error_message"] = ""

    if st.button("🫧 支援者自身が疲れている", use_container_width=True):
        st.session_state["support_category"] = "支援者自身が疲れている"
        st.session_state["ai_advice_requested"] = False
        st.session_state["ai_advice_text"] = ""
        st.session_state["ai_advice_source"] = ""
        st.session_state["ai_error_message"] = ""


support_category = st.session_state["support_category"]

if support_category != "選択してください" and SHOW_BASIC_ADVICE:
    st.markdown(
        f"""
        <div style="
            border: 1px solid #dbeafe;
            border-radius: 16px;
            padding: 14px 16px;
            margin: 12px 0 16px 0;
            background-color: #eff6ff;
            color: #1f2937;
        ">
            <div style="font-size: 14px; color: #2563eb; font-weight: bold;">
                ✅ 選択中の困りごと
            </div>
            <div style="font-size: 18px; font-weight: bold; margin-top: 6px;">
                {support_category}
            </div>
            <div style="font-size: 14px; color: #374151; margin-top: 6px;">
                この内容に合わせて、対応例とAI対応例のヒントを表示します。
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

if support_category != "選択してください" and SHOW_BASIC_ADVICE:

    st.markdown("#### 今できる対応のヒント")

    if support_category == "声かけに迷う":
        st.info(
            "💬 声かけに迷うとき\n\n"
            "・短い言葉で声をかける\n\n" 
            "・一度に多く説明しない\n\n"
            "・相手の反応を待つ"
        )

    elif support_category == "感情が高ぶっている":
        st.info(
            "🌊 感情が高ぶっているとき\n\n"
            "・自分の安全を確認する\n\n"
            "・無理に説得しない\n\n"
            "・落ち着ける場所や時間を確保する\n\n" 
            "・好きな物などを見せる"
        )

        st.markdown("#### 🔔 安全確認・共有の参考")
        st.caption("※感情が高ぶっている場面で、支援者が一人で抱え込まないための参考情報です")
        st.info(
            "本人や周囲の安全を確認しながら、支援者が一人で対応し続けないことも大切です。\n\n"
            "・危険がありそうな場合は、距離を取り、安全な場所を確保する\n\n"
            "・対応を一人で続けるのが難しい場合は、他の支援者や責任者に共有する\n\n"
            "・所属先の緊急時対応ルールがある場合は、それに従う"
        )

    elif support_category == "予定変更で混乱している":
        st.info(
            "📅 予定変更で混乱している\n\n"
            "・絵や文字を書いて見える形にする\n\n"
            "・次に何をするかを1つずつ示す\n\n"
            "・変更点を短く伝える"
        )

    elif support_category == "外出を嫌がっている":
        st.info(
            "🏠 外出を嫌がっている\n\n"
            "・理由を急いで聞き出さない\n\n"
            "・外出の目的を短く伝える\n\n"
            "・小さな一歩から提案する"
        )

    elif support_category == "支援者自身が疲れている":
        st.info(
            "🫧 支援者自身が疲れている\n\n"
            "ここまで対応しようとしていること自体が、大切な支援です。\n\n"
            "今すぐ完璧に対応しようとせず、まずは支援者自身の負担を少し軽くする方法を考えてみてください。"
        )
        
        st.markdown("#### 🫧 支援者自身のための選択肢")
        st.caption("※今の自分に近いものを選んで確認してください")

        self_care_choice = st.radio(
            "今の自分に近いものを選んでください",
            [
                "少し休む・距離を取る",
                "誰かに共有する",
                "あとで相談できるように記録する",
            ]
        )

        if self_care_choice == "少し休む・距離を取る":
            st.info(
                "🫧 少し休む・距離を取る\n\n"
                "今すぐすべてを解決しようとしなくても大丈夫です。\n\n"
                "可能であれば、少し距離を取る、深呼吸をする、数分だけ落ち着く時間をつくるなど、自分自身を整える行動を検討してください。"
                )

        elif self_care_choice == "誰かに共有する":
            st.info(
                "🤝 誰かに共有する\n\n"
                "一人で抱え込まないことも、大切な支援です。\n\n"
                "必要に応じて、他の支援者、責任者、教員、家族など、普段から相談できる人に状況を共有してください。"
                )

        elif self_care_choice == "あとで相談できるように記録する":
            st.info(
                "📝 あとで相談できるように記録する\n\n"
                "今すぐ相談できない場合は、あとで振り返れるように、状況を短く残しておくことも役立ちます。\n\n"
                "「何が起きたか」「自分が困ったこと」「次に相談したいこと」を簡単に記録しておくと、後で共有しやすくなります。"
                )
    

# ------------------------------
# Step4：対応内容の記録
# 実際の対応、または自分ならどう対応するかを書くカード
# ------------------------------
with st.container(border=True, key="step4_card"):

    st.markdown("### 📝 Step4：対応内容の記録")
    st.caption("AI支援ナビや対応のヒントを参考にして、この場面での対応内容を記録してください。")

    st.markdown(
        """
        <div style="
            border: 1px solid #fed7aa;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0 16px 0;
            background-color: #fff7ed;
            color: #374151;
        ">
            <b>ここで入力すること</b><br>
            実際に行った対応、または自分ならどう対応するかを短く書きます。
            完璧な文章でなくても大丈夫です。
        </div>
        """,
        unsafe_allow_html=True
    )

    # 支援者自身が疲れている場合は、対応内容を無理に書かせない
    if support_category == "支援者自身が疲れている":
        action_label = "[任意]今の自分にできそうなこと、または記録しておきたいことを書いてください（空欄でも大丈夫です）"
    else:
        action_label = "[必須]この場面で、どのように対応しますか？"

    action = st.text_area(
        action_label,
        key="action_text"
    )

    memo = st.text_area(
        "[任意]補足メモがあれば入力してください（空欄でも大丈夫です）",
        height=100
    )

# ------------------------------
# Step5：不安・負担感・対応結果
# 評価項目を入力するカード
# ------------------------------
with st.container(border=True, key="step5_card"):

    st.markdown("### 📊 Step5：不安・負担感・対応結果")
    st.caption("この場面で感じた不安や負担、対応結果について選んでください。")

    st.markdown(
        """
        <div style="
            border: 1px solid #d8b4fe;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0 16px 0;
            background-color: #faf5ff;
            color: #374151;
        ">
            <b>ここで入力すること</b><br>
            この場面で感じた不安、迷い、相談の必要性、負担感、対応結果を選びます。
            直感的に近いものを選んでください。
        </div>
        """,
        unsafe_allow_html=True
    )

    anxiety = st.radio(
        "[必須]この場面で、対応を考えるときの不安はどのくらいですか？",
        [
            "0:ぜんぜん大丈夫（見通しばっちり）",
            "1:ちょっとドキドキする",
            "2:まあまあ不安",
            "3:かなり不安",
            "4:パニックになりそう！"
        ]
    )

    hesitation = st.radio(
        "この場面で対応に迷いはありましたか？",
        ["はい", "いいえ"]
    )

    consult_need = st.radio(
        "この場面について、誰かに相談したいと思いますか？",
        ["はい", "いいえ"]
    )

    if consult_need == "はい":
        consult_who = st.radio(
            "[任意]相談するとしたら、誰に相談しますか？",
            ["家族", "支援員", "教員", "その他"]
        )
    else:
        consult_who = ""

    urgency = st.radio(
        "この場面では、どれくらい急いで対応・相談する必要がありますか？",
        [
            "低い（様子を見てもよい）",
            "中くらい（今日中には対応したい）",
            "高い（すぐに対応・相談したい）"
        ]
    )

    mental_load = st.radio(
        "[必須]この場面で感じた心理的な負担はどのくらいありましたか？",
        [
            "1:ほとんど負担はない",
            "2:少し負担がある",
            "3:ある程度負担がある",
            "4:かなり負担がある",
            "5:非常に負担が大きい"
        ]
    )

    is_success = st.radio(
        "[必須]この場面での対応について、あなた自身はどのように感じましたか？",
        [
            "うまくいったと思う",
            "少しうまくいったと思う",
            "どちらともいえない",
            "あまりうまくいかなかったと思う",
            "うまくいかなかったと思う"
        ]
    )

# 入力された内容を確認表示
# st.write("入力された対応内容：", action)

#AI支援ナビ：AIに渡す文章を作る関数

def build_ai_prompt(ai_input_data):
    # AI対応例を作成するためのプロンプト文を作る関数です
    # まだAIに接続しません

    place = ai_input_data.get("place","未入力")
    supporter_role = ai_input_data.get("supporter_role","未入力")
    current_state = ai_input_data.get("current_state","未入力")
    support_category = ai_input_data.get("support_category","未入力")
    anxiety_level = ai_input_data.get("anxiety_level","未入力")
    wants_consultation = ai_input_data.get("wants_consultation","未入力")
    consultation_target = ai_input_data.get("consultation_target","未入力")
    urgency_level = ai_input_data.get("urgency_level","未入力")
    mental_load = ai_input_data.get("mental_load","未入力")

    ai_prompt = f"""
あなたは、支援者の意思決定を補助するAIです。

以下の情報をもとに、支援者が次に取りやすい対応例を作成してください。

[入力情報]
・場所 : {place}
・支援者の立場 : {supporter_role}
・現在の状態 : {current_state}
・困りごとのカテゴリ : {support_category}
・不安度 : {anxiety_level}
・相談希望 : {wants_consultation}
・相談先 : {consultation_target}
・緊急度 : {urgency_level}
・心理的負担 : {mental_load}

[出力して欲しい内容]
1. まず最初に確認すること
2. 支援者がすぐに取れる対応例
3. 無理をしないための注意点
4. 必要に応じて相談する相手

[注意]
・医療的判断や専門的診断を行わないでください。
・断定的な言い方は避けてください。
・支援者の心理的負担を増やさない、やさしい表現にしてください。
・具体的で短く、実行しやすい対応例にしてください。
"""
    return ai_prompt

def get_basic_advice(ai_input_data):
    """
    AI対応例を作成するための仮関数です。
    まだOpenAI APIには接続しません。
    選択された困りごとカテゴリごとに、仮の対応例を返します
    """

    # 選択された困りごとのカテゴリを取り出す
    support_category = ai_input_data.get("support_category","未選択")

    if support_category == "声かけに迷う":
        ai_advice = """
 [AI対応例 : 声かけに迷う]

 1. まず最初に確認すること\n\n
&emsp;・相手が今、話を聞ける状態かを確認する\n\n
&emsp;・表情や姿勢を見て、無理に話しかけない方がよいかを見る\n\n

2. 支援者がすぐに取れる対応例\n\n
&emsp;・短い言葉で、1つずつ伝える\n\n
&emsp;・「今はこれをします」と、次の行動だけを伝える\n\n
&emsp;・返事を急がせず、少し待つ\n\n

3. 無理をしないための注意点\n\n
&emsp;・一度に説明しすぎない\n\n
&emsp;・正しい言葉を探しすぎて、支援者自身が疲れないようにする\n\n

4. 必要に応じて相談する相手\n\n
&emsp;・家族、支援員、教員など、普段の様子を知っている人に相談する\n\n
"""

    elif support_category == "感情が高ぶっている":
        ai_advice = """
【AI対応例：感情が高ぶっている】

1. まず最初に確認すること\n\n
&emsp;・本人と周囲の安全を確認する\n\n
&emsp;・大きな音、人の多さ、急な声かけなど刺激が強くないかを見る\n\n

2. 支援者がすぐに取れる対応例\n\n
&emsp;・無理に説得しようとしない\n\n
&emsp;・少し距離を取り、落ち着ける時間を作る\n\n
&emsp;・短く落ち着いた声で「ここで少し待ちます」と伝える\n\n

3. 無理をしないための注意点\n\n
&emsp;・支援者が一人で抱え込まない\n\n
&emsp;・危険がある場合は、早めに他の支援者を呼ぶ\n\n

4. 必要に応じて相談する相手\n\n
&emsp;・近くの支援員、教員、施設職員などに相談する\n\n
"""

    elif support_category == "予定変更で混乱している":
        ai_advice = """
【AI対応例：予定変更で混乱している】

1. まず最初に確認すること\n\n
&emsp;・何が変わったことで混乱しているのかを確認する\n\n
&emsp;・本人が今、文字や絵を見られる状態かを見る\n\n

2. 支援者がすぐに取れる対応例\n\n
&emsp;・変更前と変更後を、紙や画面に書いて見える形にする\n\n
&emsp;・次にすることを1つだけ伝える\n\n
&emsp;・「まずこれ、その次にこれ」と順番を短く示す\n\n

3. 無理をしないための注意点\n\n
&emsp;・急いで納得させようとしない\n\n
&emsp;・説明を増やしすぎず、情報を小さく分ける\n\n

4. 必要に応じて相談する相手\n\n
&emsp;・予定を知っている職員、教員、家族に確認する\n\n
"""

    elif support_category == "外出を嫌がっている":
        ai_advice = """

【AI対応例：外出を嫌がっている】

1. まず最初に確認すること\n\n
 &emsp;・体調が悪いのか、不安が強いのか、理由を急がずに確認する\n\n
 &emsp;・外出先、移動、時間、人混みなど、負担になりそうな点を見る\n\n

2. 支援者がすぐに取れる対応例\n\n
 &emsp;・外出の目的を短く伝える\n\n
 &emsp;・「玄関まで」「靴を履くところまで」など小さな一歩に分ける\n\n
 &emsp;・無理に外へ出そうとせず、選択肢を出す\n\n

3. 無理をしないための注意点\n\n
 &emsp;・外出できるかどうかだけを成功・失敗で見ない\n\n
 &emsp;・支援者自身も焦りすぎない\n\n

4. 必要に応じて相談する相手\n\n
 &emsp;・家族、支援員、教員など、本人の普段の様子を知っている人に相談する\n\n
"""
    elif support_category == "支援者自身が疲れている":
        ai_advice = """

【AI対応例：支援者自身が疲れている】

1. まず最初に確認すること\n\n
&emsp;・今すぐ一人で対応し続ける必要があるかを確認する\n\n
&emsp;・自分の疲れ、不安、焦りが強くなっていないかを見る\n\n

2. 支援者がすぐに取れる対応例\n\n
&emsp;・一度深呼吸し、少し距離を取る\n\n
&emsp;・「今すぐ全部解決しなくてよい」と考える\n\n
&emsp;・必要なことを1つだけにしぼる\n\n

3. 無理をしないための注意点\n\n
&emsp;・支援者が倒れるほど頑張ることは、よい支援とは限らない\n\n
&emsp;・一人で抱え込まず、相談することも支援の一部と考える\n\n

4. 必要に応じて相談する相手\n\n
&emsp;・家族、施設職員、学校関係者、相談支援事業所、必要に応じて医療機関\n\n
"""

    else:
        ai_advice = """
困りごとのカテゴリがまだ選択されていません。

先にカテゴリを選ぶと、AI対応例を表示できます。
"""
    return ai_advice

def get_openai_advice(ai_input_data):
    """
    OpenAI APIでAI対応例を作成する関数です。
    成功した場合は、OpenAIが生成した対応例の文章を返します
    """
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    ai_prompt = build_ai_prompt(ai_input_data)

    response = client.responses.create(
        model="gpt-5.5",
        input=ai_prompt,
    )

    ai_advice = response.output_text

    if ai_advice is None or ai_advice.strip() == "":
        raise ValueError("OpenAIから空の応答が返りました")

    return ai_advice.strip()


def generate_ai_advice(ai_input_data):
    """
    AI対応例を作成する入口となる関数です。
    OpenAI APIを試し、失敗した場合は基本の仮対応例に戻します。
    """

    try:
        ai_advice = get_openai_advice(ai_input_data)

        st.session_state["ai_advice_source"] = "openai"
        st.session_state["ai_error_message"] = ""

        return ai_advice

    except Exception as e:
        st.session_state["ai_advice_source"] = "basic_fallback"
        st.session_state["ai_error_message"] = str(e)

        return get_basic_advice(ai_input_data)

# ------------------------------
# Step6：AIからの対応ヒント
# 入力内容をもとにAI対応例を表示するカード
# ------------------------------
with st.container(border=True, key="step6_card"):

    st.markdown("### 🤖 Step6：AIからの対応ヒント")
    st.caption("入力内容をもとに、次の対応を考えるヒントを確認します。")

    st.markdown(
        """
        <div style="
            border: 1px solid #86efac;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0 16px 0;
            background-color: #f0fdf4;
            color: #374151;
        ">
            <b>ここで確認すること</b><br>
            AIヒントは、支援者の判断を置き換えるものではありません。
            ここまでの入力内容をもとに、次の対応を考えるための参考情報として確認します。
            必要に応じて、過去ログ、自分の経験、周囲への相談と合わせて使ってください。
        </div>
        """,
        unsafe_allow_html=True
    )

    ai_consult_target = consult_who if consult_need == "はい" else "なし"

    # AIに渡す情報を1つの箱にまとめる
    ai_input_data = {
        "place": location,
        "supporter_role": supporter,
        "current_state": status,
        "support_category": support_category,
        "anxiety_level": anxiety,
        "wants_consultation": consult_need,
        "consultation_target": ai_consult_target,
        "urgency_level": urgency,
        "mental_load": mental_load,
    }

    # まとめた情報をもとに、AIへ渡す文章を作る
    ai_prompt = build_ai_prompt(ai_input_data)

    if SHOW_AI_DEBUG:

        st.markdown("#### AIに渡す予定の情報（確認用）")
        st.caption("※開発者確認用です。実証時は通常表示しません。")

        with st.expander("AIに渡す予定の情報を確認する", expanded=False):

            st.markdown("#### 入力データ")

            st.info(
                f"場所 : {location}\n\n"
                f"支援者の立場 : {supporter}\n\n"
                f"現在の状態 : {status}\n\n"
                f"困りごとのカテゴリ : {support_category}\n\n"
                f"不安度 : {anxiety}\n\n"
                f"相談希望 : {consult_need}\n\n"
                f"相談先 : {ai_consult_target}\n\n"
                f"緊急度 : {urgency}\n\n"
                f"心理的負担 : {mental_load}\n\n"
            )

            st.markdown("#### AIに渡すプロンプト")
            st.text(ai_prompt)

    if support_category != "選択してください":

        if st.button("🤖 AI対応例を作成する", use_container_width=True):
            st.session_state["ai_advice_requested"] = True

            # AI対応例がまだ作成されていない場合だけ作成する
            if st.session_state["ai_advice_text"] == "":
                ai_advice = generate_ai_advice(ai_input_data)
                st.session_state["ai_advice_text"] = ai_advice

        if st.session_state["ai_advice_requested"] and st.session_state["ai_advice_text"] != "":

            st.markdown(
                """
                <div style="
                    border: 1px solid #86efac;
                    border-radius: 14px;
                    padding: 14px 16px;
                    margin: 16px 0 8px 0;
                    background-color: #f0fdf4;
                    color: #374151;
                ">
                    <b>🤖 AI対応例</b><br>
                    この対応例は、支援者が次の行動を考えるためのヒントです。
                    医療的判断や診断ではありません。
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(st.session_state["ai_advice_text"])

            if st.session_state["ai_advice_source"] == "basic_fallback":
                st.caption("※OpenAI APIが利用できない場合は、基本の対応例を表示しています。")

    else:
        st.warning("AI対応例を表示するには、先にStep3で困りごとのカテゴリを選んでください。")

# --- ここまで ---

# --- ここから 保存ボタン（まだSheetsには保存しない） ---

# ------------------------------
# Step7：保存
# 入力内容をGoogle Sheetsに保存するカード
# ------------------------------
with st.container(border=True, key="step7_card"):

    st.markdown("### 💾 Step7：入力内容を保存")
    st.caption("ここまで入力した内容を確認し、最後に保存してください。")

    st.markdown(
        """
        <div style="
            border: 1px solid #f9a8d4;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0 16px 0;
            background-color: #fff7fb;
            color: #374151;
        ">
            <b>最後にすること</b><br>
            入力が終わったら、下の保存ボタンを押してください。
            保存後、今回の記録がGoogle Sheetsに追加されます。
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state["record_saved"]:
        st.success("保存しました。ご協力ありがとうございました")

    else:
        if st.button("💾 保存する", use_container_width=True):

            #ログイン前・計測開始前なら保存させない
            if st.session_state["start_time"] is None:
                st.error("先にログインしてください")
                st.stop()

            #conditionが空なら保存させない
            if st.session_state["condition"] == "":
                st.error("条件が取得できていません。もう一度ログインしてください")
                st.stop()

            if support_category == "選択してください":
                st.error("困りごとのカテゴリを選択してください")
                st.stop()

            #支援者自身が疲れている場合以外は、対応内容を必須にする
            if support_category != "支援者自身が疲れている" and action.strip() == "":
                st.error("対応内容を入力してください.実際の対応、または自分ならどう対応するかを書いてください")
                st.stop()

            # 今の時間を作る
            now = pd.Timestamp.now(tz="Asia/Tokyo").strftime("%Y-%m-%d %H:%M:%S")

            # 既存データを読み込み
            old_data = conn.read(worksheet="supporter_log", ttl=0)

            #1件ごとの記録IDを作る
            record_id = "R" + str(pd.Timestamp.now().timestamp()).replace(".","")

            #判断にかかった秒数 小数点2桁にする
            decision_time = round(time.time() - st.session_state["start_time"],2)

            # 対応結果を分析しやすいように数値へ変換する
            success_score_map = {
                "うまくいったと思う": 5,
                "少しうまくいったと思う": 4,
                "どちらともいえない": 3,
                "あまりうまくいかなかったと思う": 2,
                "うまくいかなかったと思う": 1
            }
            is_success_score = success_score_map[is_success]

            #今回追加する1行を作る
            new_data = pd.DataFrame([{
                "record_id": record_id,
                "created_at": now,
                "participant_id": st.session_state["participant_id"],
                "supporter": supporter,
                "seen_status": status,
                "support_category": support_category,
                "ai_advice_text": st.session_state["ai_advice_text"],
                "ai_advice_source": st.session_state["ai_advice_source"],
                "ai_error_message": st.session_state["ai_error_message"],
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
                "is_success_score": is_success_score,
            
                }])

            # 新しいデータを追加
            df = pd.concat([old_data, new_data],ignore_index=True)

            # Sheetsに書き込み
            conn.update(worksheet="supporter_log",data=df)

            st.session_state["record_saved"] = True
            st.rerun()

        # if consult_need == "はい" and consult_who=="家族":
        #     st.write("家族に相談する判断をしました")

# --- ここまで ---