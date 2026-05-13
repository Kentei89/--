import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pykrx import stock

st.set_page_config(page_title="종목 추천", page_icon="🎯", layout="wide")

from utils.krx     import setup_krx, get_ohlcv, last_trading_day, get_investor_trading_by_ticker
from utils.signals import add_indicators, generate_signal, SIGNAL_COLOR
from utils.storage import load_weights
setup_krx()


def calc_targets(df: pd.DataFrame, score: int) -> dict:
    last   = df.iloc[-1]
    close  = last["종가"]
    ma20   = last.get("MA20", close)
    ma60   = last.get("MA60", close)
    bb_up  = last.get("BB_upper", close * 1.05)
    high52 = df["고가"].tail(252).max()

    if close < ma20 or close < ma20 * 1.03:
        buy_price = close
    else:
        buy_price = round(ma20 * 1.01, -2)

    if bb_up > buy_price * 1.03:
        target1 = min(bb_up, buy_price * 1.10)
    else:
        target1 = buy_price * (1.05 if score < 6 else 1.08)

    target2 = min(high52 * 0.95, buy_price * (1.15 if score < 6 else 1.20))
    target2 = max(target2, target1 * 1.05)

    stop_ma = ma60 * 0.98
    stop    = max(stop_ma, buy_price * (0.95 if score >= 6 else 0.93))
    if stop >= buy_price:
        stop = buy_price * 0.93

    ret1 = (target1 / buy_price - 1) * 100
    ret2 = (target2 / buy_price - 1) * 100
    risk = (stop / buy_price - 1) * 100
    rr   = abs(ret1 / risk) if risk != 0 else 0

    return {
        "매수가":  round(buy_price, -1 if buy_price > 1000 else 0),
        "목표가1": round(target1,   -1 if target1  > 1000 else 0),
        "목표가2": round(target2,   -1 if target2  > 1000 else 0),
        "손절가":  round(stop,      -1 if stop     > 1000 else 0),
        "수익률1": ret1, "수익률2": ret2,
        "리스크":  risk, "손익비":  rr,
    }


def get_investor_sentiment(ticker: str) -> str:
    try:
        df = get_investor_trading_by_ticker(ticker, months=1)
        if df.empty or len(df) < 3:
            return ""
        df.columns = ["기관합계", "기타법인", "개인", "외국인합계", "전체"]
        recent = df.tail(5)
        msgs = []
        if recent["외국인합계"].sum() > 0:
            msgs.append(f"외국인 {(recent['외국인합계']>0).sum()}일 순매수")
        if recent["기관합계"].sum() > 0:
            msgs.append(f"기관 {(recent['기관합계']>0).sum()}일 순매수")
        return " · ".join(msgs)
    except:
        return ""


