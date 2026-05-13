"""
자동 매매 스크립트
- Windows 작업 스케줄러로 매일 오후 4시 실행 권장
- 직접 실행: python auto_trader.py
- 장 마감 후 실행 시: 종가 기준 자동 체결
"""
import sys, os, time, logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

import requests
import pandas as pd
from pykrx import stock

from utils.signals import add_indicators, generate_signal, calc_targets as _sig_calc_targets
from utils.storage import (
    load_trades, save_trades, buy_stock, sell_stock,
    load_weights, load_watchlist, save_watchlist,
    add_to_watchlist, remove_from_watchlist, clean_expired_watchlist,
    upsert_journal, load_trade_config, load_journal,
)
from utils.kis_api import is_configured as _kis_ok, get_price as _kis_price
from utils.kis_api import buy_order as _kis_buy, sell_order as _kis_sell

# ── 로그 설정 ──────────────────────────────────────────────────────────────────
LOG_FILE = Path(__file__).parent / "data" / "auto_trader.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("AutoTrader")

# ── 기본 설정 ──────────────────────────────────────────────────────────────────
CONFIG = {
    "markets":       ["KOSPI", "KOSDAQ"],
    "scan_count":    100,
    "max_positions": 10,
    "buy_tolerance": 0.01,
    "delay":         0.25,
}

# 투자 스타일별 파라미터
_STYLE_PARAMS = {
    "안정형": {
        "min_buy_score": 6,
        "max_pos_pct":   0.07,
        "atr_stop":      1.5,
        "atr_t1":        2.5,
        "atr_t2_base":   3.5,
    },
    "성장형": {
        "min_buy_score": 4,
        "max_pos_pct":   0.15,
        "atr_stop":      2.5,
        "atr_t1":        3.5,
        "atr_t2_base":   5.5,
    },
}


def _get_style() -> dict:
    """저장된 투자 스타일 파라미터 반환."""
    style = load_trade_config().get("style", "안정형")
    return _STYLE_PARAMS.get(style, _STYLE_PARAMS["안정형"])


# ── KRX 인증 ───────────────────────────────────────────────────────────────────
def _setup_krx():
    secrets = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if secrets.exists():
        try:
            import tomllib
            with open(secrets, "rb") as f:
                s = tomllib.load(f)
            os.environ["KRX_ID"] = s.get("KRX_ID", "")
            os.environ["KRX_PW"] = s.get("KRX_PW", "")
        except Exception as e:
            log.warning(f"secrets.toml 로드 실패: {e}")


