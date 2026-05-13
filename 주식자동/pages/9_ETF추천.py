import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pykrx import stock

st.set_page_config(page_title="ETF 추천", page_icon="📦", layout="wide")

from utils.krx     import setup_krx, get_etf_ohlcv, get_etf_ticker_list_cached, last_trading_day, get_realtime_price
from utils.signals import add_indicators, generate_signal, SIGNAL_COLOR
from utils.storage import load_weights
setup_krx()

st.title("📦 ETF 추천")
st.caption("추세·모멘텀 기반 ETF 분석 및 추천 · 모의투자 연결")
st.warning("참고용 분석입니다. 투자 결정은 본인 책임입니다.", icon="⚠️")

# ── ETF 카테고리 ─────────────────────────────────────────────────────────────

ETF_CATEGORIES = {
    "전체": None,
    "국내 지수": ["KODEX", "TIGER", "KINDEX", "ARIRANG"],
    "섹터/테마": ["반도체", "2차전지", "바이오", "IT", "헬스", "미디어", "게임", "로봇", "AI"],
    "해외": ["미국", "나스닥", "S&P", "차이나", "일본", "인도", "베트남"],
    "채권/안전": ["국채", "회사채", "단기채", "금", "달러"],
    "레버리지/인버스": ["레버리지", "인버스", "2X", "곱버스"],
}


def filter_by_category(name: str, category: str) -> bool:
    if category == "전체":
        return True
    keywords = ETF_CATEGORIES.get(category, [])
    return any(k in name for k in keywords)


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("ETF 추천 설정")
    category   = st.selectbox("카테고리", list(ETF_CATEGORIES.keys()))
    scan_count = st.slider("분석 ETF 수", 30, 200, 80, step=10)
    min_score  = st.slider("최소 신호 점수", -2, 8, 1)
    run = st.button("🔍 ETF 분석 시작", type="primary", use_container_width=True)

    if st.session_state.get("etf_results"):
        if st.button("🗑️ 결과 초기화", use_container_width=True):
            st.session_state.pop("etf_results", None)
            st.session_state.pop("etf_cache_key", None)
            st.rerun()

if not run and not st.session_state.get("etf_results"):
    st.markdown("""
    ### ETF란?
    **상장지수펀드(Exchange Traded Fund)**입니다. 주식처럼 거래소에서 사고팔 수 있으며,
    여러 종목에 분산 투자하는 효과를 냅니다.

    | 구분 | 설명 |
    |------|------|
    | 지수 ETF | 코스피200, 나스닥 등 지수를 그대로 추종 |
    | 섹터 ETF | 반도체, 2차전지 등 특정 산업에 집중 |
    | 채권/금 ETF | 안전자산, 분산투자용 |
    | 레버리지 | 지수 2배 수익/손실 (고위험) |
    | 인버스 | 지수 하락 시 수익 (헤지용) |

    왼쪽에서 카테고리와 분석 수를 선택 후 **ETF 분석 시작**을 클릭하세요.
    """)
    st.stop()

# ── 스캔 실행 ─────────────────────────────────────────────────────────────────

cache_key = f"etf_{category}_{scan_count}_{min_score}"

if run or st.session_state.get("etf_cache_key") != cache_key:
    st.session_state.pop("etf_results", None)