def run_scan(market_sel, scan_count, min_score, use_inv, risk_pref) -> list:
    """종목 스캔 실행 — session_state에 캐시"""
    cache_key = f"{'-'.join(sorted(market_sel))}_{scan_count}_{min_score}_{use_inv}_{risk_pref}"
    if st.session_state.get("scan_cache_key") == cache_key and st.session_state.get("scan_results"):
        return st.session_state["scan_results"]

    weights = load_weights()
    date    = last_trading_day()
    candidates = []

    for mkt in market_sel:
        try:
            df_today = stock.get_market_ohlcv_by_ticker(date, market=mkt)
            df_today.columns = ["시가", "고가", "저가", "종가", "거래량", "거래대금", "등락률", "시가총액"]
            top = df_today.nlargest(scan_count, "시가총액")
            for ticker in top.index:
                candidates.append((ticker, mkt))
        except:
            pass

    total   = len(candidates)
    prog    = st.progress(0)
    stat    = st.empty()
    results = []

    for i, (ticker, mkt) in enumerate(candidates):
        prog.progress((i + 1) / total)
        try:
            name = stock.get_market_ticker_name(ticker)
        except:
            name = ticker
        stat.text(f"분석 중: {name} ({i+1}/{total})")

        try:
            df = get_ohlcv(ticker, months=6)
            if df is None or len(df) < 30:
                time.sleep(0.15)
                continue
            df = add_indicators(df)
            signal, score, reasons = generate_signal(df, weights)

            if score < min_score:
                time.sleep(0.15)
                continue

            last    = df.iloc[-1]
            targets = calc_targets(df, score)

            if risk_pref == "안정형 (손익비 우선)" and targets["손익비"] < 1.5:
                time.sleep(0.15)
                continue

            inv_msg = get_investor_sentiment(ticker) if use_inv else ""
            if inv_msg:
                score += 1

            results.append({
                "ticker": ticker, "name": name, "market": mkt,
                "signal": signal, "score": score,
                "close":  int(last["종가"]),
                "reasons": reasons, "inv_msg": inv_msg,
                **targets,
                "rsi":       float(last.get("RSI", 0) or 0),
                "macd_hist": float(last.get("MACD_hist", 0) or 0),
            })
        except:
            pass

        time.sleep(0.2)  # KRX 요청 속도 제한 방지

    prog.empty()
    stat.empty()

    results.sort(key=lambda x: x["score"], reverse=True)
    st.session_state["scan_results"]  = results
    st.session_state["scan_cache_key"] = cache_key
    return results


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("추천 설정")
    market_sel = st.multiselect("대상 시장", ["KOSPI", "KOSDAQ"], default=["KOSPI"])
    scan_count = st.slider("시장별 분석 종목 수 (시총 순)", 50, 300, 100, step=50)
    min_score  = st.slider("최소 신호 점수", -2, 10, 2)
    use_inv    = st.checkbox("투자자 동향 포함", value=True)
    risk_pref  = st.radio("투자 성향", ["안정형 (손익비 우선)", "성장형 (수익률 우선)"])
    run = st.button("🔍 추천 종목 분석", type="primary", use_container_width=True)

    if st.session_state.get("scan_results"):
        if st.button("🗑️ 결과 초기화", use_container_width=True):
            st.session_state.pop("scan_results", None)
            st.session_state.pop("scan_cache_key", None)
            st.rerun()

st.title("🎯 AI 종목 추천")
st.caption("기술적 분석 기반 매수 추천 · 목표가 · 손절가 제시")
st.warning("기술적 지표 기반 참고용입니다. 투자 결정은 본인 책임입니다.", icon="⚠️")

if not run and not st.session_state.get("scan_results"):
    st.markdown("""
    ### 사용 방법
    1. 왼쪽에서 시장·종목 수·성향 선택
    2. **추천 종목 분석** 클릭 (처음 1~2분 소요, 이후 캐시 사용)
    3. 추천 카드에서 매수가·목표가·손절가 확인
    4. **모의투자로 보내기** 버튼으로 바로 모의투자 연결

    | 지표 | 매수 신호 |
    |------|---------|
    | RSI | 30~45 과매도 탈출 |
    | MACD | 골든크로스 / 상승 모멘텀 |
    | 이동평균 | MA20 위 또는 돌파 직전 |
    | 볼린저밴드 | 하단 근처 반등 |
    """)
    st.stop()

# ── 스캔 실행 ─────────────────────────────────────────────────────────────────
if run:
    st.session_state.pop("scan_results", None)

with st.spinner("종목 스캔 중... (처음 실행 시 시간이 걸립니다)"):
    results = run_scan(market_sel, scan_count, min_score, use_inv, risk_pref)

if not results:
    st.warning("조건에 맞는 종목이 없습니다. 최소 점수를 낮추거나 종목 수를 늘려보세요.")
    st.stop()

st.success(f"**{len(results)}개** 종목 추천 완료 (시총 상위 {scan_count * len(market_sel)}개 중)")

# ── 추천 종목 카드 ────────────────────────────────────────────────────────────
st.subheader("추천 종목")

show_count = st.selectbox("표시 개수", [6, 9, 12, 15, len(results)],
                           format_func=lambda x: f"상위 {x}개" if x < len(results) else "전체",
                           index=1)

