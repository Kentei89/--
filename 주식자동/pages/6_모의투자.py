import sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from pykrx import stock

st.set_page_config(page_title="모의 투자", page_icon="💼", layout="wide")

from utils.krx    import setup_krx, get_ohlcv, get_etf_ohlcv, last_trading_day, get_realtime_price, get_ticker_list, get_etf_ticker_list_cached
from utils.signals import add_indicators, generate_signal, SIGNAL_COLOR
from utils.storage import (
    load_trades, buy_stock, sell_stock, reset_trades, reset_all,
    load_weights, load_watchlist, save_watchlist, remove_from_watchlist,
    add_to_watchlist, DEFAULT_CAPITAL,
    load_trade_config, save_trade_config,
)
from utils.kis_api import (
    is_configured as _kis_ok,
    get_price     as _kis_price,
    get_balance   as _kis_balance,
    buy_order     as _kis_buy,
    sell_order    as _kis_sell,
)

setup_krx()
_use_api = _kis_ok()

# ── 시간 판단 ─────────────────────────────────────────────────────────────────
_now = datetime.now()
_weekday = _now.weekday() < 5  # 월~금

# 자동 감시용 (넓은 범위 07:30~18:00)
_is_market = (
    _weekday and
    (_now.hour > 7 or (_now.hour == 7 and _now.minute >= 30)) and
    _now.hour < 18
)

# 실제 거래 가능 시간 (08:00~18:00)
_is_trading_hours = _weekday and (8 <= _now.hour < 18)

try:
    from streamlit_autorefresh import st_autorefresh
    if _is_market:
        st_autorefresh(interval=60_000, key="auto_monitor")
except ImportError:
    pass

# ── 하루 1회 자동 스캔 (백그라운드) ─────────────────────────────────────────
_today_str = _now.strftime("%Y-%m-%d")
_cfg = load_trade_config()

def _bg_scan():
    try:
        _root = str(Path(__file__).parent.parent)
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from auto_trader import step_scan as _ss, _setup_krx as _sk
        _sk()
        _ss()
        save_trade_config({"last_scan_date": datetime.now().strftime("%Y-%m-%d")})
    except Exception:
        pass

if (_is_market
        and _cfg.get("last_scan_date", "") != _today_str
        and not st.session_state.get("_scan_started")):
    st.session_state["_scan_started"] = True
    threading.Thread(target=_bg_scan, daemon=True).start()

# 자동 매도/매수 실행 (장 중에만)
_executed_sells = []
_executed_buys  = []
if _is_market:
    try:
        from auto_trader import step_sell as _step_sell, step_buy as _step_buy
        _executed_sells = _step_sell()
        _executed_buys  = _step_buy()
    except Exception:
        pass

st.title("💼 모의 투자")
st.caption("가상 자금으로 매수·매도를 연습하고 시그널 성과를 추적합니다")

# 감시 상태 표시
_scan_done_today = (load_trade_config().get("last_scan_date", "") == _today_str)
_api_badge = "🔗 KIS 모의투자 API 연결됨" if _use_api else "📁 로컬 모드"
if _is_market:
    _parts = [f"🟢 감시 중 | 마지막 체크: {_now.strftime('%H:%M:%S')}", _api_badge]
    if st.session_state.get("_scan_started") and not _scan_done_today:
        _parts.append("📡 종목 스캔 중 (백그라운드)")
    elif _scan_done_today:
        _parts.append("✅ 오늘 스캔 완료")
    if _executed_buys:
        _parts.append(f"자동매수 {len(_executed_buys)}건 체결")
    if _executed_sells:
        _parts.append(f"자동매도 {len(_executed_sells)}건 체결")
    st.success("  ·  ".join(_parts))
else:
    _reason = "주말" if _now.weekday() >= 5 else "장외 시간"
    st.info(f"⏸️ {_reason} — 자동 감시 중지 ({_now.strftime('%H:%M')})  ·  {_api_badge}")

# ── 현재 가격 헬퍼 ────────────────────────────────────────────────────────────