if not st.session_state.get("etf_results"):
    weights = load_weights()

    with st.spinner("ETF 목록 로딩 중..."):
        etf_map = get_etf_ticker_list_cached()  # {이름: 코드}

    # 카테고리 필터
    filtered = {n: c for n, c in etf_map.items() if filter_by_category(n, category)}

    # 거래대금 기준 상위 정렬 (시총 대신 거래대금으로 대형 ETF 우선)
    date = last_trading_day()
    try:
        etf_today = stock.get_etf_ohlcv_by_date(date, date, "069500")  # 테스트용
    except:
        pass

    candidates = list(filtered.items())[:scan_count]  # (이름, 코드)

    total   = len(candidates)
    prog    = st.progress(0)
    stat    = st.empty()
    results = []

    for i, (etf_name, ticker) in enumerate(candidates):
        prog.progress((i + 1) / total)
        stat.text(f"분석 중: {etf_name} ({i+1}/{total})")

        try:
            df = get_etf_ohlcv(ticker, months=6)
            if df is None or df.empty or len(df) < 30:
                time.sleep(0.1)
                continue

            df = add_indicators(df)
            signal, score, reasons = generate_signal(df, weights)

            if score < min_score:
                time.sleep(0.1)
                continue

            last    = df.iloc[-1]
            close   = int(last["종가"])
            ma20    = last.get("MA20", close)
            ma60    = last.get("MA60", close)
            rsi     = float(last.get("RSI", 0) or 0)

            # ETF 목표가 (주식보다 보수적)
            target1 = round(close * (1.04 if score < 5 else 1.06), -1)
            target2 = round(close * (1.08 if score < 5 else 1.12), -1)
            stop    = round(max(ma60 * 0.98, close * 0.95), -1)
            if stop >= close:
                stop = round(close * 0.95, -1)

            ret1 = (target1 / close - 1) * 100
            ret2 = (target2 / close - 1) * 100
            risk = (stop / close - 1) * 100
            rr   = abs(ret1 / risk) if risk != 0 else 0

            results.append({
                "ticker":  ticker,
                "name":    etf_name,
                "signal":  signal,
                "score":   score,
                "close":   close,
                "매수가":  close,
                "목표가1": target1,
                "목표가2": target2,
                "손절가":  stop,
                "수익률1": ret1,
                "수익률2": ret2,
                "리스크":  risk,
                "손익비":  rr,
                "rsi":     rsi,
                "reasons": reasons,
            })
        except:
            pass

        time.sleep(0.15)

    prog.empty()
    stat.empty()

    results.sort(key=lambda x: x["score"], reverse=True)
    st.session_state["etf_results"]  = results
    st.session_state["etf_cache_key"] = cache_key

results = st.session_state.get("etf_results", [])

if not results:
    st.warning("조건에 맞는 ETF가 없습니다. 최소 점수를 낮추거나 카테고리를 변경하세요.")
    st.stop()

st.success(f"**{len(results)}개** ETF 추천 완료")

# ── 추천 카드 ────────────────────────────────────────────────────────────────
st.subheader("추천 ETF")

show_count = st.selectbox("표시 개수", [6, 9, 12, len(results)],
                           format_func=lambda x: f"상위 {x}개" if x < len(results) else "전체",
                           index=1)

cols_per_row = 3
for row_start in range(0, show_count, cols_per_row):
    row_res = results[row_start:row_start + cols_per_row]
    cols = st.columns(cols_per_row)
    for col, r in zip(cols, row_res):
        c = SIGNAL_COLOR.get(r["signal"], "#9e9e9e")
        with col:
            st.markdown(
                f"<div style='background:{c}18;border:2px solid {c};"
                f"border-radius:10px;padding:14px;margin-bottom:6px'>"
                f"<div style='font-size:1.0rem;font-weight:bold'>{r['name']}</div>"
                f"<div style='color:#aaa;font-size:0.8rem'>{r['ticker']}</div>"
                f"<hr style='border-color:{c}44;margin:8px 0'>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:3px;font-size:0.83rem'>"
                f"<div>현재가</div><div style='text-align:right'>₩{r['close']:,}</div>"
                f"<div>목표가1</div><div style='text-align:right;color:#26a69a'>₩{r['목표가1']:,} (+{r['수익률1']:.1f}%)</div>"
                f"<div>목표가2</div><div style='text-align:right;color:#00c853'>₩{r['목표가2']:,} (+{r['수익률2']:.1f}%)</div>"
                f"<div>손절가</div><div style='text-align:right;color:#ef5350'>₩{r['손절가']:,} ({r['리스크']:.1f}%)</div>"
                f"<div>손익비</div><div style='text-align:right'>{r['손익비']:.1f}:1</div>"
                f"<div>RSI</div><div style='text-align:right'>{r['rsi']:.0f}</div>"
                f"</div>"
                f"<div style='color:{c};font-weight:bold;margin-top:8px'>{r['signal']} ({r['score']:+d}점)</div>"
                f"</div>",
                unsafe_allow_html=True)

# ── 상세 분석 + 모의투자 연결 ────────────────────────────────────────────────
st.markdown("---")
st.subheader("상세 분석")

sel_name = st.selectbox("ETF 선택", [r["name"] for r in results])
sel = next(r for r in results if r["name"] == sel_name)

detail_col, chart_col = st.columns([1, 2])