cols_per_row = 3
for row_start in range(0, show_count, cols_per_row):
    row_results = results[row_start:row_start + cols_per_row]
    cols = st.columns(cols_per_row)
    for col, r in zip(cols, row_results):
        c = SIGNAL_COLOR.get(r["signal"], "#9e9e9e")
        with col:
            st.markdown(
                f"<div style='background:{c}18;border:2px solid {c};"
                f"border-radius:10px;padding:14px;margin-bottom:6px'>"
                f"<div style='font-size:1.05rem;font-weight:bold'>{r['name']}</div>"
                f"<div style='color:#aaa;font-size:0.8rem'>{r['ticker']} · {r['market']}</div>"
                f"<hr style='border-color:{c}44;margin:8px 0'>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:3px;font-size:0.83rem'>"
                f"<div>현재가</div><div style='text-align:right'>₩{r['close']:,}</div>"
                f"<div>매수가</div><div style='text-align:right;color:#42a5f5'>₩{r['매수가']:,}</div>"
                f"<div>목표가1</div><div style='text-align:right;color:#26a69a'>₩{r['목표가1']:,} (+{r['수익률1']:.1f}%)</div>"
                f"<div>목표가2</div><div style='text-align:right;color:#00c853'>₩{r['목표가2']:,} (+{r['수익률2']:.1f}%)</div>"
                f"<div>손절가</div><div style='text-align:right;color:#ef5350'>₩{r['손절가']:,} ({r['리스크']:.1f}%)</div>"
                f"<div>손익비</div><div style='text-align:right'>{r['손익비']:.1f}:1</div>"
                f"<div>RSI</div><div style='text-align:right'>{r['rsi']:.0f}</div>"
                f"</div>"
                f"<div style='color:{c};font-weight:bold;margin-top:8px'>{r['signal']} ({r['score']:+d}점)</div>"
                f"{'<div style=\"color:#ffa726;font-size:0.78rem\">' + r['inv_msg'] + '</div>' if r['inv_msg'] else ''}"
                f"</div>",
                unsafe_allow_html=True)

# ── 상세 분석 + 모의투자 연결 ────────────────────────────────────────────────
st.markdown("---")
st.subheader("상세 분석")

sel_name = st.selectbox("종목 선택", [r["name"] for r in results])
sel = next(r for r in results if r["name"] == sel_name)

detail_col, chart_col = st.columns([1, 2])

with detail_col:
    c = SIGNAL_COLOR.get(sel["signal"], "#9e9e9e")
    st.markdown(f"### {sel['name']} ({sel['ticker']})")
    st.markdown(
        f"<div style='background:{c}22;border-left:5px solid {c};"
        f"padding:14px;border-radius:8px'>"
        f"<div style='font-size:1.4rem;font-weight:bold;color:{c}'>{sel['signal']}</div>"
        f"<div style='color:#ccc'>종합 점수: {sel['score']:+d}점</div></div>",
        unsafe_allow_html=True)

    st.markdown("#### 매매 전략")
    df_strat = pd.DataFrame({
        "항목": ["매수가", "1차 목표가", "2차 목표가", "손절가", "예상수익(1차)", "예상수익(2차)", "최대손실", "손익비"],
        "내용": [
            f"₩{sel['매수가']:,}", f"₩{sel['목표가1']:,}", f"₩{sel['목표가2']:,}",
            f"₩{sel['손절가']:,}", f"+{sel['수익률1']:.1f}%", f"+{sel['수익률2']:.1f}%",
            f"{sel['리스크']:.1f}%", f"{sel['손익비']:.1f}:1",
        ]
    }).set_index("항목")
    st.dataframe(df_strat, use_container_width=True)

    st.markdown("#### 분석 근거")
    for reason in sel["reasons"]:
        icon = "🟢" if "+" in reason else "🔴" if "-" in reason else "🟡"
        st.markdown(f"{icon} {reason}")

    if sel["inv_msg"]:
        st.info(f"투자자 동향: {sel['inv_msg']}")

    # ── 모의투자로 보내기 ─────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("💼 이 종목 모의투자로 보내기", type="primary", use_container_width=True):
        st.session_state["paper_prefill"] = {
            "ticker":  sel["ticker"],
            "name":    sel["name"],
            "price":   sel["close"],
            "signal":  sel["signal"],
            "score":   sel["score"],
            "reasons": sel["reasons"],
        }
        st.success(
            f"✅ **{sel['name']}** 정보가 전달됐습니다.  \n"
            f"왼쪽 사이드바에서 **6 모의투자** 페이지로 이동하면  \n"
            f"매수 탭에 자동으로 입력됩니다."
        )

