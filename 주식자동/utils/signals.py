import pandas as pd
import numpy as np


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df["종가"]
    h = df["고가"]
    l = df["저가"]

    # ── 이동평균 ────────────────────────────────────────────────────────────────
    df["MA5"]   = c.rolling(5).mean()
    df["MA20"]  = c.rolling(20).mean()
    df["MA60"]  = c.rolling(60).mean()
    df["MA120"] = c.rolling(120).mean()

    # ── 볼린저밴드 ──────────────────────────────────────────────────────────────
    df["BB_mid"]   = c.rolling(20).mean()
    std            = c.rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * std
    df["BB_lower"] = df["BB_mid"] - 2 * std
    df["BB_pct"]   = (c - df["BB_lower"]) / (df["BB_upper"] - df["BB_lower"])

    # ── RSI ────────────────────────────────────────────────────────────────────
    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["RSI"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))

    # ── MACD ───────────────────────────────────────────────────────────────────
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"]   = df["MACD"] - df["MACD_signal"]

    # ── Stochastic ──────────────────────────────────────────────────────────────
    low14  = l.rolling(14).min()
    high14 = h.rolling(14).max()
    df["Stoch_K"] = 100 * (c - low14) / (high14 - low14).replace(0, np.nan)
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean()

    # ── ATR (Average True Range) ─────────────────────────────────────────────
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    df["ATR"]     = tr.rolling(14).mean()
    df["ATR_pct"] = df["ATR"] / c * 100

    # ── ADX (Average Directional Index) ──────────────────────────────────────
    up_move   = h.diff()
    down_move = (-l.diff())
    plus_dm   = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index
    )
    minus_dm  = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index
    )
    atr14 = df["ATR"].replace(0, np.nan)
    df["Plus_DI"]  = 100 * plus_dm.rolling(14).mean()  / atr14
    df["Minus_DI"] = 100 * minus_dm.rolling(14).mean() / atr14
    dx = 100 * (df["Plus_DI"] - df["Minus_DI"]).abs() / (df["Plus_DI"] + df["Minus_DI"]).replace(0, np.nan)
    df["ADX"] = dx.rolling(14).mean()

    # ── OBV (On-Balance Volume) ──────────────────────────────────────────────
    sign      = np.sign(c.diff().fillna(0))
    df["OBV"] = (sign * df["거래량"]).cumsum()
    df["OBV_MA20"] = df["OBV"].rolling(20).mean()

    # ── 거래량 이동평균 ─────────────────────────────────────────────────────────
    df["Vol_MA20"] = df["거래량"].rolling(20).mean()

    # ── 52주 고가·저가 ──────────────────────────────────────────────────────────
    window = min(252, len(df))
    df["High52"] = h.rolling(window).max()
    df["Low52"]  = l.rolling(window).min()

    return df


