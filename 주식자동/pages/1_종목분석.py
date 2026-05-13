import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(page_title="종목 분석", page_icon="📊", layout="wide")

from utils.krx     import setup_krx, get_ohlcv, get_investor_trading, get_foreign_holding, get_ticker_name, get_ticker_list, get_realtime_price
from utils.signals import add_indicators, generate_signal, SIGNAL_COLOR, INDICATOR_INFO, get_indicator_context, calc_targets, generate_narrative
from utils.storage import load_weights
setup_krx()

_WEIGHTS = load_weights()

st.title("📊 종목 분석")

# ── 사이드바 ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("종목 설정")

    search_by = st.radio("검색 방법", ["종목명", "종목코드"], horizontal=True)

    if search_by == "종목명":
        with st.spinner("종목 목록 로딩..."):
            ticker_map = get_ticker_list()
        names = sorted(ticker_map.keys())
        default_idx = names.index("삼성전자") if "삼성전자" in names else 0
        sel_name = st.selectbox("종목명 검색 (직접 입력 가능)", names, index=default_idx)
        ticker = ticker_map[sel_name][0]
        name   = sel_name
    else:
        ticker_input = st.text_input("종목코드 (6자리)", value="005930", max_chars=6)
        ticker = ticker_input.strip().zfill(6)
        name   = get_ticker_name(ticker)

    st.markdown(f"**{name}** ({ticker})")
    period = st.selectbox("조회 기간", [3, 6, 12, 24],
                          format_func=lambda x: f"{x}개월", index=1)

    st.markdown("---")
    st.markdown("**차트 설정**")
    show_ma  = st.multiselect("이동평균선", ["MA5","MA20","MA60","MA120"], default=["MA20","MA60"])
    show_bb  = st.checkbox("볼린저밴드", value=True)
    show_vol = st.checkbox("거래량", value=True)

# ── 데이터 로드 ──────────────────────────────────────────────────────────────
with st.spinner(f"{name} 데이터 로딩 중..."):
    df     = get_ohlcv(ticker, period)
    df_inv = get_investor_trading(ticker, min(period, 3))

if df is None or df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

df = add_indicators(df)
signal, score, reasons = generate_signal(df, _WEIGHTS)
ind_ctx = get_indicator_context(df)
last    = df.iloc[-1]
prev    = df.iloc[-2]

# 실시간 현재가 (KIS API 우선 → 네이버 fallback → pykrx 종가)
_rt = get_realtime_price(ticker)
current_price = _rt["price"] if _rt else int(last["종가"])
price_chg = current_price - prev["종가"]
price_pct = price_chg / prev["종가"] * 100
_price_src   = _rt.get("source", "pykrx종가") if _rt else "pykrx종가"
_fetched_at  = _rt.get("fetched_at", "") if _rt else ""

# ── 상단 지표 ────────────────────────────────────────────────────────────────
st.subheader(f"{name} ({ticker})")
if _fetched_at:
    st.caption(f"현재가 기준: {_price_src} · {_fetched_at} 조회")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("현재가", f"₩{current_price:,.0f}", f"{price_pct:+.2f}%",
          delta_color="normal" if price_chg >= 0 else "inverse")
m2.metric("시가", f"₩{last['시가']:,.0f}")
m3.metric("고가", f"₩{last['고가']:,.0f}")
m4.metric("저가", f"₩{last['저가']:,.0f}")
rsi_val = last.get("RSI", float("nan"))
m5.metric("RSI (14)", f"{rsi_val:.1f}" if not np.isnan(rsi_val) else "N/A")

# ── 매매 신호 ────────────────────────────────────────────────────────────────
color = SIGNAL_COLOR.get(signal, "#9e9e9e")
sig_col, reason_col = st.columns([1, 2])
with sig_col:
    st.markdown(
        f"<div style='background:{color}22;border-left:6px solid {color};"
        f"padding:20px;border-radius:8px;text-align:center'>"
        f"<div style='font-size:1.8rem;font-weight:bold;color:{color}'>{signal}</div>"
        f"<div style='color:#aaa'>종합점수: {score:+d}</div></div>",
        unsafe_allow_html=True)
with reason_col:
    st.markdown("**분석 근거 (점수 요약)**")
    for r in reasons:
        icon = "🟢" if "+" in r else "🔴" if "-" in r else "⚪"
        st.markdown(f"{icon} {r}")