def fetch_price_and_signal(ticker: str, is_etf: bool = False):
    """(current_price, signal, score, reasons, df) 반환. 실패 시 None."""
    try:
        df = get_etf_ohlcv(ticker, months=6) if is_etf else get_ohlcv(ticker, months=6)
        if df is None or df.empty or len(df) < 30:
            return None
        df = add_indicators(df)
        weights = load_weights()
        signal, score, reasons = generate_signal(df, weights)
        rt = get_realtime_price(ticker)
        price = rt["price"] if rt else int(df["종가"].iloc[-1])
        return price, signal, score, reasons, df
    except Exception:
        return None


def get_name(ticker: str) -> str:
    try:
        return stock.get_market_ticker_name(ticker)
    except Exception:
        return ticker


# ── 포트폴리오 요약 ───────────────────────────────────────────────────────────

data = load_trades()
positions = data["positions"]
history   = data["history"]
cash      = data["capital"]

pos_with_price = []
for p in positions:
    # KIS API 우선 → 네이버 → pykrx 종가 순 fallback
    if _use_api:
        kp = _kis_price(p["ticker"])
        if kp and kp["price"] > 0:
            current_price    = kp["price"]
            price_change     = kp["change"]
            price_change_pct = kp["change_pct"]
            price_source     = "KIS(실시간)"
        else:
            current_price, price_change, price_change_pct = p["buy_price"], 0, 0.0
            price_source = "KIS오류"
    else:
        rt = get_realtime_price(p["ticker"])
        if rt:
            current_price    = rt["price"]
            price_change     = rt["change"]
            price_change_pct = rt["change_pct"]
            price_source     = "네이버(실시간)"
        else:
            res = fetch_price_and_signal(p["ticker"])
            current_price    = res[0] if res else p["buy_price"]
            price_change, price_change_pct = 0, 0.0
            price_source     = "KRX(종가)"
    pos_with_price.append({
        **p,
        "current_price":     current_price,
        "market_value":      current_price * p["quantity"],
        "pnl":               (current_price - p["buy_price"]) * p["quantity"],
        "pnl_pct":           (current_price - p["buy_price"]) / p["buy_price"] * 100,
        "price_change":      price_change,
        "price_change_pct":  price_change_pct,
        "price_source":      price_source,
    })

pos_value   = sum(p["market_value"] for p in pos_with_price)
invested    = sum(p["buy_price"] * p["quantity"] for p in pos_with_price)
total_pnl   = pos_value - invested

# KIS API 연결 시 실제 예수금으로 덮어쓰기
if _use_api:
    _bal = _kis_balance()
    if _bal.get("cash", 0) > 0:
        cash = _bal["cash"]
total_asset = cash + pos_value

col1, col2, col3, col4 = st.columns(4)
col1.metric("총 자산", f"₩{total_asset:,.0f}",
            f"{total_pnl:+,.0f}원" if pos_with_price else None,
            delta_color="inverse" if total_pnl >= 0 else "normal")
col2.metric("예수금 (현금)", f"₩{cash:,.0f}")
col3.metric("평가금액", f"₩{pos_value:,.0f}")
col4.metric("평가손익", f"₩{total_pnl:+,.0f}",
            f"{total_pnl/invested*100:+.2f}%" if invested > 0 else None,
            delta_color="inverse" if total_pnl >= 0 else "normal")

st.markdown("---")

# ── 탭 ───────────────────────────────────────────────────────────────────────

tab_pos, tab_buy, tab_sell, tab_watch, tab_hist, tab_settings = st.tabs(
    ["📊 포지션", "📈 매수", "📉 매도", "👁️ 감시목록", "📋 거래내역", "⚙️ 설정"]
)

