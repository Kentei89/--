import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime
from pykrx import stock

st.set_page_config(page_title="포트폴리오", page_icon="💼", layout="wide")

from utils.krx import setup_krx, get_ohlcv, last_trading_day
from utils.signals import add_indicators, generate_signal, SIGNAL_COLOR
setup_krx()

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "portfolio.json")

def load():
    try:
        with open(PORTFOLIO_FILE, encoding="utf-8") as f:
            return json.load(f).get("holdings", [])
    except: return []

def save(holdings):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump({"holdings": holdings}, f, ensure_ascii=False, indent=2)

def get_current_price(ticker):
    try:
        date = last_trading_day()
        df = stock.get_market_ohlcv_by_ticker(date)
        if ticker in df.index:
            return float(df.loc[ticker].iloc[3])
    except: pass
    return None

st.title("💼 포트폴리오 관리")

if "holdings" not in st.session_state:
    st.session_state.holdings = load()
holdings = st.session_state.holdings

# ── 종목 추가 ────────────────────────────────────────────────────────────────
with st.expander("+ 종목 추가", expanded=len(holdings) == 0):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        add_ticker = st.text_input("종목코드", value="005930", max_chars=6).zfill(6)
        try: add_name = stock.get_market_ticker_name(add_ticker)
        except: add_name = add_ticker
        st.caption(f"종목명: {add_name}")
    with c2:
        add_qty = st.number_input("수량 (주)", min_value=1, value=10, step=1)
    with c3:
        add_avg = st.number_input("평균단가 (원)", min_value=1, value=70000, step=100)
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("추가", type="primary"):
            exist = next((h for h in holdings if h["ticker"] == add_ticker), None)
            if exist:
                total = exist["qty"] + add_qty
                exist["avg"] = (exist["avg"] * exist["qty"] + add_avg * add_qty) / total
                exist["qty"] = total
                st.success(f"{add_name} 수량 추가 (평균단가 재계산)")
            else:
                holdings.append({"ticker": add_ticker, "name": add_name,
                                  "qty": add_qty, "avg": add_avg,
                                  "date": datetime.today().strftime("%Y-%m-%d")})
                st.success(f"{add_name} 추가")
            st.session_state.holdings = holdings
            save(holdings)
            st.rerun()

if not holdings:
    st.info("보유 종목을 추가해주세요.")
    st.stop()

# ── 현재가 조회 ──────────────────────────────────────────────────────────────
with st.spinner("현재가 조회 중..."):
    for h in holdings:
        h["cur"] = get_current_price(h["ticker"])

# ── 요약 지표 ────────────────────────────────────────────────────────────────
total_invested = sum(h["qty"] * h["avg"] for h in holdings)
total_current  = sum(h["qty"] * h["cur"] for h in holdings if h["cur"])
total_pnl      = total_current - total_invested
total_pct      = total_pnl / total_invested * 100 if total_invested else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 투자금", f"₩{total_invested:,.0f}")
m2.metric("총 평가금", f"₩{total_current:,.0f}")
m3.metric("총 손익", f"₩{total_pnl:+,.0f}", f"{total_pct:+.2f}%",
          delta_color="normal" if total_pnl >= 0 else "inverse")
m4.metric("보유 종목", f"{len(holdings)}개")

st.markdown("---")

# ── 차트 ────────────────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    st.subheader("자산 배분")
    labels = [h["name"] for h in holdings if h["cur"]]
    values = [h["qty"] * h["cur"] for h in holdings if h["cur"]]
    fig_pie = go.Figure(go.Pie(labels=labels, values=values, hole=0.4,
        textinfo="label+percent"))
    fig_pie.update_layout(template="plotly_dark", height=300,
        margin=dict(l=20,r=20,t=30,b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

with ch2:
    st.subheader("종목별 수익률")
    names  = [h["name"] for h in holdings if h["cur"]]
    pcts   = [(h["cur"] - h["avg"]) / h["avg"] * 100 for h in holdings if h["cur"]]
    colors = ["#26a69a" if p >= 0 else "#ef5350" for p in pcts]
    fig_bar = go.Figure(go.Bar(x=names, y=pcts, marker_color=colors,
        text=[f"{p:+.2f}%" for p in pcts], textposition="outside"))
    fig_bar.update_layout(template="plotly_dark", height=300,
        yaxis_title="수익률 (%)", margin=dict(l=20,r=20,t=30,b=40))
    st.plotly_chart(fig_bar, use_container_width=True)

# ── 보유 종목 테이블 ─────────────────────────────────────────────────────────
st.subheader("보유 종목 현황")
rows = []
for h in holdings:
    cur = h.get("cur")
    if cur:
        pnl = (cur - h["avg"]) * h["qty"]
        pct = (cur - h["avg"]) / h["avg"] * 100
        cur_val = cur * h["qty"]
    else:
        pnl = pct = cur_val = 0
        cur = 0

    rows.append({
        "종목명": h["name"], "티커": h["ticker"],
        "수량": f"{h['qty']:,}주",
        "평균단가": f"₩{h['avg']:,.0f}",
        "현재가": f"₩{cur:,.0f}" if cur else "N/A",
        "평가금액": f"₩{cur_val:,.0f}",
        "손익": f"₩{pnl:+,.0f}",
        "수익률": f"{pct:+.2f}%",
        "_pct": pct,
    })

df_port = pd.DataFrame(rows)
def cr(val):
    try:
        v = float(val.replace("%","").replace("+",""))
        return "color:#26a69a;font-weight:bold" if v >= 0 else "color:#ef5350;font-weight:bold"
    except: return ""

styled = df_port.drop("_pct", axis=1).style.applymap(cr, subset=["수익률","손익"])
st.dataframe(styled, use_container_width=True)

# ── 종목별 신호 ──────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("보유 종목 매매 신호")

sig_cols = st.columns(min(4, len(holdings)))
for col, h in zip(sig_cols, holdings):
    try:
        df_h = get_ohlcv(h["ticker"], months=3)
        df_h = add_indicators(df_h)
        sig, score, _ = generate_signal(df_h)
        c = SIGNAL_COLOR.get(sig, "#9e9e9e")
    except:
        sig, score, c = "N/A", 0, "#9e9e9e"

    pct = (h.get("cur", h["avg"]) - h["avg"]) / h["avg"] * 100 if h.get("cur") else 0

    with col:
        st.markdown(
            f"<div style='background:{c}22;border:2px solid {c};"
            f"border-radius:8px;padding:12px;text-align:center'>"
            f"<div style='font-weight:bold'>{h['name']}</div>"
            f"<div style='color:{c};font-weight:bold;font-size:1.1rem'>{sig}</div>"
            f"<div style='color:#aaa'>점수: {score:+d}</div>"
            f"<div style='color:{'#26a69a' if pct >= 0 else '#ef5350'}'>"
            f"수익률: {pct:+.2f}%</div></div>",
            unsafe_allow_html=True)

# ── 종목 삭제 ────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("종목 삭제"):
    del_name = st.selectbox("삭제할 종목", [h["name"] for h in holdings])
    if st.button("삭제", type="secondary"):
        holdings = [h for h in holdings if h["name"] != del_name]
        st.session_state.holdings = holdings
        save(holdings)
        st.success(f"{del_name} 삭제")
        st.rerun()