# ── 가격 조회 ──────────────────────────────────────────────────────────────────
def _naver_price(ticker: str) -> int | None:
    try:
        url  = f"https://m.stock.naver.com/api/stock/{ticker}/basic"
        resp = requests.get(url, timeout=5,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        data  = resp.json()
        close = data.get("closePrice", "")
        price = int(str(close).replace(",", "")) if close else None
        return price if price and price > 0 else None
    except Exception:
        return None


def _get_price(ticker: str) -> int | None:
    """KIS API 설정 시 실시간 호가, 미설정 시 네이버 가격 사용."""
    if _kis_ok():
        result = _kis_price(ticker)
        if result and result["price"] > 0:
            return result["price"]
    return _naver_price(ticker)


def _pykrx_ohlcv(ticker: str, months: int = 6) -> pd.DataFrame:
    end   = datetime.today()
    start = end - timedelta(days=months * 31)
    try:
        df = stock.get_market_ohlcv_by_date(
            start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker
        )
        df.index = pd.to_datetime(df.index)
        if len(df.columns) >= 5:
            df = df.iloc[:, :6]
            df.columns = ["시가", "고가", "저가", "종가", "거래량", "등락률"][:len(df.columns)]
        return df
    except Exception:
        return pd.DataFrame()


def _last_trading_day() -> str:
    d = datetime.today()
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def _market_trend_ok() -> bool:
    """코스피가 MA20 위에 있으면 True (매수 우호적 시장). 데이터 오류 시 True 반환."""
    try:
        start = (datetime.today() - timedelta(days=60)).strftime("%Y%m%d")
        end   = _last_trading_day()
        ki    = stock.get_index_ohlcv_by_date(start, end, "1001")
        if ki.empty or len(ki) < 20:
            return True
        ma20  = ki["종가"].rolling(20).mean().iloc[-1]
        close = ki["종가"].iloc[-1]
        return close > ma20 * 0.97  # 3% 버퍼: 소폭 아래도 허용
    except Exception:
        return True


def _watchlist_days_from_atr(df: pd.DataFrame) -> int:
    """ATR 변동성에 따라 감시 기간을 동적 결정."""
    try:
        atr_pct = float(df.iloc[-1].get("ATR_pct", 2.0) or 2.0)
        if atr_pct >= 4.0:
            return 3   # 고변동: 신호 빠르게 무효화
        elif atr_pct >= 2.5:
            return 5   # 중변동
        else:
            return 10  # 저변동: 안정적 종목은 더 기다림
    except Exception:
        return 7


def _calc_targets(df: pd.DataFrame, score: int) -> dict:
    sp = _get_style()
    return _sig_calc_targets(
        df, score,
        atr_stop=sp["atr_stop"],
        atr_t1=sp["atr_t1"],
        atr_t2_base=sp["atr_t2_base"],
    )


def _dir_arrow(v: float) -> str:
    """상승=🔴▲, 하락=🔵▼ (한국 주식 시장 관례)"""
    if v > 0:
        return "🔴▲"
    if v < 0:
        return "🔵▼"
    return "－"


def _get_mdd(current_total: float) -> tuple:
    """과거 일지에서 최고 자산(HWM) 추적 후 현재 MDD 반환."""
    entries = load_journal()
    hwm = max((e.get("total_assets", 0) for e in entries), default=0)
    hwm = max(hwm, current_total)
    mdd_pct = (current_total - hwm) / hwm * 100 if hwm > 0 else 0.0
    return hwm, round(mdd_pct, 2)


# ── Step 1: 자동 매도 ─────────────────────────────────────────────────────────
def step_sell() -> list:
    trades    = load_trades()
    executed  = []

    for pos in trades["positions"][:]:
        target1 = pos.get("auto_target1", 0)
        stop    = pos.get("auto_stop",    0)
        if not target1 and not stop:
            continue  # 수동 포지션은 자동 매도 안 함

        price = _get_price(pos["ticker"])
        if not price:
            time.sleep(CONFIG["delay"])
            continue

        sell_reasons = None
        if target1 and price >= target1:
            sell_reasons = [
                f"자동 매도: 목표가1(₩{target1:,}) 도달 — 수익 실현",
                f"매수 시그널: {pos.get('buy_signal','')} (점수 {pos.get('buy_score',0):+d})",
            ]
        elif stop and price <= stop:
            sell_reasons = [
                f"자동 매도: 손절가(₩{stop:,}) 도달 — 손실 최소화",
                f"매수 시그널: {pos.get('buy_signal','')} (점수 {pos.get('buy_score',0):+d})",
            ]

        if sell_reasons:
            try:
                # KIS API 실제 주문 (설정된 경우)
                if _kis_ok():
                    try:
                        _kis_sell(pos["ticker"], pos["quantity"], price)
                        log.info(f"KIS 매도 주문: {pos['name']} {pos['quantity']}주 @₩{price:,}")
                    except Exception as e:
                        log.warning(f"KIS 매도 주문 실패 {pos['name']}: {e}")

                record = sell_stock(pos["id"], price, sell_reasons, "자동매도")
                executed.append({
                    "name":    pos["name"],
                    "price":   price,
                    "pnl":     record["pnl"],
                    "pnl_pct": record["pnl_pct"],
                    "reason":  sell_reasons[0],
                    "result":  record["result"],
                })
                log.info(f"자동 매도: {pos['name']} @₩{price:,}  {record['pnl_pct']:+.2f}%  {record['result']}")
            except Exception as e:
                log.warning(f"매도 실패 {pos['name']}: {e}")

        time.sleep(CONFIG["delay"])

    return executed


# ── Step 2: 감시 목록 → 자동 매수 ────────────────────────────────────────────
def step_buy() -> list:
    clean_expired_watchlist()
    wl      = load_watchlist()
    trades  = load_trades()
    held    = {p["ticker"] for p in trades["positions"]}
    executed = []

    sp = _get_style()
    if len(trades["positions"]) >= CONFIG["max_positions"]:
        log.info(f"최대 보유 종목 수 도달 ({CONFIG['max_positions']}개), 매수 건너뜀")
        return []

    for w in wl:
        if w["ticker"] in held:
            continue

        price = _get_price(w["ticker"])
        if not price:
            time.sleep(CONFIG["delay"])
            continue

        buy_target = w["buy_price"]
        tolerance  = buy_target * (1 + CONFIG["buy_tolerance"])

        if price <= tolerance:
            trades     = load_trades()  # reload
            total_val  = trades["capital"] + sum(
                p.get("buy_price", 0) * p.get("quantity", 0)
                for p in trades["positions"]
            )
            max_invest = total_val * sp["max_pos_pct"]
            quantity   = max(1, int(max_invest / price))

            try:
                # KIS API 실제 주문 (설정된 경우)
                if _kis_ok():
                    try:
                        _kis_buy(w["ticker"], quantity, price)
                        log.info(f"KIS 매수 주문: {w['name']} {quantity}주 @₩{price:,}")
                    except Exception as e:
                        log.warning(f"KIS 매수 주문 실패 {w['name']}: {e}")

                buy_stock(
                    ticker=w["ticker"], name=w["name"],
                    quantity=quantity, price=price,
                    signal=w["signal"], score=w["score"],
                    reasons=w["reasons"],
                    note=f"자동매수 | 목표가1: ₩{w['target1']:,} | 손절가: ₩{w['stop']:,}",
                    auto_target1=w["target1"],
                    auto_target2=w["target2"],
                    auto_stop=w["stop"],
                )
                remove_from_watchlist(w["ticker"])
                held.add(w["ticker"])
                executed.append({
                    "name": w["name"], "price": price, "qty": quantity,
                    "signal": w["signal"], "score": w["score"],
                })
                log.info(f"자동 매수: {w['name']} {quantity}주 @₩{price:,}  {w['signal']} {w['score']:+d}점")
            except ValueError as e:
                log.warning(f"매수 실패 {w['name']}: {e}")

        time.sleep(CONFIG["delay"])

    return executed


# ── Step 3: 종목 스캔 → 감시 목록 갱신 ──────────────────────────────────────
def step_scan() -> list:
    weights   = load_weights()
    trades    = load_trades()
    held      = {p["ticker"] for p in trades["positions"]}
    date      = _last_trading_day()
    new_items = []
    wl_set    = {w["ticker"] for w in load_watchlist()}

    sp = _get_style()
    min_score = sp["min_buy_score"]

    # 시장 추세 필터
    market_ok = _market_trend_ok()
    if not market_ok:
        log.info("코스피 하락 추세 감지 — 최소 점수 +2 상향 적용")
    effective_min_score = min_score + (2 if not market_ok else 0)

    # 시장별 최소 시총 기준 (원)
    _MIN_CAP = {"KOSPI": 300_000_000_000, "KOSDAQ": 100_000_000_000}
    _MIN_TRADE_VAL = 3_000_000_000  # 거래대금 30억 이상

    def _get_market_df(scan_date: str, mkt: str):
        df = stock.get_market_ohlcv_by_ticker(scan_date, market=mkt)
        if df.empty:
            return df
        cols = list(df.columns)
        if len(cols) >= 8:
            df.columns = ["시가","고가","저가","종가","거래량","거래대금","등락률","시가총액"]
        elif len(cols) >= 7:
            df.columns = ["시가","고가","저가","종가","거래량","거래대금","등락률"]
        return df

    for mkt in CONFIG["markets"]:
        try:
            df_today = _get_market_df(date, mkt)

            # 장 시작 전이라 거래량=0인 경우 전일 데이터 사용
            if df_today.empty or ("거래량" in df_today.columns and df_today["거래량"].sum() == 0):
                prev_date = _last_trading_day()
                d_prev = datetime.strptime(prev_date, "%Y%m%d") - timedelta(days=1)
                while d_prev.weekday() >= 5:
                    d_prev -= timedelta(days=1)
                df_today = _get_market_df(d_prev.strftime("%Y%m%d"), mkt)
                log.info(f"{mkt} 오늘 데이터 없음 → 전일({d_prev.strftime('%Y-%m-%d')}) 데이터 사용")

            if df_today.empty:
                continue

            # 거래정지 제외 (거래량 0)
            df_today = df_today[df_today["거래량"] > 0]

            # 거래대금 필터 (30억 이상)
            if "거래대금" in df_today.columns:
                df_today = df_today[df_today["거래대금"] >= _MIN_TRADE_VAL]

            # 시가총액 필터
            if "시가총액" in df_today.columns:
                min_cap = _MIN_CAP.get(mkt, 100_000_000_000)
                df_today = df_today[df_today["시가총액"] >= min_cap]
                top = df_today.nlargest(CONFIG["scan_count"], "시가총액")
            else:
                top = df_today.head(CONFIG["scan_count"])

            log.info(f"{mkt} 필터 후 스캔 대상: {len(top)}개")
        except Exception as e:
            log.warning(f"{mkt} 목록 조회 실패: {e}")
            continue

        for ticker in top.index:
            if ticker in held:
                continue

            try:
                df = _pykrx_ohlcv(ticker)
                if df.empty or len(df) < 30:
                    time.sleep(CONFIG["delay"])
                    continue

                df = add_indicators(df)
                signal, score, reasons = generate_signal(df, weights)

                if score < effective_min_score:
                    time.sleep(CONFIG["delay"])
                    continue

                targets = _calc_targets(df, score)
                name    = stock.get_market_ticker_name(ticker)
                days    = _watchlist_days_from_atr(df)

                add_to_watchlist(
                    ticker=ticker, name=name,
                    buy_price=targets["buy_price"],
                    target1=targets["target1"],
                    target2=targets["target2"],
                    stop=targets["stop"],
                    signal=signal, score=score, reasons=reasons,
                    days=days,
                )
                wl_set.add(ticker)
                new_items.append({"name": name, "signal": signal, "score": score,
                                  "buy_price": targets["buy_price"], "days": days})
                log.info(
                    f"감시 추가: {name} ({ticker})  {signal} {score:+d}점  "
                    f"매수가 ₩{targets['buy_price']:,}  ATR ₩{targets['atr']:,}  감시 {days}일"
                )
            except Exception as e:
                log.warning(f"스캔 오류 {ticker}: {e}")

            time.sleep(CONFIG["delay"])

    return new_items


# ── Step 4: AI 매매 일기 생성 ─────────────────────────────────────────────────
def step_journal(new_items: list, executed_buys: list, executed_sells: list):
    today = datetime.now().strftime("%Y-%m-%d")
    date  = _last_trading_day()

    # ── 시장 데이터 수집 ──────────────────────────────────────────────────────
    try:
        ki = stock.get_index_ohlcv_by_date(date, date, "1001")
        qi = stock.get_index_ohlcv_by_date(date, date, "2001")
        kp = float(ki["종가"].iloc[-1])  if not ki.empty else 0
        kc = float(ki["등락률"].iloc[-1]) if not ki.empty else 0
        qp = float(qi["종가"].iloc[-1])  if not qi.empty else 0
        qc = float(qi["등락률"].iloc[-1]) if not qi.empty else 0
        market_note = f"코스피 {kp:,.2f}p ({kc:+.2f}%) · 코스닥 {qp:,.2f}p ({qc:+.2f}%)"
    except Exception:
        kp = kc = qp = qc = 0
        market_note = "시장 데이터 조회 실패"

    # ── 시장 분위기 서술 ──────────────────────────────────────────────────────
    if kc > 2.0:
        mkt_mood = "매우 강한 상승장"
        mkt_desc = (f"오늘 코스피가 {kc:+.2f}% 급등하며 강한 상승 흐름을 보였다. "
                    f"전반적인 매수 심리가 살아 있어 기술적 신호의 신뢰도가 높은 날이었다. "
                    f"이런 날은 추세 추종 전략이 유효하다.")
    elif kc > 0.5:
        mkt_mood = "완만한 상승장"
        mkt_desc = (f"코스피가 {kc:+.2f}% 상승하며 무난한 하루를 보냈다. "
                    f"시장 전체보다는 개별 종목의 신호가 중요한 날이었으며, "
                    f"섹터별 차별화가 나타나는 흐름이었다.")
    elif kc > -0.3:
        mkt_mood = "보합 흐름"
        mkt_desc = (f"코스피가 {kc:+.2f}%로 뚜렷한 방향성 없이 보합권에서 마감했다. "
                    f"관망하는 투자자가 많았고, 매수보다는 신중한 접근이 유리한 날이었다. "
                    f"신호가 확실한 종목 위주로만 대응했다.")
    elif kc > -1.5:
        mkt_mood = "약세 흐름"
        mkt_desc = (f"코스피가 {kc:+.2f}% 하락하며 약세를 보였다. "
                    f"외부 변수나 기관 매도 압력이 시장 전반에 부담을 주는 흐름이었다. "
                    f"손절 기준을 엄격히 지키는 것이 중요한 날이었다.")
    else:
        mkt_mood = "급락장"
        mkt_desc = (f"코스피가 {kc:+.2f}% 급락하는 어려운 장이었다. "
                    f"리스크 관리를 최우선으로 하여 신규 매수를 자제하고 "
                    f"기존 포지션의 손절가 도달 여부를 집중 점검했다.")

    # ── 포트폴리오 현황 ───────────────────────────────────────────────────────
    trades   = load_trades()
    cash     = trades["capital"]
    pos_list = trades["positions"]
    pos_n    = len(pos_list)
    invested = sum(p.get("buy_price", 0) * p.get("quantity", 0) for p in pos_list)
    total    = cash + invested

    # ── 일기 본문 작성 ────────────────────────────────────────────────────────
    lines = [
        f"## 📓 {today} 매매 일기",
        f"",
        f"### 📊 오늘의 시장 — {mkt_mood}",
        f"",
        mkt_desc,
        f"",
        f"> **코스피** {_dir_arrow(kc)}{kp:,.2f}p ({kc:+.2f}%)  ·  **코스닥** {_dir_arrow(qc)}{qp:,.2f}p ({qc:+.2f}%)",
        f"",
        f"---",
    ]

    # ── 매수 일기 ─────────────────────────────────────────────────────────────
    if executed_buys:
        lines += [f"", f"### 🛒 오늘의 매수 ({len(executed_buys)}건)", f""]
        for b in executed_buys:
            reasons_text = b.get("reasons", [])
            pos_data = next((p for p in pos_list if p["name"] == b["name"]), {})
            t1 = pos_data.get("auto_target1", 0)
            stop = pos_data.get("auto_stop", 0)

            lines.append(f"#### {b['name']} — {b['signal']} ({b['score']:+d}점)")
            lines.append(f"")
            lines.append(f"**매수가** ₩{b['price']:,}  |  **수량** {b['qty']}주  |  "
                         f"**투자금액** ₩{b['price'] * b['qty']:,.0f}")
            lines.append(f"")
            lines.append(f"**매수 근거:**")
            for r in reasons_text:
                icon = "🔴" if "+" in r else "🔵" if "-" in r else "⚪"
                lines.append(f"- {icon} {r}")
            lines.append(f"")

            # 매수 이유 서술
            pos_signals = [r for r in reasons_text if "+" in r]
            neg_signals = [r for r in reasons_text if "-" in r]
            narrative = f"{b['name']}은 기술적 신호 {b['score']:+d}점으로 매수 기준을 충족했다. "
            if pos_signals:
                narrative += f"특히 {'와 '.join([s.split('—')[0].strip() for s in pos_signals[:2]])} 신호가 동시에 발생하며 "
                narrative += f"상승 모멘텀이 확인됐다. "
            if neg_signals:
                narrative += f"다만 {neg_signals[0].split('—')[0].strip()} 부분은 리스크 요소로 인식하고 손절가를 엄격히 설정했다. "
            if t1 and stop:
                reward_pct = (t1 - b['price']) / b['price'] * 100
                risk_pct   = (b['price'] - stop) / b['price'] * 100
                narrative += f"목표가 ₩{t1:,} (+{reward_pct:.1f}%), 손절가 ₩{stop:,} (-{risk_pct:.1f}%)로 손익비 1:{reward_pct/risk_pct:.1f}을 설정했다."
            lines.append(f"> {narrative}")
            lines.append(f"")
    else:
        lines += [f"", f"### 🛒 오늘의 매수", f"",
                  f"감시 목록에서 조건을 충족한 종목이 없어 매수가 이루어지지 않았다. "
                  f"{'시장 분위기가 약해 진입 기준을 높게 유지했다.' if kc < -0.3 else '매수 대기가 도달 종목이 없었다.'}",
                  f""]

    lines.append(f"---")

    # ── 매도 일기 ─────────────────────────────────────────────────────────────
    if executed_sells:
        wins   = [s for s in executed_sells if s["pnl"] > 0]
        losses = [s for s in executed_sells if s["pnl"] <= 0]
        lines += [f"", f"### 💰 오늘의 매도 ({len(executed_sells)}건 / 승률 {len(wins)}/{len(executed_sells)})", f""]

        for s in executed_sells:
            icon = "🔴▲" if s["pnl"] > 0 else "🔵▼"
            lines.append(f"#### {icon} {s['name']} — {s['pnl_pct']:+.2f}% (₩{s['pnl']:+,})")
            lines.append(f"")
            lines.append(f"**매도가** ₩{s['price']:,}  |  **사유** {s['reason']}")
            lines.append(f"")

            if s["pnl"] > 0:
                narrative = (f"{s['name']}이 목표가에 도달하여 수익 실현했다. "
                             f"{s['pnl_pct']:+.2f}%의 수익으로 마무리되었으며, "
                             f"매수 시점의 기술적 판단이 적중한 거래였다.")
            else:
                narrative = (f"{s['name']}이 손절가에 도달하여 손실을 최소화하는 매도를 진행했다. "
                             f"{s['pnl_pct']:+.2f}%의 손실이 발생했지만, "
                             f"손절 원칙을 지켜 추가 손실을 방지했다.")
            lines.append(f"> {narrative}")
            lines.append(f"")
    else:
        lines += [f"", f"### 💰 오늘의 매도", f"",
                  f"목표가 또는 손절가에 도달한 포지션이 없어 매도가 이루어지지 않았다. "
                  f"보유 종목들의 흐름을 지속 모니터링 중이다.", f""]

    lines.append(f"---")

    # ── 신규 감시 종목 일기 ───────────────────────────────────────────────────
    if new_items:
        lines += [f"", f"### 👁️ 신규 감시 종목 ({len(new_items)}개)", f"",
                  f"오늘 스캔에서 다음 종목들이 매수 기준을 충족하여 감시 목록에 등록됐다. "
                  f"현재가가 매수 대기가 이하로 내려오면 자동 매수가 진행된다.", f""]

        for n in new_items:
            wl_data = next((w for w in load_watchlist() if w["name"] == n["name"]), {})
            reasons = wl_data.get("reasons", [])
            lines.append(f"**{n['name']}** — {n['signal']} {n['score']:+d}점  "
                         f"| 매수 대기가 ₩{n['buy_price']:,}  | 감시 {n.get('days', 7)}일")
            if reasons:
                pos_r = [r for r in reasons if "+" in r]
                if pos_r:
                    lines.append(f"  → {', '.join([r.split('—')[0].strip() for r in pos_r[:3]])}")
            lines.append(f"")

    lines.append(f"---")

    # ── 포트폴리오 마감 현황 ──────────────────────────────────────────────────
    hwm, mdd_pct = _get_mdd(total)
    mdd_icon = "🔵▼" if mdd_pct < -10 else ("🟡" if mdd_pct < -5 else "🟢")
    lines += [f"", f"### 📈 포트폴리오 마감 현황", f"",
              f"| 항목 | 금액 |",
              f"|------|------|",
              f"| 보유 종목 수 | {pos_n}개 |",
              f"| 투자 금액 | ₩{invested:,.0f} |",
              f"| 예수금 | ₩{cash:,.0f} |",
              f"| 총 자산 | ₩{total:,.0f} |",
              f"| 최고 자산 (HWM) | ₩{hwm:,.0f} |",
              f"| 최대 낙폭 (MDD) | {mdd_icon} {mdd_pct:.2f}% |",
              f""]

    # ── 오늘의 한 줄 평 ───────────────────────────────────────────────────────
    buy_n  = len(executed_buys)
    sell_n = len(executed_sells)
    watch_n = len(new_items)

    if buy_n == 0 and sell_n == 0 and watch_n == 0:
        summary = "오늘은 조용한 하루였다. 시장을 관망하며 다음 기회를 기다렸다."
    elif sell_n > 0 and all(s["pnl"] > 0 for s in executed_sells):
        summary = f"오늘은 {sell_n}건의 매도가 모두 수익으로 마무리된 좋은 날이었다. 원칙대로 목표가에서 실현했다."
    elif sell_n > 0 and any(s["pnl"] < 0 for s in executed_sells):
        summary = f"손절이 포함된 하루였다. 아쉽지만 손절 원칙을 지킨 것이 장기적으로 올바른 선택이다."
    elif buy_n > 0:
        summary = f"{buy_n}종목을 새로 편입했다. 설정한 목표가와 손절가를 지속 모니터링할 것이다."
    else:
        summary = f"{watch_n}개 종목이 감시 목록에 추가됐다. 매수 대기가 도달 시 자동 진입 예정이다."

    lines += [f"", f"### 💬 오늘의 한 줄 평", f"", f"> {summary}", f""]

    content = "\n".join(lines)
    upsert_journal(today, content, market_note, total_assets=total)
    log.info(f"일지 생성 완료 — {today}")


# ── 메인 ──────────────────────────────────────────────────────────────────────
def run():
    log.info("=" * 60)
    log.info(f"자동 매매 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    _setup_krx()

    log.info("▶ Step 1: 자동 매도 체크")
    sold = step_sell()

    log.info("▶ Step 2: 자동 매수 체크 (감시 목록 → 체결)")
    bought = step_buy()

    log.info("▶ Step 3: 종목 스캔 → 감시 목록 갱신")
    new_items = step_scan()

    log.info("▶ Step 4: 일지 자동 생성")
    step_journal(new_items, bought, sold)

    log.info(f"완료 — 매수 {len(bought)}건, 매도 {len(sold)}건, 신규감시 {len(new_items)}개")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