def generate_signal(df: pd.DataFrame, weights: dict = None) -> tuple:
    """Returns (signal_label, score, reasons).

    weights keys: RSI, MACD, MA, BB, Stoch, Volume, ADX, Candle — float multipliers.
    """
    if df is None or len(df) < 30:
        return "데이터 부족", 0, []

    if weights is None:
        weights = {}

    def w(key: str) -> float:
        return float(weights.get(key, 1.0))

    last = df.iloc[-1]
    prev = df.iloc[-2]
    score   = 0
    reasons = []

    # ── ADX 추세 강도 ────────────────────────────────────────────────────────
    adx      = last.get("ADX",      np.nan)
    plus_di  = last.get("Plus_DI",  np.nan)
    minus_di = last.get("Minus_DI", np.nan)
    adx_w    = w("ADX")
    adx_ok   = not np.isnan(adx)

    if adx_ok:
        if adx >= 30:
            reasons.append(f"ADX {adx:.1f} — 강한 추세 (신호 신뢰도 ↑)")
        elif adx < 20:
            reasons.append(f"ADX {adx:.1f} — 횡보장 (신호 신뢰도 ↓)")

        if not any(np.isnan(v) for v in [plus_di, minus_di]):
            if plus_di > minus_di and adx >= 20:
                pts = round(1 * adx_w); score += pts
                reasons.append(f"+DI({plus_di:.1f}) > -DI({minus_di:.1f}) — 상승 추세 우위 (+{pts})")
            elif minus_di > plus_di and adx >= 20:
                pts = round(1 * adx_w); score -= pts
                reasons.append(f"-DI({minus_di:.1f}) > +DI({plus_di:.1f}) — 하락 추세 우위 (-{pts})")

    # ADX 횡보장이면 이후 신호 점수 감쇠
    adx_scale = 0.6 if (adx_ok and adx < 20) else (1.3 if (adx_ok and adx >= 30) else 1.0)

    # ── RSI ────────────────────────────────────────────────────────────────────
    rsi = last.get("RSI", np.nan)
    if not np.isnan(rsi):
        rsi_w = w("RSI") * adx_scale
        if rsi < 25:
            pts = round(3 * rsi_w); score += pts
            reasons.append(f"RSI {rsi:.1f} — 극도 과매도 (매수 +{pts})")
        elif rsi < 35:
            pts = round(2 * rsi_w); score += pts
            reasons.append(f"RSI {rsi:.1f} — 과매도 구간 (매수 +{pts})")
        elif rsi < 45:
            pts = round(1 * rsi_w); score += pts
            reasons.append(f"RSI {rsi:.1f} — 매수 관심 (+{pts})")
        elif rsi > 75:
            pts = round(3 * rsi_w); score -= pts
            reasons.append(f"RSI {rsi:.1f} — 극도 과매수 (매도 -{pts})")
        elif rsi > 65:
            pts = round(2 * rsi_w); score -= pts
            reasons.append(f"RSI {rsi:.1f} — 과매수 구간 (매도 -{pts})")
        elif rsi > 55:
            pts = round(1 * rsi_w); score -= pts
            reasons.append(f"RSI {rsi:.1f} — 매도 관심 (-{pts})")
        else:
            reasons.append(f"RSI {rsi:.1f} — 중립")

    # ── MACD ───────────────────────────────────────────────────────────────────
    macd,   sig   = last.get("MACD", np.nan), last.get("MACD_signal", np.nan)
    p_macd, p_sig = prev.get("MACD", np.nan), prev.get("MACD_signal", np.nan)
    if not any(np.isnan(v) for v in [macd, sig, p_macd, p_sig]):
        macd_w = w("MACD") * adx_scale
        if p_macd < p_sig and macd > sig:
            pts = round(3 * macd_w); score += pts
            reasons.append(f"MACD 골든크로스 — 강한 매수 (+{pts})")
        elif p_macd > p_sig and macd < sig:
            pts = round(3 * macd_w); score -= pts
            reasons.append(f"MACD 데드크로스 — 강한 매도 (-{pts})")
        elif macd > sig:
            pts = round(1 * macd_w); score += pts
            reasons.append(f"MACD > 시그널 — 상승 모멘텀 (+{pts})")
        else:
            pts = round(1 * macd_w); score -= pts
            reasons.append(f"MACD < 시그널 — 하락 모멘텀 (-{pts})")

    # ── 이동평균 ────────────────────────────────────────────────────────────────
    close  = last["종가"]
    ma5    = last.get("MA5",   np.nan)
    ma20   = last.get("MA20",  np.nan)
    ma60   = last.get("MA60",  np.nan)
    p_ma5  = prev.get("MA5",   np.nan)
    p_ma20 = prev.get("MA20",  np.nan)
    ma_w   = w("MA")

    if not np.isnan(ma20):
        if close > ma20:
            pts = round(1 * ma_w); score += pts
            reasons.append(f"종가 > MA20 — 단기 상승추세 (+{pts})")
        else:
            pts = round(1 * ma_w); score -= pts
            reasons.append(f"종가 < MA20 — 단기 하락추세 (-{pts})")

    if not np.isnan(ma60):
        if close > ma60:
            pts = round(1 * ma_w); score += pts
            reasons.append(f"종가 > MA60 — 중기 상승추세 (+{pts})")
        else:
            pts = round(1 * ma_w); score -= pts
            reasons.append(f"종가 < MA60 — 중기 하락추세 (-{pts})")

    if not any(np.isnan(v) for v in [ma5, p_ma5, ma20, p_ma20]):
        if p_ma5 < p_ma20 and ma5 > ma20:
            pts = round(2 * ma_w); score += pts
            reasons.append(f"MA5 골든크로스 — 단기 반전 (+{pts})")
        elif p_ma5 > p_ma20 and ma5 < ma20:
            pts = round(2 * ma_w); score -= pts
            reasons.append(f"MA5 데드크로스 — 단기 하락 (-{pts})")

    # 정배열 / 역배열
    if not any(np.isnan(v) for v in [ma5, ma20, ma60]):
        if ma5 > ma20 > ma60:
            pts = round(2 * ma_w); score += pts
            reasons.append(f"정배열 (MA5>MA20>MA60) — 강한 상승 구도 (+{pts})")
        elif ma5 < ma20 < ma60:
            pts = round(2 * ma_w); score -= pts
            reasons.append(f"역배열 (MA5<MA20<MA60) — 강한 하락 구도 (-{pts})")

    # ── 볼린저밴드 ──────────────────────────────────────────────────────────────
    bb_u = last.get("BB_upper", np.nan)
    bb_l = last.get("BB_lower", np.nan)
    bb_w = w("BB")
    if not any(np.isnan(v) for v in [bb_u, bb_l]):
        if close < bb_l:
            pts = round(2 * bb_w); score += pts
            reasons.append(f"볼린저밴드 하단 이탈 — 반등 가능 (+{pts})")
        elif close > bb_u:
            pts = round(2 * bb_w); score -= pts
            reasons.append(f"볼린저밴드 상단 이탈 — 조정 가능 (-{pts})")

    # ── Stochastic ──────────────────────────────────────────────────────────────
    stk   = last.get("Stoch_K", np.nan)
    std_d = last.get("Stoch_D", np.nan)
    st_w  = w("Stoch")
    if not any(np.isnan(v) for v in [stk, std_d]):
        if stk < 20 and stk > std_d:
            pts = round(1 * st_w); score += pts
            reasons.append(f"스토캐스틱 {stk:.0f} — 과매도 반등 (+{pts})")
        elif stk > 80 and stk < std_d:
            pts = round(1 * st_w); score -= pts
            reasons.append(f"스토캐스틱 {stk:.0f} — 과매수 하락 (-{pts})")

    # ── 거래량 ──────────────────────────────────────────────────────────────────
    vol    = last["거래량"]
    vol_ma = last.get("Vol_MA20", np.nan)
    vol_w  = w("Volume")
    if not np.isnan(vol_ma) and vol_ma > 0 and vol > vol_ma * 2:
        if close > prev["종가"]:
            pts = round(1 * vol_w); score += pts
            reasons.append(f"거래량 급증 + 상승 — 강한 매수세 (+{pts})")
        else:
            pts = round(1 * vol_w); score -= pts
            reasons.append(f"거래량 급증 + 하락 — 강한 매도세 (-{pts})")

    # ── OBV (세력 매집/분산) ────────────────────────────────────────────────────
    obv    = last.get("OBV", np.nan)
    obv_ma = last.get("OBV_MA20", np.nan)
    if not (pd.isna(obv) or pd.isna(obv_ma)):
        obv_pts = round(1 * vol_w)
        if obv > obv_ma:
            score += obv_pts
            reasons.append(f"OBV > 기준선 — 매집(세력 유입) 신호 (+{obv_pts})")
        else:
            score -= obv_pts
            reasons.append(f"OBV < 기준선 — 분산(세력 유출) 신호 (-{obv_pts})")

    # ── 캔들 패턴 ───────────────────────────────────────────────────────────────
    open_p = last.get("시가", np.nan)
    high_p = last.get("고가", np.nan)
    low_p  = last.get("저가", np.nan)
    candle_w = w("Candle")
    if not any(np.isnan(v) for v in [open_p, high_p, low_p]):
        body        = abs(close - open_p)
        total_range = high_p - low_p
        if total_range > 0:
            lower_wick = min(close, open_p) - low_p
            upper_wick = high_p - max(close, open_p)
            # 망치형: 아래 꼬리가 몸통의 2배 이상, 위 꼬리 거의 없음, 양봉
            if lower_wick >= body * 2 and upper_wick <= body * 0.5 and close >= open_p:
                pts = round(2 * candle_w); score += pts
                reasons.append(f"망치형 캔들 — 하락→반등 전환 신호 (+{pts})")

            # 상승 장악형
            prev_open  = prev.get("시가", np.nan)
            prev_close = prev.get("종가", np.nan)
            if not any(np.isnan(v) for v in [prev_open, prev_close]):
                if (prev_close < prev_open and close > open_p
                        and close > prev_open and open_p < prev_close):
                    pts = round(2 * candle_w); score += pts
                    reasons.append(f"상승 장악형 캔들 — 강한 반전 신호 (+{pts})")

    # ── 52주 저점/고점 근접 ─────────────────────────────────────────────────────
    low52  = last.get("Low52",  np.nan)
    high52 = last.get("High52", np.nan)
    if not any(np.isnan(v) for v in [low52, high52]) and high52 > low52:
        pos_pct = (close - low52) / (high52 - low52) * 100
        if pos_pct <= 15:
            pts = 2; score += pts
            reasons.append(f"52주 저점 근접 ({pos_pct:.0f}%) — 바닥권 매수 기회 (+{pts})")
        elif pos_pct >= 85:
            pts = 1; score -= pts
            reasons.append(f"52주 고점 근접 ({pos_pct:.0f}%) — 고점권 주의 (-{pts})")

    # ── 시그널 레이블 ──────────────────────────────────────────────────────────
    if   score >= 9:  signal = "강력 매수"
    elif score >= 5:  signal = "매수"
    elif score >= 0:  signal = "중립/관망"
    elif score >= -5: signal = "매도"
    else:             signal = "강력 매도"

    return signal, score, reasons