# ════════════════════════════════════════════════════════════════════════════════
# 탭 1: 현재 포지션
# ════════════════════════════════════════════════════════════════════════════════
with tab_pos:
    if not pos_with_price:
        st.info("보유 중인 포지션이 없습니다. 매수 탭에서 종목을 매수하세요.")
    else:
        _src_label = "KIS실시간" if _use_api else "네이버(1~2분 지연)"
        st.caption(f"현재가 기준: {_src_label} · {_now.strftime('%H:%M:%S')} 조회 · 1분마다 자동 갱신")
        rows = []
        for p in pos_with_price:
            chg_sign = "▲" if p["price_change"] > 0 else "▼" if p["price_change"] < 0 else "─"
            rows.append({
                "구분":        "🤖 자동" if p.get("is_auto") else "👤 수동",
                "종목명":     p["name"],
                "현재가":      p["current_price"],
                "등락":        f"{chg_sign}{abs(p['price_change']):,} ({p['price_change_pct']:+.2f}%)",
                "수량":        p["quantity"],
                "매수가":      p["buy_price"],
                "평가금액":    p["market_value"],
                "평가손익":    p["pnl"],
                "수익률":      p["pnl_pct"],
                "매수일":      p["buy_date"],
                "매수시그널":  p["buy_signal"],
            })
        df_pos = pd.DataFrame(rows)

        def color_pnl(val):
            color = "#ef5350" if val >= 0 else "#1565c0"
            return f"color: {color}"

        styled = df_pos.style\
            .applymap(color_pnl, subset=["평가손익", "수익률"])\
            .format({
                "매수가":   "₩{:,.0f}",
                "현재가":   "₩{:,.0f}",
                "평가금액": "₩{:,.0f}",
                "평가손익": "₩{:+,.0f}",
                "수익률":   "{:+.2f}%",
            })
        st.dataframe(styled, use_container_width=True)

        # 매수 이유 상세 보기
        st.markdown("**매수 근거 상세**")
        for p in pos_with_price:
            with st.expander(f"{p['name']} ({p['ticker']}) — 매수일 {p['buy_date']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**매수 시그널:** `{p['buy_signal']}` (점수 {p['buy_score']})")
                    st.markdown("**매수 근거:**")
                    for r in p.get("buy_reasons", []):
                        st.markdown(f"  - {r}")
                    if p.get("buy_note"):
                        st.markdown(f"**메모:** {p['buy_note']}")
                with c2:
                    pnl_color = "#ef5350" if p["pnl"] >= 0 else "#1565c0"
                    st.markdown(
                        f"<div style='text-align:center; font-size:1.4rem; color:{pnl_color}'>"
                        f"₩{p['pnl']:+,.0f}<br>"
                        f"<span style='font-size:1rem'>{p['pnl_pct']:+.2f}%</span></div>",
                        unsafe_allow_html=True,
                    )

