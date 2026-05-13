import json
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TRADES_FILE    = DATA_DIR / "trades.json"
JOURNAL_FILE   = DATA_DIR / "journal.json"
STATS_FILE     = DATA_DIR / "signal_stats.json"
WEIGHTS_FILE   = DATA_DIR / "weights.json"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
TRADE_CONFIG_FILE = DATA_DIR / "trade_config.json"

DEFAULT_CAPITAL = 10_000_000

# 수수료 / 세금
_BUY_FEE  = 0.00015  # 매수 수수료 0.015%
_SELL_FEE = 0.00015  # 매도 수수료 0.015%
_SELL_TAX = 0.00180  # 증권거래세 0.18% (코스피/코스닥 동일)

DEFAULT_TRADE_CONFIG = {
    "style": "안정형",
}


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _save(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def load_trade_config() -> dict:
    saved = _load(TRADE_CONFIG_FILE, {})
    c = DEFAULT_TRADE_CONFIG.copy()
    c.update(saved)
    return c


def save_trade_config(data: dict):
    current = load_trade_config()
    current.update(data)
    _save(TRADE_CONFIG_FILE, current)


# ── Trades ─────────────────────────────────────────────────────────────────────

def load_trades() -> dict:
    return _load(TRADES_FILE, {"capital": DEFAULT_CAPITAL, "positions": [], "history": []})


def save_trades(data: dict):
    _save(TRADES_FILE, data)


def reset_trades(starting_capital: int = DEFAULT_CAPITAL):
    _save(TRADES_FILE, {"capital": starting_capital, "positions": [], "history": []})


def reset_all(starting_capital: int = DEFAULT_CAPITAL):
    """거래내역·포지션·감시목록·매매통계·가중치·일지 전부 초기화."""
    _save(TRADES_FILE,   {"capital": starting_capital, "positions": [], "history": []})
    _save(WATCHLIST_FILE, [])
    _save(STATS_FILE,    {})
    _save(WEIGHTS_FILE,  {})
    _save(JOURNAL_FILE,  [])


def buy_stock(ticker: str, name: str, quantity: int, price: float,
              signal: str, score: int, reasons: list, note: str = "",
              auto_target1: float = 0, auto_target2: float = 0,
              auto_stop: float = 0) -> dict:
    data = load_trades()
    trade_val  = price * quantity
    commission = round(trade_val * _BUY_FEE)
    cost       = trade_val + commission
    if data["capital"] < cost:
        raise ValueError(f"잔액 부족 — 필요 {cost:,.0f}원 (수수료 {commission:,}원 포함), 보유 {data['capital']:,.0f}원")

    pos = {
        "id":            datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "ticker":        ticker,
        "name":          name,
        "quantity":      quantity,
        "buy_price":     price,
        "buy_commission": commission,
        "buy_date":      datetime.now().strftime("%Y-%m-%d"),
        "buy_time":      datetime.now().strftime("%H:%M"),
        "buy_signal":    signal,
        "buy_score":     score,
        "buy_reasons":   reasons,
        "buy_note":      note,
        "auto_target1":  auto_target1,
        "auto_target2":  auto_target2,
        "auto_stop":     auto_stop,
        "is_auto":       auto_target1 > 0,
    }
    data["capital"] -= cost
    data["positions"].append(pos)
    save_trades(data)
    return pos


def sell_stock(position_id: str, sell_price: float,
               sell_reasons: list, note: str = "") -> dict:
    data = load_trades()
    pos = next((p for p in data["positions"] if p["id"] == position_id), None)
    if pos is None:
        raise ValueError("포지션 없음")

    buy_dt  = datetime.strptime(pos["buy_date"], "%Y-%m-%d")
    sell_dt = datetime.now()

    sell_val       = sell_price * pos["quantity"]
    sell_commission = round(sell_val * _SELL_FEE)
    sell_tax       = round(sell_val * _SELL_TAX)
    buy_commission = pos.get("buy_commission", 0)
    total_fee      = buy_commission + sell_commission + sell_tax

    proceeds = sell_val - sell_commission - sell_tax
    pnl      = proceeds - pos["buy_price"] * pos["quantity"] - buy_commission
    pnl_pct  = pnl / (pos["buy_price"] * pos["quantity"]) * 100

    record = {
        **pos,
        "sell_price":      sell_price,
        "sell_date":       sell_dt.strftime("%Y-%m-%d"),
        "sell_time":       sell_dt.strftime("%H:%M"),
        "sell_reasons":    sell_reasons,
        "sell_note":       note,
        "sell_commission": sell_commission,
        "sell_tax":        sell_tax,
        "total_fee":       total_fee,
        "pnl":             round(pnl),
        "pnl_pct":         round(pnl_pct, 2),
        "holding_days":    (sell_dt - buy_dt).days,
        "result":          "수익" if pnl > 0 else "손실" if pnl < 0 else "본전",
    }
    data["capital"]  += proceeds
    data["positions"] = [p for p in data["positions"] if p["id"] != position_id]
    data["history"].append(record)
    save_trades(data)
    _update_signal_stats(record)
    return record


# ── Signal Stats ───────────────────────────────────────────────────────────────

def load_signal_stats() -> dict:
    return _load(STATS_FILE, {})


def _save_signal_stats(data: dict):
    _save(STATS_FILE, data)


_KEY_MAP = [
    ("RSI_oversold",   lambda r: "rsi" in r.lower() and any(k in r for k in ["과매도", "매수 관심", "극도 과매도"])),
    ("RSI_overbought", lambda r: "rsi" in r.lower() and any(k in r for k in ["과매수", "매도 관심", "극도 과매수"])),
    ("MACD_golden",    lambda r: "골든크로스" in r and "macd" in r.lower()),
    ("MACD_dead",      lambda r: "데드크로스" in r and "macd" in r.lower()),
    ("MACD_above",     lambda r: "MACD > 시그널" in r),
    ("MA5_golden",     lambda r: "MA5 골든크로스" in r),
    ("MA20_above",     lambda r: "종가 > MA20" in r),
    ("MA60_above",     lambda r: "종가 > MA60" in r),
    ("MA_align",       lambda r: "정배열" in r),
    ("BB_lower",       lambda r: "볼린저밴드 하단" in r),
    ("Stoch_oversold", lambda r: "스토캐스틱" in r and "과매도" in r),
    ("Volume_spike",   lambda r: "거래량 급증" in r and "상승" in r),
    ("OBV_bull",       lambda r: "OBV" in r and "매집" in r),
    ("Candle_hammer",  lambda r: "망치형" in r),
    ("Candle_engulf",  lambda r: "장악형" in r),
    ("Low52",          lambda r: "52주 저점" in r),
    ("ADX_trend",      lambda r: "+DI" in r and "상승 추세" in r),
]


def _reason_to_keys(reason: str) -> list:
    return [k for k, fn in _KEY_MAP if fn(reason)]


def _update_signal_stats(record: dict):
    stats = load_signal_stats()
    win   = record["pnl"] > 0
    pct   = record["pnl_pct"]
    for reason in record.get("buy_reasons", []):
        for key in _reason_to_keys(reason):
            if key not in stats:
                stats[key] = {"win": 0, "loss": 0, "total_return": 0.0, "count": 0}
            stats[key]["win" if win else "loss"] += 1
            stats[key]["total_return"] = round(stats[key]["total_return"] + pct, 4)
            stats[key]["count"] += 1
    _save_signal_stats(stats)


# ── Weights ─────────────────────────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "RSI": 1.0, "MACD": 1.0, "MA": 1.0,
    "BB": 1.0,  "Stoch": 1.0, "Volume": 1.0,
    "ADX": 1.0, "Candle": 1.0,
}