SIGNAL_COLOR = {
    "강력 매수": "#00c853",
    "매수":      "#69f0ae",
    "중립/관망": "#ffeb3b",
    "매도":      "#ff6d00",
    "강력 매도": "#d50000",
    "데이터 부족": "#9e9e9e",
}

# ── 지표 상세 설명 ─────────────────────────────────────────────────────────────

INDICATOR_INFO = {
    "RSI": {
        "name": "RSI (상대강도지수, Relative Strength Index)",
        "desc": (
            "최근 14일간 주가가 오른 날과 내린 날의 평균 폭을 비교해 0~100 사이 숫자로 나타낸 지표입니다. "
            "주가가 얼마나 과열(너무 많이 오름)되었거나 침체(너무 많이 내림)되었는지 보여줍니다."
        ),
        "guide": [
            "70 이상 → 과매수: 단기간 너무 많이 올랐으므로 조정(하락) 가능성",
            "30 이하 → 과매도: 단기간 너무 많이 내렸으므로 반등(상승) 가능성",
            "50 기준선 위 → 상승 추세, 아래 → 하락 추세",
        ],
    },
    "MACD": {
        "name": "MACD (이동평균 수렴·발산, Moving Average Convergence Divergence)",
        "desc": (
            "단기(12일)와 장기(26일) 지수이동평균의 차이값입니다. "
            "이 값이 신호선(9일 평균)과 교차할 때 추세 전환 신호로 활용합니다."
        ),
        "guide": [
            "골든크로스: MACD가 신호선을 아래→위 돌파 → 강한 매수 신호",
            "데드크로스: MACD가 신호선을 위→아래 돌파 → 강한 매도 신호",
            "MACD > 신호선 → 현재 상승 모멘텀 유지 중",
        ],
    },
    "MA": {
        "name": "이동평균선 (Moving Average) + 정배열",
        "desc": (
            "일정 기간의 종가를 평균 내어 연결한 선입니다. "
            "MA5>MA20>MA60 순서로 쌓인 '정배열'은 가장 강한 상승 구도를 의미합니다."
        ),
        "guide": [
            "종가 > MA20 → 단기 상승추세",
            "종가 > MA60 → 중기 상승추세",
            "MA5 골든크로스 (MA5가 MA20 위 돌파) → 단기 반전 신호",
            "정배열(MA5>MA20>MA60) → 가장 이상적인 강한 상승 구도 +2점",
        ],
    },
    "BB": {
        "name": "볼린저밴드 (Bollinger Bands)",
        "desc": (
            "20일 이동평균선을 기준으로 위아래에 표준편차×2 밴드를 그린 지표입니다. "
            "주가가 밴드 안에 있을 확률이 약 95%로, 밴드 이탈은 통계적 비정상 상태입니다."
        ),
        "guide": [
            "하단 밴드 이탈 → 과매도, 반등 가능성 높음",
            "상단 밴드 이탈 → 과매수, 조정 가능성 높음",
            "밴드 폭 좁아짐 → 조만간 큰 변동 예고",
        ],
    },
    "Stoch": {
        "name": "스토캐스틱 (Stochastic Oscillator)",
        "desc": (
            "최근 14일 고가·저가 범위에서 오늘 종가 위치를 0~100으로 나타냅니다. "
            "K선(현재값)과 D선(K의 3일 평균) 교차로 과매수·과매도를 판단합니다."
        ),
        "guide": [
            "20 이하에서 K>D → 과매도 반등 매수 신호",
            "80 이상에서 K<D → 과매수 하락 매도 신호",
        ],
    },
    "Volume": {
        "name": "거래량 + OBV (On-Balance Volume)",
        "desc": (
            "거래량은 하루 동안 거래된 주식 수입니다. "
            "OBV는 상승일 거래량을 더하고 하락일 거래량을 빼서 누적한 값으로 "
            "기관·외국인의 매집(사들임) 또는 분산(팔아치움)을 감지합니다."
        ),
        "guide": [
            "거래량 2배↑ + 주가 상승 → 강한 매수세",
            "OBV > 기준선(20일 평균) → 세력 매집 중 (상승 신호)",
            "OBV < 기준선 → 세력 분산 중 (하락 경고)",
        ],
    },
    "ADX": {
        "name": "ADX (평균방향지수, Average Directional Index)",
        "desc": (
            "추세의 '강도'를 0~100으로 측정하는 지표입니다. "
            "방향은 알려주지 않고 '추세가 있는지 없는지'만 알려줍니다. "
            "+DI(상승력)와 -DI(하락력) 크기를 비교해 방향성을 판단합니다."
        ),
        "guide": [
            "ADX < 20 → 횡보장: 신호 신뢰도 낮음 (점수 감쇠 적용)",
            "ADX 20~30 → 보통 추세: 신호 그대로 사용",
            "ADX > 30 → 강한 추세: 신호 신뢰도 높음 (점수 증폭)",
            "+DI > -DI → 상승 추세 우위 / -DI > +DI → 하락 추세 우위",
        ],
    },
    "Candle": {
        "name": "캔들 패턴 (Candlestick Patterns)",
        "desc": (
            "당일 시가·고가·저가·종가로 그리는 캔들 모양에서 반전 신호를 감지합니다. "
            "망치형과 상승 장악형은 하락→상승 반전의 대표 패턴입니다."
        ),
        "guide": [
            "망치형: 아래 꼬리가 몸통의 2배 이상, 양봉 → 낙폭 과대 반등 신호 +2점",
            "상승 장악형: 전날 음봉을 오늘 양봉이 완전히 감쌈 → 강한 반전 신호 +2점",
        ],
    },
    "ATR": {
        "name": "ATR (평균진폭, Average True Range)",
        "desc": (
            "최근 14일간 하루 평균 주가 변동폭을 나타냅니다. "
            "이 시스템은 ATR을 기반으로 손절가와 목표가를 동적으로 설정합니다."
        ),
        "guide": [
            "손절가 = 매수가 − ATR × 2 (변동성 큰 종목은 손절 폭도 넓어짐)",
            "목표가1 = 매수가 + ATR × 3",
            "목표가2 = 매수가 + ATR × 4~5 (강력매수 신호면 더 높게)",
            "ATR%가 클수록 고변동 종목 → 감시 기간 단축",
        ],
    },
}


