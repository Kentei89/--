import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="성과 분석", page_icon="📊", layout="wide")

from utils.krx     import setup_krx
from utils.storage import (
    load_trades, load_signal_stats, load_weights, save_weights,
    compute_weights_from_stats, DEFAULT_WEIGHTS,
)

setup_krx()

st.title("📊 성과 분석 & 시그널 학습")
st.caption("거래 성과를 분석하고 시그널 가중치를 자동으로 조정합니다")

trades_data = load_trades()
history     = trades_data["history"]

# ── 거래 없을 때 ────────────────────────────────────────────────────────────
if not history:
    st.info("아직 완료된 거래가 없습니다. 모의 투자에서 매도를 완료하면 성과를 분석할 수 있습니다.")
    st.stop()

# ── 기본 통계 ────────────────────────────────────────────────────────────────

wins      = [t for t in history if t["pnl"] > 0]
losses    = [t for t in history if t["pnl"] < 0]
breakeven = [t for t in history if t["pnl"] == 0]
total     = len(history)
win_rate  = len(wins) / total * 100
avg_ret   = sum(t["pnl_pct"] for t in history) / total
total_pnl = sum(t["pnl"] for t in history)
best      = max(history, key=lambda t: t["pnl_pct"])
worst     = min(history, key=lambda t: t["pnl_pct"])
avg_hold  = sum(t.get("holding_days", 0) for t in history) / total

st.subheader("전체 성과 요약")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 거래수",   f"{total}건")
c2.metric("승률",         f"{win_rate:.1f}%",
          f"승{len(wins)} / 패{len(losses)}")
c3.metric("평균 수익률",  f"{avg_ret:+.2f}%")
c4.metric("총 실현손익",  f"₩{total_pnl:+,.0f}",
          delta_color="normal" if total_pnl >= 0 else "inverse")
c5.metric("평균 보유기간", f"{avg_hold:.1f}일")

col_b, col_w = st.columns(2)
col_b.metric("최고 거래",
             f"{best['name']} {best['pnl_pct']:+.2f}%",
             f"₩{best['pnl']:+,.0f}")
col_w.metric("최저 거래",
             f"{worst['name']} {worst['pnl_pct']:+.2f}%",
             f"₩{worst['pnl']:+,.0f}",
             delta_color="inverse")

st.markdown("---")

# ── 수익 차트 ────────────────────────────────────────────────────────────────

st.subheader("손익 추이")

sorted_hist = sorted(history, key=lambda t: t.get("sell_date", ""))
dates  = [t["sell_date"] for t in sorted_hist]
pnl_pcts = [t["pnl_pct"] for t in sorted_hist]
cum_ret  = []
running  = 0.0
for p in pnl_pcts:
    running += p
    cum_ret.append(round(running, 2))