# ════════════════════════════════════════════════════════════════════════════════
# 탭 2: 매수
# ════════════════════════════════════════════════════════════════════════════════
with tab_buy:
    st.subheader("종목 분석 후 매수")

    # 종목추천 페이지에서 넘어온 경우 자동 입력
    prefill = st.session_state.pop("paper_prefill", None)
    if prefill:
        st.success(
            f"종목추천에서 **{prefill['name']}** 정보가 전달됐습니다. 아래에서 수량을 입력 후 매수하세요."
        )
        st.session_state["buy_analysis"] = prefill

    asset_type = st.radio("종류", ["주식", "ETF"], horizontal=True, key="buy_asset_type")
    search_by  = st.radio("검색 방법", ["종목명", "종목코드"], horizontal=True, key="buy_search_by")

    ticker_input = None
    buy_name     = ""
    is_etf_buy   = (asset_type == "ETF")

    if search_by == "종목명":
        with st.spinner("목록 로딩..."):
            if is_etf_buy:
                name_map = get_etf_ticker_list_cached()  # {이름: 코드}
            else:
                raw_map  = get_ticker_list()              # {이름: (코드, 시장)}
                name_map = {n: v[0] for n, v in raw_map.items()}
        names = sorted(name_map.keys())
        sel   = st.selectbox("종목명 검색 (직접 입력 가능)", names, key="buy_name_sel")
        ticker_input = name_map.get(sel, "")
        buy_name     = sel
    else:
        ticker_input = st.text_input("종목코드 (6자리)", max_chars=6, key="buy_ticker").zfill(6)
        buy_name     = ""

    analyze_btn = st.button("종목 분석", type="primary", use_container_width=True)

    if analyze_btn and ticker_input and ticker_input != "000000":
        with st.spinner("분석 중..."):
            result = fetch_price_and_signal(ticker_input, is_etf=is_etf_buy)
        if result is None:
            st.error("데이터를 가져올 수 없습니다. 종목코드를 확인하세요.")
            st.session_state.pop("buy_analysis", None)
        else:
            price, signal, score, reasons, df = result
            name = buy_name or get_name(ticker_input)
            st.session_state["buy_analysis"] = {
                "ticker":  ticker_input,
                "name":    name,
                "price":   price,
                "signal":  signal,
                "score":   score,
                "reasons": reasons,
                "is_etf":  is_etf_buy,
            }

    if "buy_analysis" in st.session_state:
        ana = st.session_state["buy_analysis"]
        sig_color = SIGNAL_COLOR.get(ana["signal"], "#9e9e9e")

        st.markdown(
            f"<div style='padding:12px;border-radius:8px;border-left:4px solid {sig_color};"
            f"background:#1e1e2e'>"
            f"<b>{ana['name']}</b> ({ana['ticker']}) &nbsp;&nbsp; "
            f"현재가: <b>₩{ana['price']:,}</b> &nbsp;&nbsp; "
            f"<span style='color:{sig_color};font-size:1.1rem'><b>{ana['signal']}</b></span> "
            f"(점수 {ana['score']:+d})</div>",
            unsafe_allow_html=True,
        )

        st.markdown("**시그널 분석 근거:**")
        for r in ana["reasons"]:
            icon = "🟢" if "+" in r else "🔴" if "-" in r else "⚪"
            st.markdown(f"{icon} {r}")

        st.markdown("---")

        if not _is_trading_hours:
            _reason_t = "주말" if not _weekday else f"장 시간 외 ({_now.strftime('%H:%M')} / 거래 가능: 08:00~18:00)"
            st.warning(f"⏸️ {_reason_t} — 매수할 수 없습니다.")

        with st.form("buy_form"):
            col_q, col_p = st.columns(2)
            with col_q:
                qty = st.number_input("매수 수량 (주)", min_value=1, value=1, step=1)
            with col_p:
                buy_price = st.number_input("매수가 (원)", min_value=1,
                                            value=int(ana["price"]), step=100)
            trade_val  = buy_price * qty
            commission = round(trade_val * 0.00015)
            cost       = trade_val + commission
            st.info(f"매수 금액: ₩{trade_val:,.0f}  |  수수료: ₩{commission:,}  |  "
                    f"총 필요금액: ₩{cost:,.0f}  |  잔여: ₩{cash - cost:,.0f}")

            note = st.text_area("매수 메모 (선택)", placeholder="매수 이유, 목표가 등 자유롭게 입력")
            submitted = st.form_submit_button(
                "✅ 매수 확정", type="primary",
                disabled=not _is_trading_hours,
            )

        if submitted:
            if cost > cash:
                st.error(f"예수금 부족 — 필요 ₩{cost:,.0f}, 보유 ₩{cash:,.0f}")
            elif qty <= 0:
                st.error("수량을 1주 이상 입력하세요.")
            else:
                try:
                    # KIS API 실제 주문
                    if _use_api:
                        _kis_buy(ana["ticker"], qty, buy_price)
                        st.info("📡 KIS 모의투자 매수 주문 전송됨")

                    buy_stock(
                        ticker=ana["ticker"],
                        name=ana["name"],
                        quantity=qty,
                        price=buy_price,
                        signal=ana["signal"],
                        score=ana["score"],
                        reasons=ana["reasons"],
                        note=note,
                    )
                    st.success(
                        f"✅ {ana['name']} {qty}주를 ₩{buy_price:,}에 매수했습니다."
                    )
                    del st.session_state["buy_analysis"]
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

