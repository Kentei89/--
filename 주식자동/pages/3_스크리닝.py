import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock

st.set_page_config(page_title="종목 스크리닝", page_icon="🔍", layout="wide")

from utils.krx import setup_krx, get_ohlcv, get_investor_trading, last_trading_day, date_range
from utils.signals import add_indicators, generate_signal, SIGNAL_COLOR
setup_krx()

st.title("🔍 종목 스크리닝")
st.caption("기술적 지표 + 투자자 동향 기반 유망 종목 발굴")

# ── 사이드바 조건 ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("스크리닝 조건")
    market_sel = st.multiselect("대상 시장", ["KOSPI","KOSDAQ"], default=["KOSPI","KOSDAQ"])

    st.markdown("**가격 조건**")
    min_price = st.number_input("최소 주가 (원)", value=1000, step=1000)
    max_price = st.number_input("최대 주가 (원)", value=500000, step=10000)

    st.markdown("**기술적 조건**")
    rsi_min = st.slider("RSI 최소", 0, 100, 0)
    rsi_max = st.slider("RSI 최대", 0, 100, 50)

    use_macd   = st.checkbox("MACD > 시그널 (상승 모멘텀)", value=False)
    use_ma_up  = st.checkbox("종가 > MA20 (단기 상승)", value=False)
    use_bb_low = st.checkbox("볼린저밴드 하단 근처 (BB%B < 0.2)", value=False)

    st.markdown("**투자자 조건**")
    use_foreign_buy = st.checkbox("외국인 순매수 (최근 3일)", value=False)
    use_inst_buy    = st.checkbox("기관 순매수 (최근 3일)", value=False)

    st.markdown("**등락률 조건**")
    chg_min = st.slider("등락률 최소 (%)", -30, 30, -5)
    chg_max = st.slider("등락률 최대 (%)", -30, 30, 15)

    max_stocks = st.slider("분석 종목 수 (많을수록 느림)", 20, 200, 50, step=10)
    run = st.button("스크리닝 실행", type="primary", use_container_width=True)

if not run:
    st.info("왼쪽에서 조건을 설정하고 **스크리닝 실행**을 누르세요.")

    st.markdown("### 조건 예시")
    st.markdown("""
    | 전략 | 조건 |
    |------|------|
    | 눌림목 매수 | RSI 30~45 + 종가>MA20 |
    | 과매도 반등 | RSI 0~30 + BB하단 근처 |
    | 모멘텀 매수 | MACD>시그널 + 외국인 순매수 |
    | 기관 매수 추종 | 기관 순매수 + 종가>MA20 |
    """)
    st.stop()

# ── 종목 리스트 수집 ─────────────────────────────────────────────────────────
date = last_trading_day()
all_tickers = []
for m in market_sel:
    tickers = stock.get_market_ticker_list(date, market=m)
    all_tickers += [(t, m) for t in tickers]

# 오늘 데이터로 1차 필터
today_data = {}
for m in market_sel:
    try:
        df_today = stock.get_market_ohlcv_by_ticker(date, market=m)
        today_data[m] = df_today
    except Exception:
        pass

# 1차 필터 (가격, 등락률)
candidates = []
for ticker, mkt in all_tickers:
    if mkt not in today_data:
        continue
    df_t = today_data[mkt]
    if ticker not in df_t.index:
        continue
    row = df_t.loc[ticker]
    price = row.iloc[3] if len(row) > 3 else 0  # 종가
    chg   = row.iloc[6] if len(row) > 6 else 0  # 등락률

    if not (min_price <= price <= max_price):
        continue
    if not (chg_min <= chg <= chg_max):
        continue
    candidates.append((ticker, mkt))

candidates = candidates[:max_stocks]
st.info(f"1차 필터: **{len(candidates)}개** 종목 기술적 분석 중... (종목당 ~1초 소요)")

# ── 기술적 분석 ──────────────────────────────────────────────────────────────
progress = st.progress(0)
status   = st.empty()
results  = []

