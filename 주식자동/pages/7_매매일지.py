import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="매매일지", page_icon="📓", layout="wide")

from utils.krx     import setup_krx
from utils.storage import load_trades, load_journal

setup_krx()

st.title("📓 매매일지")
st.caption("auto_trader.py가 매일 장 마감 후 자동으로 작성합니다")

journal_entries = load_journal()
trades_data     = load_trades()
history         = trades_data["history"]
positions       = trades_data["positions"]

# ── 최신 일지 ────────────────────────────────────────────────────────────────
if journal_entries:
    latest = journal_entries[0]
    st.subheader(f"최신 일지 — {latest['date']}")

    if latest.get("market_note"):
        st.info(f"시장: {latest['market_note']}")

    st.markdown(latest.get("content", "내용 없음"))
    st.markdown("---")

# ── 일지 목록 ────────────────────────────────────────────────────────────────
st.subheader("전체 일지 목록")

if not journal_entries:
    st.info("아직 일지가 없습니다. auto_trader.py를 실행하면 자동으로 생성됩니다.")
else:
    for entry in journal_entries:
        label = f"📓 {entry['date']}"
        if entry.get("market_note"):
            label += f"  —  {entry['market_note']}"
        with st.expander(label):
            st.markdown(entry.get("content", "내용 없음"))

st.markdown("---")

# ── 날짜별 거래 내역 ──────────────────────────────────────────────────────────
st.subheader("날짜별 거래 내역")

all_dates = sorted(
    set(t.get("buy_date","")  for t in history) |
    set(t.get("sell_date","") for t in history) |
    set(p.get("buy_date","")  for p in positions),
    reverse=True,
)

if not all_dates:
    st.info("거래 내역이 없습니다.")
else:
    rows = []
    for d in all_dates:
        b_cnt  = len([t for t in history   if t.get("buy_date")  == d])
        b_cnt += len([p for p in positions if p.get("buy_date")  == d])
        s_cnt  = len([t for t in history   if t.get("sell_date") == d])
        day_pnl = sum(t["pnl"] for t in history if t.get("sell_date") == d)
        auto_cnt = len([t for t in history if t.get("sell_date") == d and t.get("is_auto")])
        rows.append({
            "날짜":      d,
            "매수건":    b_cnt,
            "매도건":    s_cnt,
            "자동매도":  auto_cnt,
            "당일손익":  day_pnl,
        })

    df_sum = pd.DataFrame(rows)
    styled = df_sum.style.applymap(
        lambda v: "color:#26a69a" if v > 0 else ("color:#ef5350" if v < 0 else ""),
        subset=["당일손익"]
    ).format({"당일손익": "₩{:+,.0f}"})
    st.dataframe(styled, use_container_width=True)

    # 날짜 선택해서 상세 보기
    sel_date = st.selectbox("상세 보기", all_dates)
    buys_day  = [t for t in history   if t.get("buy_date")  == sel_date]
    buys_day += [p for p in positions if p.get("buy_date")  == sel_date]
    sells_day = [t for t in history   if t.get("sell_date") == sel_date]

    if buys_day:
        st.markdown(f"**{sel_date} 매수 기록**")
        for t in buys_day:
            auto_badge = " 🤖자동" if t.get("is_auto") else ""
            st.markdown(
                f"- **{t['name']}** {t['quantity']}주 @ ₩{t['buy_price']:,}"
                f"  |  {t.get('buy_signal','')} {t.get('buy_score',0):+d}점{auto_badge}"
            )
            for r in t.get("buy_reasons", [])[:3]:
                st.markdown(f"  &nbsp;&nbsp;• {r}")

    if sells_day:
        st.markdown(f"**{sel_date} 매도 기록**")
        for t in sells_day:
            icon = "✅" if t["pnl"] > 0 else "❌"
            auto_badge = " 🤖자동" if t.get("is_auto") else ""
            st.markdown(
                f"{icon} **{t['name']}** @ ₩{t['sell_price']:,}"
                f"  |  {t['pnl_pct']:+.2f}% (₩{t['pnl']:+,}){auto_badge}"
            )
            for r in t.get("sell_reasons", [])[:2]:
                st.markdown(f"  &nbsp;&nbsp;• {r}")