# ── AI 종합 분석 ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 AI 종합 분석")
narrative = generate_narrative(signal, score, reasons, last, df)
color_bg  = SIGNAL_COLOR.get(signal, "#9e9e9e") + "22"
st.markdown(
    f"<div style='background:{color_bg};border-left:4px solid {SIGNAL_COLOR.get(signal,'#9e9e9e')};"
    f"padding:16px;border-radius:8px;line-height:1.8'>{narrative}</div>",
    unsafe_allow_html=True,
)

# ── 추천 가격 ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("💰 추천 가격 (ATR 기반 자동 계산)")
st.caption("⚠️ 기술적 분석 기반 참고값입니다. 실제 투자는 본인 판단으로 결정하세요.")

tgt = calc_targets(df, score)
pc1, pc2, pc3, pc4 = st.columns(4)
pc1.metric("매수 추천가",  f"₩{tgt['buy_price']:,}")
pc2.metric("목표가 1",     f"₩{tgt['target1']:,}",  f"+{tgt['reward1_pct']:.1f}%")
pc3.metric("목표가 2",     f"₩{tgt['target2']:,}",  f"+{tgt['reward2_pct']:.1f}%")
pc4.metric("손절가",       f"₩{tgt['stop']:,}",     f"-{tgt['risk_pct']:.1f}%",
           delta_color="inverse")
st.caption(
    f"ATR(평균변동폭) ₩{tgt['atr']:,} 기준 | "
    f"손익비 목표1: **1:{tgt['reward1_pct']/tgt['risk_pct']:.1f}** "
    f"/ 목표2: **1:{tgt['reward2_pct']/tgt['risk_pct']:.1f}**"
    if tgt['risk_pct'] > 0 else ""
)

if st.button("💼 이 종목 모의투자로 보내기", key="send_to_paper"):
    st.session_state["paper_prefill"] = {
        "ticker":  ticker,
        "name":    name,
        "price":   tgt["buy_price"],
        "signal":  signal,
        "score":   score,
        "reasons": reasons,
        "is_etf":  False,
    }
    st.success(f"✅ {name} 정보를 모의투자 탭으로 전달했습니다. 모의투자 페이지로 이동하세요.")

st.markdown("---")

# ── 지표 상세 설명 ────────────────────────────────────────────────────────────
with st.expander("📚 지표 상세 설명 (각 지표가 무엇인지, 지금 어떤 상태인지)"):
    for key, info in INDICATOR_INFO.items():
        ctx_text = ind_ctx.get(key, "")
        st.markdown(f"#### {info['name']}")
        st.markdown(info["desc"])
        st.markdown("**판단 기준:**")
        for g in info["guide"]:
            st.markdown(f"  - {g}")
        if ctx_text:
            st.info(f"**현재 상태:** {ctx_text}")
        st.markdown("")

st.markdown("---")

# ── 캔들 차트 ────────────────────────────────────────────────────────────────
rows  = 2 + (1 if show_vol else 0)
row_h = [0.6, 0.2, 0.2] if show_vol else [0.7, 0.3]
titles = ["가격"] + (["거래량"] if show_vol else []) + ["RSI / MACD"]

fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                    row_heights=row_h, vertical_spacing=0.03,
                    subplot_titles=titles)

fig.add_trace(go.Candlestick(
    x=df.index, open=df["시가"], high=df["고가"],
    low=df["저가"], close=df["종가"], name="가격",
    increasing_line_color="#ef5350", decreasing_line_color="#26a69a"), row=1, col=1)

ma_colors = {"MA5":"#ffa726","MA20":"#42a5f5","MA60":"#ab47bc","MA120":"#26c6da"}
for ma in show_ma:
    if ma in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[ma], name=ma,
            line=dict(color=ma_colors[ma], width=1.5)), row=1, col=1)

if show_bb and "BB_upper" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB상단",
        line=dict(color="rgba(128,128,128,0.4)", width=1, dash="dash"),
        showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB하단",
        line=dict(color="rgba(128,128,128,0.4)", width=1, dash="dash"),
        fill="tonexty", fillcolor="rgba(128,128,128,0.06)",
        showlegend=False), row=1, col=1)