# ════════════════════════════════════════════════════════════════════════════════
# 탭 3: 매도
# ════════════════════════════════════════════════════════════════════════════════
with tab_sell:
    if not pos_with_price:
        st.info("보유 중인 포지션이 없습니다.")
    else:
        choices = {
            f"{p['name']} ({p['ticker']}) — {p['quantity']}주 @ ₩{p['buy_price']:,}": p["id"]
            for p in pos_with_price
        }
        selected_label = st.selectbox("매도할 포지션 선택", list(choices.keys()))
        sel_id  = choices[selected_label]
        sel_pos = next(p for p in pos_with_price if p["id"] == sel_id)

        # 현재 분석 표시
        pnl_color = "#ef5350" if sel_pos["pnl"] >= 0 else "#1565c0"
        st.markdown(
            f"<div style='padding:10px;border-radius:6px;background:#1e1e2e'>"
            f"현재가 <b>₩{sel_pos['current_price']:,}</b> &nbsp;|&nbsp; "
            f"평가손익 <span style='color:{pnl_color}'><b>₩{sel_pos['pnl']:+,.0f} "
            f"({sel_pos['pnl_pct']:+.2f}%)</b></span></div>",
            unsafe_allow_html=True,
        )

        # 현재 시그널 분석
        if st.button("현재 시그널 분석", key="sell_analyze"):
            with st.spinner("분석 중..."):
                result = fetch_price_and_signal(sel_pos["ticker"])
            if result:
                _, signal, score, reasons, _ = result
                st.session_state["sell_analysis"] = {
                    "id": sel_id, "signal": signal,
                    "score": score, "reasons": reasons,
                }

        if st.session_state.get("sell_analysis", {}).get("id") == sel_id:
            sa = st.session_state["sell_analysis"]
            sig_color = SIGNAL_COLOR.get(sa["signal"], "#9e9e9e")
            st.markdown(
                f"<span style='color:{sig_color}'><b>현재 시그널: {sa['signal']} "
                f"(점수 {sa['score']:+d})</b></span>",
                unsafe_allow_html=True,
            )
            for r in sa["reasons"]:
                icon = "🟢" if "+" in r else "🔴" if "-" in r else "⚪"
                st.markdown(f"{icon} {r}")
            sell_reasons = sa["reasons"]
        else:
            sell_reasons = []

        st.markdown("---")
        if not _is_trading_hours:
            _reason_t = "주말" if not _weekday else f"장 시간 외 ({_now.strftime('%H:%M')} / 거래 가능: 08:00~18:00)"
            st.warning(f"⏸️ {_reason_t} — 매도할 수 없습니다.")

        with st.form("sell_form"):
            sell_price = st.number_input(
                "매도가 (원)", min_value=1,
                value=int(sel_pos["current_price"]), step=100,
            )
            sell_note = st.text_area("매도 메모", placeholder="매도 이유, 소감 등")
            sell_btn  = st.form_submit_button(
                "✅ 매도 확정", type="primary",
                disabled=not _is_trading_hours,
            )

        if sell_btn:
            final_reasons = sell_reasons if sell_reasons else [f"수동 매도 — 매도가 ₩{sell_price:,}"]
            try:
                # KIS API 실제 주문
                if _use_api:
                    _kis_sell(sel_pos["ticker"], sel_pos["quantity"], sell_price)
                    st.info("📡 KIS 모의투자 매도 주문 전송됨")

                record = sell_stock(
                    position_id=sel_id,
                    sell_price=sell_price,
                    sell_reasons=final_reasons,
                    note=sell_note,
                )
                st.success(
                    f"✅ {sel_pos['name']} 매도 완료 | "
                    f"손익: ₩{record['pnl']:+,.0f} ({record['pnl_pct']:+.2f}%)"
                )
                st.session_state.pop("sell_analysis", None)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ════════════════════════════════════════════════════════════════════════════════