with detail_col:
    c = SIGNAL_COLOR.get(sel["signal"], "#9e9e9e")
    st.markdown(f"### {sel['name']}")
    st.markdown(f"`{sel['ticker']}`")
    st.markdown(
        f"<div style='background:{c}22;border-left:5px solid {c};"
        f"padding:14px;border-radius:8px'>"
        f"<div style='font-size:1.4rem;font-weight:bold;color:{c}'>{sel['signal']}</div>"
        f"<div style='color:#ccc'>종합 점수: {sel['score']:+d}점</div></div>",
        unsafe_allow_html=True)

    st.markdown("#### 매매 전략")
    df_strat = pd.DataFrame({
        "항목": ["현재가", "목표가1", "목표가2", "손절가", "예상수익(1차)", "예상수익(2차)", "최대손실", "손익비"],
        "내용": [
            f"₩{sel['close']:,}", f"₩{sel['목표가1']:,}", f"₩{sel['목표가2']:,}",
            f"₩{sel['손절가']:,}", f"+{sel['수익률1']:.1f}%", f"+{sel['수익률2']:.1f}%",
            f"{sel['리스크']:.1f}%", f"{sel['손익비']:.1f}:1",
        ]
    }).set_index("항목")
    st.dataframe(df_strat, use_container_width=True)

    st.markdown("#### 분석 근거")
    for r in sel["reasons"]:
        icon = "🟢" if "+" in r else "🔴" if "-" in r else "🟡"
        st.markdown(f"{icon} {r}")

    st.markdown("---")
    if st.button("💼 이 ETF 모의투자로 보내기", type="primary", use_container_width=True):
        st.session_state["paper_prefill"] = {
            "ticker":  sel["ticker"],
            "name":    sel["name"],
            "price":   sel["close"],
            "signal":  sel["signal"],
            "score":   sel["score"],
            "reasons": sel["reasons"],
            "is_etf":  True,
        }
        st.success(
            f"✅ **{sel['name']}** 정보가 전달됐습니다.  \n"
            f"**6 모의투자** 페이지로 이동하면 매수 탭에 자동 입력됩니다."
        )

with chart_col:
    df_chart = get_etf_ohlcv(sel["ticker"], months=6)
    if not df_chart.empty:
        df_chart = add_indicators(df_chart)

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_chart.index, open=df_chart["시가"], high=df_chart["고가"],
            low=df_chart["저가"], close=df_chart["종가"], name="가격",
            increasing_line_color="#ef5350", decreasing_line_color="#26a69a"))

        for ma, color in [("MA20","#42a5f5"), ("MA60","#ab47bc")]:
            if ma in df_chart.columns:
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart[ma], name=ma,
                    line=dict(color=color, width=1.5)))

        fig.add_hline(y=sel["매수가"],  line_color="#42a5f5", line_dash="dash",
                      annotation_text="매수가")
        fig.add_hline(y=sel["목표가1"], line_color="#26a69a", line_dash="dot",
                      annotation_text="목표1")
        fig.add_hline(y=sel["손절가"],  line_color="#ef5350", line_dash="dash",
                      annotation_text="손절")

        fig.update_layout(height=500, template="plotly_dark",
            xaxis_rangeslider_visible=False,
            title=f"{sel['name']} 가격 차트",
            margin=dict(l=40, r=40, t=60, b=40))
        st.plotly_chart(fig, use_container_width=True)

# ── 전체 테이블 ───────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("전체 추천 ETF 테이블"):
    table_data = [{
        "ETF명":   r["name"],
        "코드":    r["ticker"],
        "현재가":  f"₩{r['close']:,}",
        "목표가1": f"₩{r['목표가1']:,} (+{r['수익률1']:.1f}%)",
        "목표가2": f"₩{r['목표가2']:,} (+{r['수익률2']:.1f}%)",
        "손절가":  f"₩{r['손절가']:,} ({r['리스크']:.1f}%)",
        "손익비":  f"{r['손익비']:.1f}:1",
        "RSI":     round(r["rsi"], 1),
        "신호":    r["signal"],
        "점수":    r["score"],
    } for r in results]
    df_table = pd.DataFrame(table_data)
    def color_sig(v):
        return f"color:{SIGNAL_COLOR.get(v,'#9e9e9e')};font-weight:bold"
    st.dataframe(df_table.style.applymap(color_sig, subset=["신호"]),
                 use_container_width=True, height=400)