bar_colors = ["#26a69a" if v >= 0 else "#ef5350" for v in pnl_pcts]
fig = go.Figure()
fig.add_trace(go.Bar(
    x=dates, y=pnl_pcts, name="개별 수익률(%)",
    marker_color=bar_colors, opacity=0.8,
))
fig.add_trace(go.Scatter(
    x=dates, y=cum_ret, name="누적 수익률(%)",
    line=dict(color="#ffeb3b", width=2.5),
))
fig.update_layout(
    height=350, template="plotly_dark",
    title="거래별 수익률 & 누적 수익률",
    yaxis_title="%", margin=dict(l=40, r=40, t=50, b=40),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── 시그널별 성과 ────────────────────────────────────────────────────────────

st.subheader("시그널별 성과 분석")

stats = load_signal_stats()
if not stats:
    st.info("아직 시그널 성과 데이터가 없습니다. 매도가 완료되면 자동으로 집계됩니다.")
else:
    SIGNAL_LABELS = {
        "RSI_oversold":   "RSI 과매도",
        "RSI_overbought": "RSI 과매수",
        "MACD_golden":    "MACD 골든크로스",
        "MACD_dead":      "MACD 데드크로스",
        "MACD_above":     "MACD > 시그널",
        "MA5_golden":     "MA5 골든크로스",
        "MA20_above":     "종가 > MA20",
        "MA60_above":     "종가 > MA60",
        "BB_lower":       "볼린저밴드 하단",
        "Stoch_oversold": "스토캐스틱 과매도",
        "Volume_spike":   "거래량 급증+상승",
    }

    rows = []
    for key, s in stats.items():
        cnt = s.get("count", 0)
        if cnt == 0:
            continue
        wr  = s.get("win", 0) / cnt * 100
        avg = s.get("total_return", 0) / cnt
        rows.append({
            "시그널":       SIGNAL_LABELS.get(key, key),
            "발동횟수":      cnt,
            "승":            s.get("win", 0),
            "패":            s.get("loss", 0),
            "승률(%)":       round(wr, 1),
            "평균수익률(%)":  round(avg, 2),
            "평가":          "✅ 효과적" if wr >= 60 and avg > 0
                             else "⚠️ 보통" if wr >= 40
                             else "❌ 비효율",
        })

    df_stats = pd.DataFrame(rows).sort_values("승률(%)", ascending=False)

    def color_wr(val):
        if val >= 60: return "color: #26a69a; font-weight: bold"
        if val >= 40: return "color: #ffeb3b"
        return "color: #ef5350"

    styled_stats = df_stats.style\
        .applymap(color_wr, subset=["승률(%)"])\
        .applymap(
            lambda v: "color: #26a69a" if v > 0 else "color: #ef5350",
            subset=["평균수익률(%)"]
        )
    st.dataframe(styled_stats, use_container_width=True)

    # 승률 바 차트
    if len(df_stats) >= 2:
        fig2 = go.Figure(go.Bar(
            x=df_stats["시그널"],
            y=df_stats["승률(%)"],
            marker_color=[
                "#26a69a" if v >= 60 else "#ffeb3b" if v >= 40 else "#ef5350"
                for v in df_stats["승률(%)"]
            ],
            text=[f"{v:.0f}%" for v in df_stats["승률(%)"]],
            textposition="outside",
        ))
        fig2.add_hline(y=50, line_dash="dash", line_color="#aaa",
                       annotation_text="50% 기준선")
        fig2.update_layout(
            height=300, template="plotly_dark",
            title="시그널별 승률",
            margin=dict(l=40, r=40, t=50, b=80),
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── 시그널 가중치 관리 ────────────────────────────────────────────────────────

st.subheader("🎛️ 시그널 가중치")
st.markdown(
    "거래 성과에 따라 시그널의 영향력을 조정합니다.  \n"
    "가중치 1.0 = 기본, 2.0 = 2배 강조, 0.3 = 약화"
)

current_weights = load_weights()
computed        = compute_weights_from_stats()

GROUP_LABELS = {
    "RSI": "RSI (과매도/과매수)",
    "MACD": "MACD (크로스/모멘텀)",
    "MA": "이동평균선 (MA5/MA20/MA60)",
    "BB": "볼린저밴드",
    "Stoch": "스토캐스틱",
    "Volume": "거래량",
}

w_col1, w_col2 = st.columns(2)

with w_col1:
    st.markdown("**현재 적용 중인 가중치**")
    for k, label in GROUP_LABELS.items():
        val = current_weights.get(k, 1.0)
        bar = "█" * int(val * 5) + "░" * (10 - int(val * 5))
        color = "#26a69a" if val > 1.0 else "#ef5350" if val < 1.0 else "#aaa"
        st.markdown(
            f"**{label}** &nbsp; "
            f"<span style='color:{color};font-family:monospace'>{bar} {val:.2f}x</span>",
            unsafe_allow_html=True,
        )

with w_col2:
    st.markdown("**성과 기반 추천 가중치**")
    if not stats:
        st.info("데이터 부족 (거래 5건 이상 필요)")
    else:
        for k, label in GROUP_LABELS.items():
            cur = current_weights.get(k, 1.0)
            rec = computed.get(k, 1.0)
            arrow = "▲" if rec > cur else "▼" if rec < cur else "─"
            color = "#26a69a" if rec > cur else "#ef5350" if rec < cur else "#aaa"
            st.markdown(
                f"**{label}** &nbsp; "
                f"<span style='color:{color}'>{arrow} {rec:.2f}x</span>",
                unsafe_allow_html=True,
            )

st.markdown("")

btn1, btn2, btn3 = st.columns(3)
with btn1:
    if st.button("✅ 추천 가중치 적용", type="primary", use_container_width=True):
        if not stats:
            st.warning("데이터 부족으로 가중치를 계산할 수 없습니다.")
        else:
            save_weights(computed)
            st.success("가중치가 업데이트되었습니다.")
            st.rerun()
with btn2:
    if st.button("🔄 기본값으로 초기화", use_container_width=True):
        save_weights(DEFAULT_WEIGHTS.copy())
        st.success("기본 가중치로 초기화되었습니다.")
        st.rerun()
with btn3:
    # 수동 가중치 편집
    with st.expander("✏️ 수동 편집"):
        new_w = {}
        for k, label in GROUP_LABELS.items():
            new_w[k] = st.slider(
                label, min_value=0.3, max_value=2.0,
                value=float(current_weights.get(k, 1.0)),
                step=0.1, key=f"slider_{k}",
            )
        if st.button("수동 가중치 저장"):
            save_weights(new_w)
            st.success("저장되었습니다.")
            st.rerun()

st.markdown("---")

# ── 매수 시그널 분포 ──────────────────────────────────────────────────────────

st.subheader("매수 시그널 분포")

signal_counts: dict = {}
for t in history:
    sig = t.get("buy_signal", "알 수 없음")
    signal_counts[sig] = signal_counts.get(sig, 0) + 1

if signal_counts:
    fig3 = go.Figure(go.Pie(
        labels=list(signal_counts.keys()),
        values=list(signal_counts.values()),
        hole=0.4,
    ))
    fig3.update_layout(
        height=280, template="plotly_dark",
        title="매수 시 시그널 유형 분포",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── 보유기간 vs 수익률 ────────────────────────────────────────────────────────

if len(history) >= 3:
    st.subheader("보유기간 vs 수익률")
    df_scatter = pd.DataFrame({
        "보유기간(일)": [t.get("holding_days", 0) for t in history],
        "수익률(%)":    [t["pnl_pct"] for t in history],
        "종목":         [t["name"] for t in history],
        "결과":         [t.get("result", "") for t in history],
    })
    color_map = {"수익": "#26a69a", "손실": "#ef5350", "본전": "#ffeb3b"}
    fig4 = px.scatter(
        df_scatter, x="보유기간(일)", y="수익률(%)",
        color="결과", color_discrete_map=color_map,
        hover_data=["종목"],
        template="plotly_dark",
    )
    fig4.add_hline(y=0, line_dash="dash", line_color="#aaa")
    fig4.update_layout(height=300, margin=dict(l=40, r=40, t=30, b=40))
    st.plotly_chart(fig4, use_container_width=True)