# 탭 4: 감시 목록 (자동매매 대기)
# ════════════════════════════════════════════════════════════════════════════════
with tab_watch:
    st.subheader("자동매매 감시 목록")
    st.caption("auto_trader.py가 실행될 때 현재가가 매수가 이하이면 자동 매수됩니다")

    wl = load_watchlist()
    if not wl:
        st.info("감시 중인 종목이 없습니다. 종목추천/ETF추천에서 '모의투자로 보내기' 후 수동 추가하거나, auto_trader.py를 실행하세요.")
    else:
        today_str = datetime.now().strftime("%Y-%m-%d")
        rows = []
        for w in wl:
            rt = get_realtime_price(w["ticker"])
            cur = rt["price"] if rt else None
            gap = f"{(cur/w['buy_price']-1)*100:+.1f}%" if cur else "—"
            status = "✅ 매수 가능" if cur and cur <= w["buy_price"] * 1.01 else "⏳ 대기 중"
            rows.append({
                "종목명":   w["name"],
                "시그널":   f"{w['signal']} ({w['score']:+d}점)",
                "매수 대기가": f"₩{w['buy_price']:,}",
                "현재가":   f"₩{cur:,}" if cur else "—",
                "gap":      gap,
                "목표가1":  f"₩{w['target1']:,}",
                "손절가":   f"₩{w['stop']:,}",
                "만료일":   w.get("expires", "—"),
                "상태":     status,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        # 개별 삭제
        del_name = st.selectbox("삭제할 종목", ["선택 안 함"] + [w["name"] for w in wl])
        if del_name != "선택 안 함" and st.button("감시 목록에서 제거", type="secondary"):
            ticker_to_del = next(w["ticker"] for w in wl if w["name"] == del_name)
            remove_from_watchlist(ticker_to_del)
            st.success(f"{del_name} 제거 완료")
            st.rerun()

    st.markdown("---")
    c_clear, c_run = st.columns(2)
    with c_clear:
        st.markdown("**감시목록 전체 초기화**")
        st.caption("초기화 후 스캔 실행 시 새 점수 기준으로 전부 재평가됩니다")
        if st.button("🗑️ 감시목록 전체 삭제", type="secondary", use_container_width=True):
            save_watchlist([])
            st.success("감시목록이 초기화됐습니다.")
            st.rerun()

    with c_run:
        st.markdown("**자동매매 수동 실행**")
        st.caption("스캔 + 매수/매도 + 일지 작성을 지금 즉시 실행합니다 (2~5분 소요)")
        if st.button("▶ auto_trader.py 지금 실행", type="primary", use_container_width=True):
            import subprocess, sys
            with st.spinner("스캔 중... 종목 수에 따라 2~5분 소요됩니다. 기다려 주세요."):
                result = subprocess.run(
                    [sys.executable, "auto_trader.py"],
                    capture_output=True, text=True, encoding="utf-8",
                    cwd=str(Path(__file__).parent.parent),
                    timeout=600,
                )
            if result.returncode == 0:
                st.success("✅ 자동매매 실행 완료! 감시목록과 매매일지를 확인하세요.")
            else:
                st.error(f"실행 오류:\n{result.stderr[-1000:]}")
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# 탭 5: 거래내역
# ════════════════════════════════════════════════════════════════════════════════
with tab_hist:
    if not history:
        st.info("아직 완료된 거래가 없습니다.")
    else:
        rows = []
        for t in reversed(history):
            rows.append({
                "구분":      "🤖 자동" if t.get("is_auto") else "👤 수동",
                "매도일":   t.get("sell_date", ""),
                "종목명":   t["name"],
                "수량":      t["quantity"],
                "매수가":    t["buy_price"],
                "매도가":    t["sell_price"],
                "손익":      t["pnl"],
                "수익률":    t["pnl_pct"],
                "보유일":    t.get("holding_days", 0),
                "결과":      t.get("result", ""),
                "매수시그널": t.get("buy_signal", ""),
            })
        df_hist = pd.DataFrame(rows)

        def color_result(val):
            if val == "수익": return "color: #ef5350"
            if val == "손실": return "color: #1565c0"
            return ""

        styled_h = df_hist.style\
            .applymap(color_result, subset=["결과"])\
            .applymap(lambda v: "color: #ef5350" if v >= 0 else "color: #1565c0",
                      subset=["손익", "수익률"])\
            .format({"매수가": "₩{:,.0f}", "매도가": "₩{:,.0f}",
                     "손익": "₩{:+,.0f}", "수익률": "{:+.2f}%"})
        st.dataframe(styled_h, use_container_width=True)

        # 요약 지표 — 전체 / AI / 수동 구분
        st.markdown("---")
        auto_h   = [t for t in history if t.get("is_auto")]
        manual_h = [t for t in history if not t.get("is_auto")]

        def _stats_cols(label: str, subset: list, cols):
            n = len(subset)
            w = len([t for t in subset if t["pnl"] > 0])
            cols[0].metric(f"{label} 거래", f"{n}건")
            cols[1].metric("승률",       f"{w/n*100:.1f}%" if n else "—")
            cols[2].metric("평균 수익률",
                           f"{sum(t['pnl_pct'] for t in subset)/n:+.2f}%" if n else "—")
            total_pnl_v = sum(t['pnl'] for t in subset)
            cols[3].metric("실현손익",
                           f"₩{total_pnl_v:+,.0f}",
                           delta_color="inverse" if total_pnl_v >= 0 else "normal")

        st.markdown("**📊 전체**")
        _stats_cols("전체", history, st.columns(4))
        st.markdown("**🤖 AI 자동매매**")
        _stats_cols("AI", auto_h, st.columns(4))
        st.markdown("**👤 내 수동매매**")
        _stats_cols("수동", manual_h, st.columns(4))

        # 거래별 상세
        st.markdown("**거래별 매수/매도 근거 상세**")
        for t in reversed(history):
            _badge = "🤖자동" if t.get("is_auto") else "👤수동"
            label = (f"{t['sell_date']} | {_badge} | {t['name']} | "
                     f"{'수익 ✅' if t['pnl'] > 0 else '손실 ❌'} "
                     f"₩{t['pnl']:+,.0f} ({t['pnl_pct']:+.2f}%)")
            with st.expander(label):
                bc, sc = st.columns(2)
                with bc:
                    st.markdown(f"**매수 ({t['buy_date']} {t.get('buy_time','')})**")
                    st.markdown(f"시그널: `{t.get('buy_signal','')}` (점수 {t.get('buy_score',0):+d})")
                    for r in t.get("buy_reasons", []):
                        st.markdown(f"  - {r}")
                    if t.get("buy_note"):
                        st.markdown(f"메모: {t['buy_note']}")
                with sc:
                    st.markdown(f"**매도 ({t.get('sell_date','')} {t.get('sell_time','')})**")
                    for r in t.get("sell_reasons", []):
                        st.markdown(f"  - {r}")
                    if t.get("sell_note"):
                        st.markdown(f"메모: {t['sell_note']}")
                st.markdown(
                    f"보유기간: {t.get('holding_days', 0)}일 | "
                    f"손익: ₩{t['buy_price']:,} → ₩{t['sell_price']:,}"
                )

        # 손익 차트
        if len(history) >= 2:
            dates  = [t["sell_date"] for t in history]
            pnls   = [t["pnl"] for t in history]
            cum    = [sum(pnls[:i+1]) for i in range(len(pnls))]
            colors = ["#ef5350" if v >= 0 else "#1565c0" for v in pnls]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=dates, y=pnls, name="개별 손익",
                                 marker_color=colors))
            fig.add_trace(go.Scatter(x=dates, y=cum, name="누적 손익",
                                     line=dict(color="#ffeb3b", width=2)))
            fig.update_layout(height=350, template="plotly_dark",
                              title="거래 손익 추이",
                              margin=dict(l=40, r=40, t=50, b=40))
            st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# 탭 5: 설정