_STAT_TO_WEIGHT = {
    "RSI":    ["RSI_oversold", "RSI_overbought"],
    "MACD":   ["MACD_golden",  "MACD_dead", "MACD_above"],
    "MA":     ["MA5_golden",   "MA20_above", "MA60_above", "MA_align"],
    "BB":     ["BB_lower"],
    "Stoch":  ["Stoch_oversold"],
    "Volume": ["Volume_spike", "OBV_bull"],
    "ADX":    ["ADX_trend"],
    "Candle": ["Candle_hammer", "Candle_engulf"],
}


def load_weights() -> dict:
    saved = _load(WEIGHTS_FILE, {})
    w = DEFAULT_WEIGHTS.copy()
    w.update(saved)
    return w


def save_weights(data: dict):
    _save(WEIGHTS_FILE, data)


def compute_weights_from_stats() -> dict:
    stats   = load_signal_stats()
    weights = DEFAULT_WEIGHTS.copy()
    for group, keys in _STAT_TO_WEIGHT.items():
        count = sum(stats.get(k, {}).get("count", 0) for k in keys)
        if count >= 5:
            wins      = sum(stats.get(k, {}).get("win", 0) for k in keys)
            total_ret = sum(stats.get(k, {}).get("total_return", 0) for k in keys)
            win_rate  = wins / count
            avg_ret   = total_ret / count
            if win_rate >= 0.6 and avg_ret > 0:
                weights[group] = min(2.0, round(1.0 + (win_rate - 0.5) * 2, 2))
            elif win_rate < 0.4:
                weights[group] = max(0.3, round(1.0 - (0.5 - win_rate) * 2, 2))
    return weights


