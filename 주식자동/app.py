import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="한국 주식 분석", page_icon="📈", layout="wide")

from utils.krx import setup_krx, get_market_today, get_index_ohlcv, INDEX_MAP
setup_krx()

from datetime import datetime
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.title("📈 한국 주식 종합 분석 대시보드")
st.caption(f"KOSPI · KOSDAQ | 기술적 분석 · 투자자 동향 · 종목 스크리닝 · 포트폴리오")

_hcol1, _hcol2 = st.columns([4, 1])
with _hcol1:
    st.markdown(f"<div style='color:#aaa;font-size:0.85rem'>마지막 조회: {now}</div>",
                unsafe_allow_html=True)
with _hcol2:
    if st.button("🔄 새로고침", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ── 지수 현황 ────────────────────────────────────────────────────────────────
st.subheader("시장 지수 현황")
idx_cols = st.columns(3)
idx_info = {
    "코스피": ("1001", "#ef5350"),
    "코스닥": ("2001", "#42a5f5"),
    "코스피200": ("1028", "#ab47bc"),
}

for col, (name, (ticker, color)) in zip(idx_cols, idx_info.items()):
    try:
        df_idx = get_index_ohlcv(ticker, months=1)
        cur  = df_idx["종가"].iloc[-1]
        prev = df_idx["종가"].iloc[-2]
        chg  = cur - prev
        pct  = chg / prev * 100
        arrow = "▲" if chg >= 0 else "▼"
        with col:
            st.metric(name, f"{cur:,.2f}",
                      f"{arrow} {abs(chg):,.2f} ({pct:+.2f}%)",
                      delta_color="normal" if chg >= 0 else "inverse")
    except Exception:
        with col:
            st.metric(name, "N/A")

st.markdown("---")

# ── 오늘의 시장 ──────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["KOSPI", "KOSDAQ"])

for tab, market in zip([tab1, tab2], ["KOSPI", "KOSDAQ"]):
    with tab:
        with st.spinner(f"{market} 데이터 로딩 중..."):
            try:
                df = get_market_today(market)
                df = df.dropna(subset=["종가"])
            except Exception as e:
                st.error(f"데이터 로드 실패: {e}")
                continue

        c1, c2, c3, c4 = st.columns(4)
        rising  = (df["등락률"] > 0).sum()
        falling = (df["등락률"] < 0).sum()
        flat    = (df["등락률"] == 0).sum()
        with c1: st.metric("상승", f"{rising}개", delta_color="normal")
        with c2: st.metric("하락", f"{falling}개", delta_color="inverse")
        with c3: st.metric("보합", f"{flat}개")
        with c4:
            total_vol = df["거래량"].sum()
            st.metric("총 거래량", f"{total_vol/1e8:.1f}억주")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**상승 Top 10**")
            top_up = df.nlargest(10, "등락률")[["종목명", "종가", "등락률", "거래량"]].copy()
            top_up["등락률"] = top_up["등락률"].apply(lambda x: f"{x:+.2f}%")
            top_up["종가"]   = top_up["종가"].apply(lambda x: f"₩{x:,.0f}")
            top_up["거래량"] = top_up["거래량"].apply(lambda x: f"{x:,}")
            st.dataframe(top_up, use_container_width=True, height=360)

        with col_b:
            st.markdown("**하락 Top 10**")
            top_dn = df.nsmallest(10, "등락률")[["종목명", "종가", "등락률", "거래량"]].copy()
            top_dn["등락률"] = top_dn["등락률"].apply(lambda x: f"{x:+.2f}%")
            top_dn["종가"]   = top_dn["종가"].apply(lambda x: f"₩{x:,.0f}")
            top_dn["거래량"] = top_dn["거래량"].apply(lambda x: f"{x:,}")
            st.dataframe(top_dn, use_container_width=True, height=360)

        st.markdown("**거래량 Top 10**")
        top_vol = df.nlargest(10, "거래량")[["종목명", "종가", "등락률", "거래량", "시가총액"]].copy()
        top_vol["등락률"]   = top_vol["등락률"].apply(lambda x: f"{x:+.2f}%")
        top_vol["종가"]     = top_vol["종가"].apply(lambda x: f"₩{x:,.0f}")
        top_vol["거래량"]   = top_vol["거래량"].apply(lambda x: f"{x:,}")
        top_vol["시가총액"] = top_vol["시가총액"].apply(
            lambda x: f"₩{x/1e12:.2f}조" if pd.notna(x) and x >= 1e12 else (
                      f"₩{x/1e8:.0f}억" if pd.notna(x) else "N/A"))
        st.dataframe(top_vol, use_container_width=True, height=360)