# ════════════════════════════════════════════════════════════════════════════════
with tab_settings:
    st.subheader("⚙️ 모의 투자 설정")

    # ── 투자 스타일 ─────────────────────────────────────────────────────────────
    st.markdown("**투자 스타일**")
    _cur_cfg   = load_trade_config()
    _cur_style = _cur_cfg.get("style", "안정형")

    style_col1, style_col2 = st.columns(2)
    with style_col1:
        sel_style = st.radio(
            "자동매매 스타일 선택",
            ["안정형", "성장형"],
            index=0 if _cur_style == "안정형" else 1,
            horizontal=True,
        )

    _style_info = {
        "안정형": {
            "desc":       "적게 잃는 것을 우선합니다. 신호가 확실할 때만 진입하고 손절 폭을 좁게 설정합니다.",
            "min_score":  "6점 이상",
            "max_pct":    "종목당 최대 7%",
            "atr_stop":   "손절 ATR × 1.5",
            "atr_target": "목표1 ATR × 2.5 / 목표2 ATR × 3.5",
        },
        "성장형": {
            "desc":       "크게 버는 것을 목표합니다. 더 많은 기회에 진입하고 목표가를 높게 설정합니다.",
            "min_score":  "4점 이상",
            "max_pct":    "종목당 최대 15%",
            "atr_stop":   "손절 ATR × 2.5",
            "atr_target": "목표1 ATR × 3.5 / 목표2 ATR × 5.5",
        },
    }

    with style_col2:
        info = _style_info[sel_style]
        st.info(
            f"**{sel_style}** — {info['desc']}\n\n"
            f"- 최소 점수: {info['min_score']}\n"
            f"- 비중 한도: {info['max_pct']}\n"
            f"- 손절: {info['atr_stop']}\n"
            f"- 목표: {info['atr_target']}"
        )

    if st.button("✅ 스타일 저장", type="primary"):
        save_trade_config({"style": sel_style})
        st.success(f"투자 스타일이 **{sel_style}**으로 저장됐습니다. 다음 스캔부터 반영됩니다.")

    st.markdown("---")

    # ── 초기 자금 설정 ──────────────────────────────────────────────────────────
    st.markdown("**초기 자금 설정**")

    if "cap_input" not in st.session_state:
        st.session_state["cap_input"] = DEFAULT_CAPITAL

    qb1, qb2, qb3, qb4 = st.columns(4)
    if qb1.button("1억",  use_container_width=True): st.session_state["cap_input"] = 100_000_000
    if qb2.button("천만", use_container_width=True): st.session_state["cap_input"] = 10_000_000
    if qb3.button("백만", use_container_width=True): st.session_state["cap_input"] = 1_000_000
    if qb4.button("십만", use_container_width=True): st.session_state["cap_input"] = 100_000

    init_cap = st.number_input(
        "초기 자금 직접 입력 (원)",
        min_value=100_000, step=100_000, key="cap_input",
    )

    st.markdown("---")

    # ── 3단계 초기화 ────────────────────────────────────────────────────────────
    st.markdown("**초기화**")

    rc1, rc2, rc3 = st.columns(3)

    with rc1:
        st.markdown("**거래 초기화**")
        st.caption("포지션·거래내역·자금만 리셋. 감시목록·통계는 유지.")
        if st.button("🔄 거래 초기화", use_container_width=True, type="secondary",
                     key="reset_trades_btn"):
            st.session_state["confirm_reset"] = "trades"

    with rc2:
        st.markdown("**감시목록 초기화**")
        st.caption("자동매매 감시 중인 종목 목록만 삭제.")
        if st.button("🗑️ 감시목록 초기화", use_container_width=True, type="secondary",
                     key="reset_watch_btn"):
            st.session_state["confirm_reset"] = "watchlist"

    with rc3:
        st.markdown("**전체 초기화**")
        st.caption("거래·감시목록·매매통계·가중치·일지 전부 삭제.")
        if st.button("⚠️ 전체 초기화", use_container_width=True, type="secondary",
                     key="reset_all_btn"):
            st.session_state["confirm_reset"] = "all"

    confirm = st.session_state.get("confirm_reset")
    if confirm:
        _labels = {
            "trades":    "거래 초기화 (포지션·내역·자금 삭제)",
            "watchlist": "감시목록 초기화 (감시 종목 전체 삭제)",
            "all":       "전체 초기화 (모든 데이터 삭제)",
        }
        st.error(f"⚠️ 정말 **{_labels[confirm]}** 하시겠습니까? 되돌릴 수 없습니다.")
        cc1, cc2 = st.columns(2)
        if cc1.button("✅ 확인, 초기화합니다", type="primary", use_container_width=True):
            if confirm == "trades":
                reset_trades(int(init_cap))
                st.success(f"거래 초기화 완료 — 초기 자금 ₩{int(init_cap):,.0f}")
            elif confirm == "watchlist":
                save_watchlist([])
                st.success("감시목록 초기화 완료")
            elif confirm == "all":
                reset_all(int(init_cap))
                st.success(f"전체 초기화 완료 — 초기 자금 ₩{int(init_cap):,.0f}")
            st.session_state.pop("confirm_reset", None)
            st.rerun()
        if cc2.button("❌ 취소", use_container_width=True):
            st.session_state.pop("confirm_reset", None)
            st.rerun()