cur_row = 2
if show_vol:
    colors_v = ["#ef5350" if c >= o else "#26a69a"
                for c, o in zip(df["종가"], df["시가"])]
    fig.add_trace(go.Bar(x=df.index, y=df["거래량"], name="거래량",
        marker_color=colors_v, showlegend=False), row=cur_row, col=1)
    if "Vol_MA20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Vol_MA20"], name="거래량MA20",
            line=dict(color="#ffa726", width=1.2)), row=cur_row, col=1)
    cur_row += 1

if "RSI" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
        line=dict(color="#e040fb", width=1.5)), row=cur_row, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red",   opacity=0.5, row=cur_row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=cur_row, col=1)
if "MACD_hist" in df.columns:
    hc = ["#ef5350" if v < 0 else "#26a69a" for v in df["MACD_hist"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="MACD Hist",
        marker_color=hc, opacity=0.5), row=cur_row, col=1)

fig.update_layout(height=680, template="plotly_dark",
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
    margin=dict(l=40, r=40, t=60, b=40))
st.plotly_chart(fig, use_container_width=True)

# ── 투자자별 매매 동향 ──────────────────────────────────────────────────────
st.subheader("투자자별 매매 동향 (순매수)")
if df_inv is not None and not df_inv.empty:
    cols_to_show = [c for c in ["기관합계","외국인합계","개인","기타법인"] if c in df_inv.columns]
    if cols_to_show:
        fig_inv = go.Figure()
        inv_colors = {"기관합계":"#42a5f5","외국인합계":"#ef5350","개인":"#26a69a","기타법인":"#ffa726"}
        for col in cols_to_show:
            bar_c = ["#ef5350" if v < 0 else inv_colors.get(col, "#9e9e9e") for v in df_inv[col]]
            fig_inv.add_trace(go.Bar(x=df_inv.index, y=df_inv[col], name=col,
                marker_color=bar_c, opacity=0.8))
        fig_inv.update_layout(height=350, template="plotly_dark", barmode="group",
            title="투자자별 순매수 (주)", yaxis_title="순매수 (주)",
            margin=dict(l=40,r=40,t=60,b=40))
        st.plotly_chart(fig_inv, use_container_width=True)

        st.markdown("**최근 5일 순매수 요약**")
        recent = df_inv[cols_to_show].tail(5).copy()
        recent.index = recent.index.strftime("%m/%d")
        for col in cols_to_show:
            recent[col] = recent[col].apply(lambda x: f"{x:+,.0f}주")
        st.dataframe(recent, use_container_width=True)
else:
    st.info("투자자 데이터를 불러올 수 없습니다.")

# ── 기술적 지표 테이블 ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("기술적 지표 현황")
ind_cols = st.columns(4)
def _fmt(v, fmt=".1f"):
    return f"{v:{fmt}}" if not np.isnan(v) else "N/A"

indicators = [
    ("RSI (14)",      _fmt(last.get("RSI",         float("nan")))),
    ("MACD",          _fmt(last.get("MACD",        float("nan")), ".2f")),
    ("MACD Signal",   _fmt(last.get("MACD_signal", float("nan")), ".2f")),
    ("볼린저 %B",     _fmt(last.get("BB_pct",      float("nan")), ".2f")),
    ("MA20",          f"₩{last.get('MA20', 0):,.0f}"),
    ("MA60",          f"₩{last.get('MA60', 0):,.0f}"),
    ("스토캐스틱K",   _fmt(last.get("Stoch_K",     float("nan")))),
    ("거래량/MA비율", f"{last['거래량']/last.get('Vol_MA20',1):.2f}x" if last.get("Vol_MA20", 0) > 0 else "N/A"),
    ("ADX (추세강도)", _fmt(last.get("ADX",        float("nan")))),
    ("+DI / -DI",     f"{_fmt(last.get('Plus_DI', float('nan')))} / {_fmt(last.get('Minus_DI', float('nan')))}"),
    ("ATR (변동폭)",  f"₩{last.get('ATR', 0):,.0f}"),
    ("ATR %",         f"{last.get('ATR_pct', 0):.1f}%"),
]
ind_cols2 = st.columns(4)
for i, (label, val) in enumerate(indicators):
    with ind_cols2[i % 4]:
        st.metric(label, val)