def get_indicator_context(df: pd.DataFrame) -> dict:
    """각 지표의 현재값과 해석을 반환."""
    if df is None or len(df) < 2:
        return {}
    last = df.iloc[-1]
    prev = df.iloc[-2]
    ctx  = {}

    rsi = last.get("RSI", np.nan)
    if not np.isnan(rsi):
        if rsi >= 70:
            interp = f"현재 {rsi:.1f} — 과매수 구간입니다. 단기 조정 가능성이 있으니 신규 매수는 자제하세요."
        elif rsi <= 30:
            interp = f"현재 {rsi:.1f} — 과매도 구간입니다. 반등 가능성이 높아 매수 관심 구간입니다."
        elif rsi >= 60:
            interp = f"현재 {rsi:.1f} — 과매수 기준(70)에 근접 중입니다."
        elif rsi <= 40:
            interp = f"현재 {rsi:.1f} — 과매도 기준(30)에 근접 중입니다."
        else:
            interp = f"현재 {rsi:.1f} — 중립 구간입니다."
        ctx["RSI"] = interp

    macd   = last.get("MACD", np.nan)
    sig    = last.get("MACD_signal", np.nan)
    p_macd = prev.get("MACD", np.nan)
    p_sig  = prev.get("MACD_signal", np.nan)
    if not any(np.isnan(v) for v in [macd, sig, p_macd, p_sig]):
        if p_macd < p_sig and macd > sig:
            interp = "골든크로스 발생! MACD가 신호선을 위로 돌파했습니다. 강한 매수 구간입니다."
        elif p_macd > p_sig and macd < sig:
            interp = "데드크로스 발생! MACD가 신호선 아래로 떨어졌습니다. 매도 구간입니다."
        elif macd > sig:
            interp = f"MACD({macd:.2f})가 신호선({sig:.2f}) 위에 있습니다. 상승 모멘텀 유지 중."
        else:
            interp = f"MACD({macd:.2f})가 신호선({sig:.2f}) 아래에 있습니다. 하락 압력 있음."
        ctx["MACD"] = interp

    close = last["종가"]
    ma5   = last.get("MA5",  np.nan)
    ma20  = last.get("MA20", np.nan)
    ma60  = last.get("MA60", np.nan)
    p_ma5 = prev.get("MA5",  np.nan)
    p_ma20= prev.get("MA20", np.nan)
    ma_lines = []
    if not np.isnan(ma20):
        ma_lines.append(f"MA20(₩{ma20:,.0f}) {'위' if close > ma20 else '아래'}")
    if not np.isnan(ma60):
        ma_lines.append(f"MA60(₩{ma60:,.0f}) {'위' if close > ma60 else '아래'}")
    if not any(np.isnan(v) for v in [ma5, p_ma5, ma20, p_ma20]):
        if p_ma5 < p_ma20 and ma5 > ma20:
            ma_lines.append("MA5·MA20 골든크로스 발생!")
        elif p_ma5 > p_ma20 and ma5 < ma20:
            ma_lines.append("MA5·MA20 데드크로스 발생!")
    if not any(np.isnan(v) for v in [ma5, ma20, ma60]):
        align = "정배열(강한 상승 구도)" if ma5 > ma20 > ma60 else ("역배열(강한 하락 구도)" if ma5 < ma20 < ma60 else "")
        if align:
            ma_lines.append(align)
    if ma_lines:
        ctx["MA"] = f"종가(₩{close:,.0f})가 {', '.join(ma_lines)}."

    bb_u = last.get("BB_upper", np.nan)
    bb_l = last.get("BB_lower", np.nan)
    if not any(np.isnan(v) for v in [bb_u, bb_l]):
        if close > bb_u:
            ctx["BB"] = f"상단 밴드(₩{bb_u:,.0f}) 위로 이탈 — 통계적 과매수 상태입니다."
        elif close < bb_l:
            ctx["BB"] = f"하단 밴드(₩{bb_l:,.0f}) 아래로 이탈 — 통계적 과매도 상태입니다."
        else:
            bb_pct = (close - bb_l) / (bb_u - bb_l) * 100
            ctx["BB"] = f"밴드 내 위치: {bb_pct:.0f}% (0%=하단, 100%=상단)."

    stk   = last.get("Stoch_K", np.nan)
    std_d = last.get("Stoch_D", np.nan)
    if not any(np.isnan(v) for v in [stk, std_d]):
        if stk <= 20:
            ctx["Stoch"] = f"K={stk:.0f}, D={std_d:.0f} — 과매도. K가 D 위로 올라오면 반등 신호."
        elif stk >= 80:
            ctx["Stoch"] = f"K={stk:.0f}, D={std_d:.0f} — 과매수. K가 D 아래로 내려오면 하락 신호."
        else:
            ctx["Stoch"] = f"K={stk:.0f}, D={std_d:.0f} — 중립 구간."

    vol    = last.get("거래량", 0)
    vol_ma = last.get("Vol_MA20", np.nan)
    obv    = last.get("OBV", np.nan)
    obv_ma = last.get("OBV_MA20", np.nan)
    if not np.isnan(vol_ma) and vol_ma > 0:
        ratio = vol / vol_ma
        vol_str = f"거래량 {vol:,.0f}주 — 평균 대비 {ratio:.1f}배."
        if not (pd.isna(obv) or pd.isna(obv_ma)):
            obv_str = " OBV: " + ("매집(세력 유입) 중" if obv > obv_ma else "분산(세력 유출) 중")
            vol_str += obv_str
        ctx["Volume"] = vol_str

    adx      = last.get("ADX",      np.nan)
    plus_di  = last.get("Plus_DI",  np.nan)
    minus_di = last.get("Minus_DI", np.nan)
    if not np.isnan(adx):
        strength = "강한 추세" if adx >= 30 else ("보통 추세" if adx >= 20 else "횡보장")
        di_str = ""
        if not any(np.isnan(v) for v in [plus_di, minus_di]):
            di_str = f" | +DI {plus_di:.1f} vs -DI {minus_di:.1f} ({'상승' if plus_di > minus_di else '하락'} 우위)"
        ctx["ADX"] = f"ADX {adx:.1f} — {strength}{di_str}"

    atr     = last.get("ATR",     np.nan)
    atr_pct = last.get("ATR_pct", np.nan)
    if not np.isnan(atr):
        ctx["ATR"] = f"ATR ₩{atr:,.0f} (가격의 {atr_pct:.1f}%) — 하루 평균 변동폭"

    return ctx