for i, (ticker, mkt) in enumerate(candidates):
    progress.progress((i + 1) / len(candidates))
    try:
        name = stock.get_market_ticker_name(ticker)
        status.text(f"분석 중: {name} ({i+1}/{len(candidates)})")
    except Exception:
        name = ticker

    try:
        df = get_ohlcv(ticker, months=3)
        if df is None or len(df) < 30:
            continue
        df = add_indicators(df)
        signal, score, _ = generate_signal(df)
        last = df.iloc[-1]
        rsi  = last.get("RSI", np.nan)

        # 기술적 조건 필터
        if not (rsi_min <= rsi <= rsi_max):
            continue
        if use_macd and last.get("MACD", 0) <= last.get("MACD_signal", 0):
            continue
        if use_ma_up and last["종가"] <= last.get("MA20", last["종가"]):
            continue
        if use_bb_low and last.get("BB_pct", 1) >= 0.2:
            continue

        # 투자자 조건 필터
        if use_foreign_buy or use_inst_buy:
            try:
                df_inv = get_investor_trading(ticker, months=1)
                if df_inv is None or df_inv.empty:
                    continue
                recent = df_inv.tail(3)
                fore_col = next((c for c in df_inv.columns if "외국인" in c), None)
                inst_col = next((c for c in df_inv.columns if "기관" in c), None)

                if use_foreign_buy and fore_col and recent[fore_col].sum() <= 0:
                    continue
                if use_inst_buy and inst_col and recent[inst_col].sum() <= 0:
                    continue
            except Exception:
                continue

        chg_val = last.get("등락률", 0)
        results.append({
            "종목명": name, "티커": ticker, "시장": mkt,
            "현재가": f"₩{last['종가']:,.0f}",
            "등락률": f"{chg_val:+.2f}%",
            "RSI": round(rsi, 1) if not np.isnan(rsi) else None,
            "신호": signal, "점수": score,
            "_rsi": rsi, "_score": score,
        })
    except Exception:
        continue

progress.empty()
status.empty()

if not results:
    st.warning("조건에 맞는 종목이 없습니다. 조건을 완화해 보세요.")
    st.stop()

# ── 결과 출력 ────────────────────────────────────────────────────────────────
df_res = pd.DataFrame(results).sort_values("_score", ascending=False).reset_index(drop=True)
st.success(f"스크리닝 완료: **{len(df_res)}개** 종목 발굴")

# 신호별 요약
sum_cols = st.columns(5)
for col, lbl in zip(sum_cols, ["강력 매수","매수","중립/관망","매도","강력 매도"]):
    cnt = len(df_res[df_res["신호"] == lbl])
    color = SIGNAL_COLOR[lbl]
    with col:
        st.markdown(
            f"<div style='background:{color}22;border:2px solid {color};"
            f"border-radius:8px;padding:10px;text-align:center'>"
            f"<div style='color:{color};font-weight:bold'>{lbl}</div>"
            f"<div style='font-size:1.8rem;font-weight:bold'>{cnt}</div></div>",
            unsafe_allow_html=True)

st.markdown("---")

# 결과 테이블
def color_signal(val):
    c = SIGNAL_COLOR.get(val, "#9e9e9e")
    return f"background-color:{c}33;color:{c};font-weight:bold"
def color_chg(val):
    try:
        v = float(val.replace("%","").replace("+",""))
        return "color:#26a69a" if v >= 0 else "color:#ef5350"
    except: return ""

display = df_res[["종목명","티커","시장","현재가","등락률","RSI","신호","점수"]]
styled = (display.style
    .applymap(color_signal, subset=["신호"])
    .applymap(color_chg, subset=["등락률"])
    .background_gradient(subset=["RSI"], cmap="RdYlGn_r", vmin=20, vmax=80)
    .background_gradient(subset=["점수"], cmap="RdYlGn", vmin=-6, vmax=6))
st.dataframe(styled, use_container_width=True, height=600)

# 매수 Top 5
top5 = df_res[df_res["신호"].isin(["강력 매수","매수"])].head(5)
if not top5.empty:
    st.markdown("---")
    st.subheader("주목 종목 (매수 신호 상위)")
    cols = st.columns(min(5, len(top5)))
    for col, (_, row) in zip(cols, top5.iterrows()):
        c = SIGNAL_COLOR.get(row["신호"], "#9e9e9e")
        with col:
            st.markdown(
                f"<div style='background:{c}22;border:2px solid {c};"
                f"border-radius:8px;padding:12px;text-align:center'>"
                f"<div style='font-weight:bold'>{row['종목명']}</div>"
                f"<div style='color:#aaa;font-size:.8rem'>{row['티커']}</div>"
                f"<div style='font-size:1.1rem'>{row['현재가']}</div>"
                f"<div style='color:{c};font-weight:bold'>{row['신호']}</div>"
                f"<div>RSI: {row['RSI']}</div></div>",
                unsafe_allow_html=True)
