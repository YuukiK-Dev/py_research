import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="支援者：一覧", layout="wide")
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

st.title("支援者：一覧（supporter_log）")

conn = st.connection("gsheets", type=GSheetsConnection)

# 1) 読み込み
df = conn.read(worksheet="supporter_log", ttl=0)
df = df.loc[:, ~df.columns.duplicated()]
df = df.reindex(columns=["date", "time", "supporter", "seen_status", "action", "memo", "anxiety","hesitation","consult_need","urgency"]).dropna(how="all")

if df.empty:
    st.warning("supporter_log にデータがありません（まだ記録がない可能性）")
    st.stop()

# 2) datetime化（直近24hのため）
dt_str = df["date"].astype(str).str.strip() + " " + df["time"].astype(str).str.strip()
df["dt"] = pd.to_datetime(dt_str, errors="coerce")

# 3) フィルタUI
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    only_24h = st.toggle("直近24h", value=True)
with col2:
    supporter_filter = st.multiselect(
        "支援者の種類",
        sorted(df["supporter"].dropna().unique().tolist()),
        default=sorted(df["supporter"].dropna().unique().tolist())
    )
with col3:
    urgency_min = st.selectbox("緊急度（以上）", [0, 1, 2], index=0)

view = df.copy()
view = view[view["supporter"].isin(supporter_filter)]
view = view[view["urgency"].fillna(0).astype(int) >= int(urgency_min)]

if only_24h:
    since = datetime.now() - timedelta(hours=24)
    view = view[view["dt"] >= since]

# 4) KPI（簡単）
shindoi_count = int((view["seen_status"] == "shindoi").sum())
st.metric("😣 shindoi 回数（表示範囲内）", shindoi_count)

latest = view.sort_values("dt").tail(1)
if len(latest):
    r = latest.iloc[0]
    st.info(f"最新：{r['seen_status']} / {r['action']} / 緊急度 {r['urgency']} / {r['dt']}")
else:
    st.info("条件に合うデータがありません")

# 5) 表示
st.dataframe(view.sort_values("dt", ascending=False), use_container_width=True)