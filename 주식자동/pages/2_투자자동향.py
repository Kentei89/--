import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pykrx import stock

st.set_page_config(page_title="투자자 동향", page_icon="👥", layout="wide")

from utils.krx import setup_krx, get_investor_market_total, get_investor_trading_by_ticker, last_trading_day, date_range
setup_krx()

st.title("👥 투자자별 매매 동향")
st.caption("기관 · 외국인 · 개인 순매수 현황")

# ── 시장 전체 투자자 현황 ─────────────────────────────────────────────────────
st.subheader("오늘 시장 전체 투자자 현황")

market_tabs = st.tabs(["KOSPI", "KOSDAQ"])
for tab, mkt in zip(market_tabs, ["KOSPI", "KOSDAQ"]):
    with tab:
        with st.spinner(f"{mkt} 투자자 데이터 로딩..."):
            try:
                df = get_investor_market_total(mkt)
            except Exception as e:
                st.error(f"데이터 로드 실패: {e}")
                continue

        if df.empty:
            st.warning("데이터 없음")
            continue

        # 컬럼명 표준화
        cols = df.columns.tolist()
        if len(cols) >= 3:
            df.columns = ["매도", "매수", "순매수"]

        st.dataframe(df.style.background_gradient(subset=["순매수"], cmap="RdYlGn"),
                     use_container_width=True)

        # 순매수 차트
        fig = go.Figure(go.Bar(
            x=df.index, y=df["순매수"],
            marker_color=["#26a69a" if v >= 0 else "#ef5350" for v in df["순매수"]],
            text=df["순매수"].apply(lambda x: f"{x/1e8:+.0f}억"),
            textposition="outside"
        ))
        fig.update_layout(height=350, template="plotly_dark",
            title=f"{mkt} 투자자별 순매수 (원)",
            yaxis_title="순매수", margin=dict(l=40,r=40,t=60,b=40))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── 개별 종목 투자자 동향 ────────────────────────────────────────────────────
st.subheader("개별 종목 기관/외국인/개인 동향")

c1, c2 = st.columns([2, 1])
with c1:
    sel_ticker = st.text_input("종목코드 (6자리)", value="005930", max_chars=6).zfill(6)
    try:
        ticker_name = stock.get_market_ticker_name(sel_ticker)
        st.caption(f"종목명: {ticker_name}")
    except:
        ticker_name = sel_ticker
with c2:
    sel_months = st.selectbox("조회 기간", [1, 3, 6], format_func=lambda x: f"{x}개월", index=1)

if st.button("조회", type="primary"):
    with st.spinner("조회 중..."):
        try:
            df_t = get_investor_trading_by_ticker(sel_ticker, sel_months)
            df_t.columns = ["기관합계", "기타법인", "개인", "외국인합계", "전체"]
        except Exception as e:
            st.error(f"조회 실패: {e}")
            st.stop()

    if df_t.empty:
        st.warning("데이터가 없습니다.")
        st.stop()

    # 기간 합계 요약
    inv_cols = ["기관합계", "외국인합계", "개인"]
    m_cols = st.columns(3)
    for col, inv in zip(m_cols, inv_cols):
        total = df_t[inv].sum()
        col.metric(f"{inv} 순매수 합계", f"{total:+,.0f}주",
                   delta_color="normal" if total >= 0 else "inverse")

    # 차트
    color_map = {"기관합계": "#42a5f5", "외국인합계": "#ef5350", "개인": "#26a69a"}
    fig2 = go.Figure()
    for inv in inv_cols:
        bar_c = [color_map[inv] if v >= 0 else "#555555" for v in df_t[inv]]
        fig2.add_trace(go.Bar(x=df_t.index, y=df_t[inv], name=inv,
            marker_color=bar_c, opacity=0.85))

    fig2.update_layout(height=400, template="plotly_dark", barmode="group",
        title=f"{ticker_name} 투자자별 순매수",
        yaxis_title="순매수 (주)", margin=dict(l=40,r=40,t=60,b=40))
    st.plotly_chart(fig2, use_container_width=True)

    # 연속 순매수 일수
    st.markdown("**연속 순매수/순매도 현황 (최근 10일)**")
    recent = df_t[inv_cols].tail(10).copy()
    recent.index = recent.index.strftime("%m/%d")

    streak_data = []
    for inv in inv_cols:
        vals = df_t[inv].tail(10).values
        streak = 0
        for v in reversed(vals):
            if v > 0:
                if streak >= 0: streak += 1
                else: break
            elif v < 0:
                if streak <= 0: streak -= 1
                else: break
        streak_data.append({"투자자": inv,
                             "연속": f"{'매수' if streak > 0 else '매도'} {abs(streak)}일" if streak != 0 else "혼조",
                             "최근10일합계": f"{df_t[inv].tail(10).sum():+,.0f}주"})

    st.dataframe(pd.DataFrame(streak_data).set_index("투자자"), use_container_width=True)

    # 상세 테이블
    with st.expander("일별 상세"):
        display = recent.copy()
        for col in inv_cols:
            display[col] = display[col].apply(lambda x: f"{x:+,.0f}주")
        st.dataframe(display, use_container_width=True)
