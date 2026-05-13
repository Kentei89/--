"""
한국투자증권 OpenAPI 래퍼 (모의투자 / 실전투자 공용)
- 토큰 자동 발급·갱신 (파일 캐시)
- 현재가 조회, 매수/매도 주문, 잔고 조회
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# ── 설정 ──────────────────────────────────────────────────────────────────────

def _load_cfg() -> dict:
    """secrets.toml 또는 환경변수에서 KIS 설정 로드."""
    try:
        import streamlit as st
        cfg = dict(st.secrets.get("kis", {}))
        if cfg.get("app_key") and cfg["app_key"] != "여기에_APP_KEY_입력":
            return cfg
    except Exception:
        pass
    # streamlit 외부(auto_trader 등)에서 실행 시 secrets.toml 직접 읽기
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            tomllib = None
    if tomllib:
        p = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
        if p.exists():
            data = tomllib.loads(p.read_text(encoding="utf-8"))
            return data.get("kis", {})
    return {}


_TOKEN_CACHE = Path(__file__).parent.parent / "data" / "kis_token.json"

_MOCK_URL = "https://openapivts.koreainvestment.com:29443"
_REAL_URL = "https://openapi.koreainvestment.com:9443"


def _base_url(cfg: dict) -> str:
    return _MOCK_URL if cfg.get("mock", True) else _REAL_URL


# ── 토큰 ──────────────────────────────────────────────────────────────────────

def _load_cached_token() -> dict:
    try:
        if _TOKEN_CACHE.exists():
            return json.loads(_TOKEN_CACHE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_token(token: str, expires_at: str):
    _TOKEN_CACHE.parent.mkdir(exist_ok=True)
    _TOKEN_CACHE.write_text(
        json.dumps({"token": token, "expires_at": expires_at}, ensure_ascii=False),
        encoding="utf-8",
    )


def get_token(cfg: dict | None = None) -> str:
    """액세스 토큰 반환 (캐시 유효 시 재사용)."""
    if cfg is None:
        cfg = _load_cfg()
    cached = _load_cached_token()
    if cached.get("token") and cached.get("expires_at"):
        exp = datetime.fromisoformat(cached["expires_at"])
        if exp - datetime.now() > timedelta(minutes=10):
            return cached["token"]

    url = f"{_base_url(cfg)}/oauth2/tokenP"
    body = {
        "grant_type":    "client_credentials",
        "appkey":        cfg["app_key"],
        "appsecret":     cfg["app_secret"],
    }
    resp = requests.post(url, json=body, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    token      = data["access_token"]
    expires_at = (datetime.now() + timedelta(seconds=int(data.get("expires_in", 86400)))).isoformat()
    _save_token(token, expires_at)
    return token


def _headers(cfg: dict, tr_id: str) -> dict:
    return {
        "Content-Type":  "application/json",
        "authorization": f"Bearer {get_token(cfg)}",
        "appkey":        cfg["app_key"],
        "appsecret":     cfg["app_secret"],
        "tr_id":         tr_id,
        "custtype":      "P",
    }


# ── 현재가 조회 ───────────────────────────────────────────────────────────────

def get_price(ticker: str, cfg: dict | None = None) -> dict | None:
    """
    현재가 조회.
    반환: {"price": int, "change": int, "change_pct": float, "volume": int}
    """
    if cfg is None:
        cfg = _load_cfg()
    if not cfg.get("app_key"):
        return None
    try:
        url    = f"{_base_url(cfg)}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker}
        resp   = requests.get(url, headers=_headers(cfg, "FHKST01010100"),
                              params=params, timeout=5)
        resp.raise_for_status()
        d = resp.json().get("output", {})
        return {
            "price":      int(d.get("stck_prpr", 0)),
            "change":     int(d.get("prdy_vrss", 0)),
            "change_pct": float(d.get("prdy_ctrt", 0)),
            "volume":     int(d.get("acml_vol", 0)),
        }
    except Exception:
        return None


# ── 주문 ──────────────────────────────────────────────────────────────────────

def _order(cfg: dict, ticker: str, qty: int, price: int,
           order_type: str, buy: bool) -> dict:
    """
    공통 주문 함수.
    order_type: "00"=지정가, "01"=시장가
    """
    is_mock = cfg.get("mock", True)
    if buy:
        tr_id = "VTTC0802U" if is_mock else "TTTC0802U"
    else:
        tr_id = "VTTC0801U" if is_mock else "TTTC0801U"

    acct = cfg["account_no"].replace("-", "")
    acct_no   = acct[:8]
    acct_prod = acct[8:] if len(acct) > 8 else "01"

    body = {
        "CANO":          acct_no,
        "ACNT_PRDT_CD":  acct_prod,
        "PDNO":          ticker,
        "ORD_DVSN":      order_type,
        "ORD_QTY":       str(qty),
        "ORD_UNPR":      str(price) if order_type == "00" else "0",
    }
    url  = f"{_base_url(cfg)}/uapi/domestic-stock/v1/trading/order-cash"
    resp = requests.post(url, headers=_headers(cfg, tr_id), json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()


def buy_order(ticker: str, qty: int, price: int = 0,
              market_order: bool = False, cfg: dict | None = None) -> dict:
    """매수 주문. market_order=True 이면 시장가."""
    if cfg is None:
        cfg = _load_cfg()
    otype = "01" if market_order else "00"
    return _order(cfg, ticker, qty, price, otype, buy=True)


def sell_order(ticker: str, qty: int, price: int = 0,
               market_order: bool = False, cfg: dict | None = None) -> dict:
    """매도 주문. market_order=True 이면 시장가."""
    if cfg is None:
        cfg = _load_cfg()
    otype = "01" if market_order else "00"
    return _order(cfg, ticker, qty, price, otype, buy=False)


# ── 잔고 조회 ─────────────────────────────────────────────────────────────────

def get_balance(cfg: dict | None = None) -> dict:
    """
    잔고 조회.
    반환: {"cash": int, "positions": [{"ticker", "name", "qty", "avg_price", "current_price", "pnl", "pnl_pct"}]}
    """
    if cfg is None:
        cfg = _load_cfg()
    if not cfg.get("app_key"):
        return {"cash": 0, "positions": []}
    try:
        is_mock  = cfg.get("mock", True)
        tr_id    = "VTTC8434R" if is_mock else "TTTC8434R"
        acct     = cfg["account_no"].replace("-", "")
        acct_no  = acct[:8]
        acct_prod = acct[8:] if len(acct) > 8 else "01"

        url    = f"{_base_url(cfg)}/uapi/domestic-stock/v1/trading/inquire-balance"
        params = {
            "CANO":           acct_no,
            "ACNT_PRDT_CD":   acct_prod,
            "AFHR_FLPR_YN":   "N",
            "OFL_YN":         "",
            "INQR_DVSN":      "02",
            "UNPR_DVSN":      "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN":      "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        resp = requests.get(url, headers=_headers(cfg, tr_id),
                            params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        positions = []
        for p in data.get("output1", []):
            qty = int(p.get("hldg_qty", 0))
            if qty == 0:
                continue
            positions.append({
                "ticker":        p.get("pdno", ""),
                "name":          p.get("prdt_name", ""),
                "qty":           qty,
                "avg_price":     int(float(p.get("pchs_avg_pric", 0))),
                "current_price": int(p.get("prpr", 0)),
                "pnl":           int(p.get("evlu_pfls_amt", 0)),
                "pnl_pct":       float(p.get("evlu_pfls_rt", 0)),
            })

        output2 = data.get("output2", [{}])
        cash    = int(float((output2[0] if output2 else {}).get("dnca_tot_amt", 0)))
        return {"cash": cash, "positions": positions}
    except Exception as e:
        return {"cash": 0, "positions": [], "error": str(e)}


# ── 설정 유효성 확인 ──────────────────────────────────────────────────────────

def is_configured() -> bool:
    """secrets.toml에 KIS 키가 입력됐는지 확인."""
    cfg = _load_cfg()
    return bool(
        cfg.get("app_key")
        and cfg["app_key"] != "여기에_APP_KEY_입력"
        and cfg.get("app_secret")
        and cfg["app_secret"] != "여기에_APP_SECRET_입력"
        and cfg.get("account_no")
        and cfg["account_no"] != "여기에_계좌번호_입력"
    )