with chart_col:
    df_chart = get_ohlcv(sel["ticker"], months=6)
    df_chart = add_indicators(df_chart)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.2, 0.25], vertical_spacing=0.03,
        subplot_titles=["가격 차트", "거래량", "RSI"])

    fig.add_trace(go.Candlestick(
        x=df_chart.index, open=df_chart["시가"], high=df_chart["고가"],
        low=df_chart["저가"], close=df_chart["종가"], name="가격",
        increasing_line_color="#ef5350", decreasing_line_color="#26a69a"), row=1, col=1)

    for ma, color in [("MA20", "#42a5f5"), ("MA60", "#ab47bc")]:
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart[ma], name=ma,
            line=dict(color=color, width=1.5)), row=1, col=1)

    if "BB_upper" in df_chart.columns:
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["BB_upper"],
            line=dict(color="rgba(128,128,128,0.4)", width=1, dash="dash"),
            showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["BB_lower"],
            line=dict(color="rgba(128,128,128,0.4)", width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(128,128,128,0.05)",
            showlegend=False), row=1, col=1)

    fig.add_hline(y=sel["매수가"],  line_color="#42a5f5", line_dash="dash",
                  annotation_text="매수가",  row=1, col=1)
    fig.add_hline(y=sel["목표가1"], line_color="#26a69a", line_dash="dot",
                  annotation_text="목표1",   row=1, col=1)
    fig.add_hline(y=sel["목표가2"], line_color="#00c853", line_dash="dot",
                  annotation_text="목표2",   row=1, col=1)
    fig.add_hline(y=sel["손절가"],  line_color="#ef5350", line_dash="dash",
                  annotation_text="손절",    row=1, col=1)

    vcol = ["#ef5350" if c >= o else "#26a69a"
            for c, o in zip(df_chart["종가"], df_chart["시가"])]
    fig.add_trace(go.Bar(x=df_chart.index, y=df_chart["거래량"],
        marker_color=vcol, showlegend=False), row=2, col=1)

    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["RSI"], name="RSI",
        line=dict(color="#e040fb", width=1.5)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red",   opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)

    fig.update_layout(height=650, template="plotly_dark",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=60, b=40))
    st.plotly_chart(fig, use_container_width=True)

# ── 전체 테이블 ───────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("전체 추천 종목 테이블"):
    table_data = [{
        "종목명": r["name"], "시장": r["market"],
        "현재가": f"₩{r['close']:,}",
        "매수가": f"₩{r['매수가']:,}",
        "목표가1": f"₩{r['목표가1']:,} (+{r['수익률1']:.1f}%)",
        "목표가2": f"₩{r['목표가2']:,} (+{r['수익률2']:.1f}%)",
        "손절가": f"₩{r['손절가']:,} ({r['리스크']:.1f}%)",
        "손익비": f"{r['손익비']:.1f}:1",
        "RSI": round(r["rsi"], 1),
        "신호": r["signal"], "점수": r["score"],
    } for r in results]
    df_table = pd.DataFrame(table_data)
    def color_sig(v):
        return f"color:{SIGNAL_COLOR.get(v,'#9e9e9e')};font-weight:bold"
    st.dataframe(df_table.style.applymap(color_sig, subset=["신호"]),
                 use_container_width=True, height=400)