_ROUND_TRIP_COST = 0.0021  # 매수수수료 0.015% + 매도수수료 0.015% + 증권거래세 0.18%


def calc_targets(df: pd.DataFrame, score: int,
                 atr_stop: float = 2.0, atr_t1: float = 3.0, atr_t2_base: float = 4.0) -> dict:
    """ATR 기반 매수가·목표가·손절가 계산. 투자 스타일별 multiplier 주입 가능."""
    last  = df.iloc[-1]
    close = int(last["종가"])
    atr   = float(last.get("ATR", 0) or 0)
    ma20  = float(last.get("MA20", close) or close)

    if atr < close * 0.005:
        atr = close * 0.02

    buy_price   = close if close <= ma20 * 1.02 else round(ma20 * 1.01, -1 if ma20 > 1000 else 0)
    cost_buffer = round(buy_price * _ROUND_TRIP_COST)  # 수수료·세금 실비용 반영
    stop        = buy_price - atr * atr_stop
    target1     = buy_price + atr * atr_t1 + cost_buffer
    target2     = buy_price + atr * (atr_t2_base + 1.0 if score >= 9 else atr_t2_base) + cost_buffer

    stop = max(stop, buy_price * 0.85)
    stop = min(stop, buy_price * 0.95)

    def rnd(v): return round(v, -1 if v > 1000 else 0)
    return {
        "buy_price": rnd(buy_price),
        "target1":   rnd(target1),
        "target2":   rnd(target2),
        "stop":      rnd(stop),
        "atr":       round(atr, 2),
        "risk_pct":  round((buy_price - stop) / buy_price * 100, 1),
        "reward1_pct": round((target1 - buy_price) / buy_price * 100, 1),
        "reward2_pct": round((target2 - buy_price) / buy_price * 100, 1),
    }


