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

# ログインできたどうかを覚えておく箱を用意する
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

# ログインしたIDを覚えておく箱を用意する
if "participant_id" not in st.session_state:
    st.session_state["participant_id"] = ""



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
st.write("配付された_id と 配付されたパスワード を入力してください")

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
        st.error("配付された_id と配付されたパスワードの両方を入力してください")
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

    if not matched_user.empty:
        st.success("ログイン成功")
        # st.write("ログインID:", input_id)
        st.session_state["start_time"] = time.time()

        # ログイン成功状態にする
        st.session_state["is_logged_in"] = True

        # ログインしたIDを保存する
        st.session_state["participant_id"] = input_id

    

        #userシートのcondition列から、この人の条件を取り出す
        condition = matched_user.iloc[0]["condition"]

         #conditionが空なら、この先に進ませない
        if str(condition).strip() == "":
            st.error("このIDは現在使用できません。管理者へ連絡してください")
            st.stop()

        #あとで保存時に使えるように、session_stateに覚えておく
        # 前後の空白を消して、ログあり/ログなし判定を安定させる
        st.session_state["condition"] = str(condition).strip()

       

        #いま取得できたcondition　を確認表示する
        # st.write("condition:", condition)
        # st.write("conditionの中身確認:", repr(condition))

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

   

st.subheader("Step1：基本情報")
st.caption("まず、今回の支援場面について基本情報を選んでください")

# ラジオボタンで場所を選ぶ
# radio = 選択式ボタン（1つだけ選べる）
location = st.radio(
    "場所を選んでください",
    ["自宅", "学校", "職場", "その他"]
)
# 今選ばれている値を確認表示
# st.write("選択された場所：", location)

# --- ここまで ---

# --- ここから supporter入力 ---

# st.subheader("Step1.5：支援者の種類を選択")
supporter = st.radio(
    "あなたの立場を選んでください",
    ["家族", "支援員", "教員","その他"]
    )

# st.write("選択された支援者：", supporter)

# --- ここまで ---



# --- ここから Day2（status入力） ---

st.subheader("Step2：現在の状態")
st.caption("今、子供や利用者さんがどのような状態かを選んでください")

# ラジオボタンで状態を選ぶ
status = st.radio(
    "[必須]子供や利用者さんの今の状態を選んでください",
    ["安定", "少し不安", "しんどい", "パニック"]
)

#ログありの人だけ過去ログを表示する
if st.session_state["condition"] == "ログあり":
    st.subheader("参考：過去の対応ログ")

    #条件の明示（研究的に重要）
    # st.caption("※あなたは「ログあり」条件です")
    st.write(f"※「{status}」に近い状態で、以前うまくいった対応例を表示しています")
    

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
        st.info("参考にできる過去の対応例は、まだありません")
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

st.subheader("Step3：AI支援ナビ")
st.caption("困りごとを選ぶと、対応のヒントを表示します")
st.write("今の困りごとに近いものを1つ選んでください")

support_category = st.selectbox(
    "困りごとのカテゴリを選んでください",
    [
        "選択してください",
        "声かけに迷う",
        "感情が高ぶっている",
        "予定変更で混乱している",
        "外出を嫌がっている",
        "支援者自身が疲れている",
    ]
)

if support_category != "選択してください":

    st.markdown("#### 対応例")

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
            "・一度、ゆっくり深呼吸をする\n\n"
            "・無理に一人で抱え込まない\n\n"
            "・必要に応じて相談先や他の支援者に相談する"
        )
        
        st.markdown("#### 相談先の参考情報")
        st.info("一人で抱え込まず、必要に応じて家族、施設職員、学校関係者、相談支援事業所、医療機関などに相談してください")

    

# テキスト入力（複数行）
#[必須]対応内容は、保存時に空欄チェックをしているため必ず入力してもらう
action = st.text_area("[必須]この場面で、どのように対応しますか？")

# [任意]補足メモは、必要な場合だけ入力してもらう
memo = st.text_area("[任意]補足メモがあれば入力してください（空欄でも大丈夫です）", height=100)

st.subheader("Step4：不安・負担感・対応結果")
st.caption("この場面で感じた不安や負担、対応結果について選んでください")

anxiety = st.radio(
    "[必須]この場面で、対応を考えるときの不安はどのくらいですか？",
    ["0:ぜんぜん大丈夫（見通しばっちり）", "1:ちょっとドキドキする", "2:まあまあ不安", "3:かなり不安", "4:パニックになりそう！"]
    )

hesitation = st.radio(
    "この場面で対応に迷いはありましたか？",
    ["はい", "いいえ"]
    )

consult_need = st.radio(
    "この場面について、誰かに相談したいと思いますか？",
    ["はい","いいえ"]
)

if consult_need == "はい":
    consult_who = st.radio(
        "[任意]相談するとしたら、誰に相談しますか？",
        ["家族", "支援員", "教員", "その他"]
    )
else:
    consult_who = ""

#緊急度（どれくらい急いで対応・相談する必要があるか）を選ぶ
urgency = st.radio(
    "この場面では、どれくらい急いで対応・相談する必要がありますか？",
    ["低い（様子を見てもよい）","中くらい（今日中には対応したい）","高い（すぐに対応・相談したい）"]
)

#心理的負担：今回の対応がどれくらい大変だったか
mental_load = st.radio(
    "[必須]この場面で感じた心理的な負担はどのくらいありましたか？",
    ["1:ほとんど負担はない", "2:少し負担がある","3:ある程度負担がある", "4:かなり負担がある","5:非常に負担が大きい"]
)

is_success = st.radio(
    "[必須]この場面での対応について、あなた自身はどのように感じましたか？",
    ["うまくいったと思う",
     "少しうまくいったと思う",
     "どちらともいえない",
     "あまりうまくいかなかったと思う",
     "うまくいかなかったと思う"
     ]
)

# 入力された内容を確認表示
# st.write("入力された対応内容：", action)

# --- ここまで ---

# --- ここから 保存ボタン（まだSheetsには保存しない） ---

st.caption("入力が終わったら、下の保存ボタンを押してください。")
if st.button("保存"):

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

    #対応内容が空なら保存させない
    if action.strip() == "":
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

    st.success("保存しました。ご協力ありがとうございました。")

    # if consult_need == "はい" and consult_who=="家族":
    #     st.write("家族に相談する判断をしました")

# --- ここまで ---