# ── Journal ─────────────────────────────────────────────────────────────────────

def load_journal() -> list:
    return _load(JOURNAL_FILE, [])


def save_journal(entries: list):
    _save(JOURNAL_FILE, entries)


# ── Watchlist (자동매매 감시 목록) ────────────────────────────────────────────

def load_watchlist() -> list:
    return _load(WATCHLIST_FILE, [])


def save_watchlist(data: list):
    _save(WATCHLIST_FILE, data)


def add_to_watchlist(ticker: str, name: str, buy_price: float,
                     target1: float, target2: float, stop: float,
                     signal: str, score: int, reasons: list,
                     days: int = 7) -> dict:
    wl    = load_watchlist()
    wl    = [w for w in wl if w["ticker"] != ticker]
    entry = {
        "ticker":     ticker,
        "name":       name,
        "buy_price":  buy_price,
        "target1":    target1,
        "target2":    target2,
        "stop":       stop,
        "signal":     signal,
        "score":      score,
        "reasons":    reasons,
        "added_date": datetime.now().strftime("%Y-%m-%d"),
        "expires":    (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d"),
    }
    wl.append(entry)
    save_watchlist(wl)
    return entry


def remove_from_watchlist(ticker: str):
    wl = [w for w in load_watchlist() if w["ticker"] != ticker]
    save_watchlist(wl)


def clean_expired_watchlist():
    today = datetime.now().strftime("%Y-%m-%d")
    wl    = [w for w in load_watchlist() if w.get("expires", "9999") >= today]
    save_watchlist(wl)


# ── Journal ─────────────────────────────────────────────────────────────────────

def upsert_journal(date: str, content: str, market_note: str = "", total_assets: float = 0):
    entries = load_journal()
    trades_data = load_trades()
    trades_of_day = [
        t for t in trades_data["history"]
        if t.get("buy_date") == date or t.get("sell_date") == date
    ]
    entry = {
        "date":         date,
        "content":      content,
        "market_note":  market_note,
        "trades":       trades_of_day,
        "updated_at":   datetime.now().isoformat(),
        "total_assets": total_assets,
    }
    entries = [e for e in entries if e["date"] != date]
    entries.append(entry)
    entries.sort(key=lambda x: x["date"], reverse=True)
    save_journal(entries)
    return entry