def generate_narrative(signal: str, score: int, reasons: list, last, df: pd.DataFrame) -> str:
    """종합 분석 요약 자연어 생성."""
    close  = float(last["종가"])
    ma5    = last.get("MA5",      np.nan)
    ma20   = last.get("MA20",     np.nan)
    ma60   = last.get("MA60",     np.nan)
    adx    = last.get("ADX",      np.nan)
    rsi    = last.get("RSI",      np.nan)
    obv    = last.get("OBV",      np.nan)
    obv_ma = last.get("OBV_MA20", np.nan)
    macd   = last.get("MACD",     np.nan)
    macd_s = last.get("MACD_signal", np.nan)

    # 추세
    if not any(np.isnan(v) for v in [ma5, ma20, ma60]):
        if ma5 > ma20 > ma60:
            trend = "단기·중기 모두 상승 추세(정배열)"
        elif ma5 < ma20 < ma60:
            trend = "단기·중기 모두 하락 추세(역배열)"
        elif close > ma20:
            trend = "단기 상승 추세(MA20 위)"
        else:
            trend = "단기 하락 추세(MA20 아래)"
    else:
        trend = "추세 파악 중"

    # 추세 강도
    if not np.isnan(adx):
        if adx >= 30:
            strength = f"추세 강도가 강합니다(ADX {adx:.0f})"
        elif adx >= 20:
            strength = f"추세 강도는 보통입니다(ADX {adx:.0f})"
        else:
            strength = f"방향성 없이 횡보 중입니다(ADX {adx:.0f} — 신호 신뢰도 낮음)"
    else:
        strength = ""

    # RSI
    if not np.isnan(rsi):
        if rsi < 30:
            rsi_str = f"RSI({rsi:.0f})가 과매도 구간으로 기술적 반등 가능성이 있습니다"
        elif rsi > 70:
            rsi_str = f"RSI({rsi:.0f})가 과매수 구간으로 단기 조정 가능성이 있습니다"
        elif rsi < 45:
            rsi_str = f"RSI({rsi:.0f})로 매수 우호 구간입니다"
        elif rsi > 55:
            rsi_str = f"RSI({rsi:.0f})로 다소 높은 편입니다"
        else:
            rsi_str = f"RSI({rsi:.0f})는 중립 구간입니다"
    else:
        rsi_str = ""

    # MACD
    if not any(np.isnan(v) for v in [macd, macd_s]):
        macd_str = "MACD가 시그널 위로 상승 모멘텀 유지 중" if macd > macd_s else "MACD가 시그널 아래로 하락 압력 중"
    else:
        macd_str = ""

    # OBV 세력
    if not (pd.isna(obv) or pd.isna(obv_ma)):
        obv_str = "세력(기관·외국인)의 **매집** 흔적이 보입니다" if obv > obv_ma else "세력의 **분산(매도)** 흔적이 보입니다"
    else:
        obv_str = ""

    # 긍정/부정 신호 분류
    pos = [r for r in reasons if "+" in r and "신뢰도" not in r and "ADX" not in r]
    neg = [r for r in reasons if "-" in r and "신뢰도" not in r and "ADX" not in r]

    # 결론
    conclusions = {
        "강력 매수": "여러 지표가 동시에 매수 신호를 보내고 있어 단기 상승 가능성이 높습니다. **손절가를 반드시 설정**하고 진입하세요.",
        "매수":      "전반적으로 매수 우위이나 일부 지표가 혼조세입니다. 분할 매수 또는 추가 확인 후 진입을 권장합니다.",
        "중립/관망": "뚜렷한 방향성이 없습니다. 신호가 명확해질 때까지 관망이 유리합니다.",
        "매도":      "매도 신호가 우세합니다. 신규 매수보다는 관망, 보유 중이라면 비중 축소를 고려하세요.",
        "강력 매도": "다수 지표가 강한 하락 신호입니다. 보유 중이라면 손절 또는 전량 매도를 검토하세요.",
    }
    conclusion = conclusions.get(signal, "")

    # 문단 조합
    p1_parts = [f"현재 **{trend}**이며"]
    if strength:
        p1_parts.append(strength)
    p1 = ", ".join(p1_parts) + "."

    p2_parts = []
    if rsi_str:
        p2_parts.append(rsi_str)
    if macd_str:
        p2_parts.append(macd_str)
    if obv_str:
        p2_parts.append(obv_str)
    p2 = ". ".join(p2_parts) + "." if p2_parts else ""

    sig_parts = []
    if pos:
        top_pos = ", ".join(r.split("—")[0].strip() for r in pos[:3])
        sig_parts.append(f"긍정 신호 {len(pos)}개({top_pos})")
    if neg:
        top_neg = ", ".join(r.split("—")[0].strip() for r in neg[:2])
        sig_parts.append(f"부정 신호 {len(neg)}개({top_neg})")
    p3 = " / ".join(sig_parts) + "." if sig_parts else ""

    result = p1
    if p2:
        result += " " + p2
    if p3:
        result += "\n\n" + p3
    if conclusion:
        result += f"\n\n**결론:** {conclusion}"

    return result
