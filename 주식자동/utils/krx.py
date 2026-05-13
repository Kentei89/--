import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pykrx import stock


def setup_krx():
    os.environ["KRX_ID"] = st.secrets.get("KRX_ID", os.getenv("KRX_ID", ""))
    os.environ["KRX_PW"] = st.secrets.get("KRX_PW", os.getenv("KRX_PW", ""))


def last_trading_day(days_back=0) -> str:
    d = datetime.today() - timedelta(days=days_back)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def date_range(months=6) -> tuple[str, str]:
    end = datetime.today()
    start = end - timedelta(days=months * 31)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


@st.cache_data(ttl=3600)
def get_ohlcv(ticker: str, months: int = 12) -> pd.DataFrame:
    fromdate, todate = date_range(months)
    df = stock.get_market_ohlcv_by_date(fromdate, todate, ticker)
    df.index = pd.to_datetime(df.index)
    df.columns = ["시가", "고가", "저가", "종가", "거래량", "등락률"]
    return df


@st.cache_data(ttl=3600)
def get_investor_trading(ticker: str, months: int = 3) -> pd.DataFrame:
    fromdate, todate = date_range(months)
    df = stock.get_market_trading_volume_by_date(fromdate, todate, ticker)
    df.index = pd.to_datetime(df.index)
    return df


@st.cache_data(ttl=300)
def get_market_today(market: str = "KOSPI") -> pd.DataFrame:
    date = last_trading_day()
    df = stock.get_market_ohlcv_by_ticker(date, market=market)
    df.index.name = "종목코드"
    # pykrx 반환 컬럼: 시가, 고가, 저가, 종가, 거래량, 거래대금, 등락률, 시가총액
    df.columns = ["시가", "고가", "저가", "종가", "거래량", "거래대금", "등락률", "시가총액"]
    names = {t: stock.get_market_ticker_name(t) for t in df.index}
    df["종목명"] = df.index.map(names)
    return df


@st.cache_data(ttl=1800)
def get_ticker_list(market: str = "ALL") -> dict:
    date = last_trading_day()
    result = {}
    markets = ["KOSPI", "KOSDAQ"] if market == "ALL" else [market]
    for m in markets:
        tickers = stock.get_market_ticker_list(date, market=m)
        for t in tickers:
            try:
                name = stock.get_market_ticker_name(t)
                result[name] = (t, m)
            except Exception:
                pass
    return result


@st.cache_data(ttl=1800)
def get_investor_market_total(market: str = "KOSPI") -> pd.DataFrame:
    """시장 전체 투자자별 거래대금 (매도/매수/순매수)"""
    date = last_trading_day()
    df = stock.get_market_trading_value_by_investor(date, date, market)
    return df


@st.cache_data(ttl=3600)
def get_investor_trading_by_ticker(ticker: str, months: int = 1) -> pd.DataFrame:
    """개별 종목 투자자별 순매수 (기관/외국인/개인)"""
    fromdate, todate = date_range(months)
    df = stock.get_market_trading_volume_by_date(fromdate, todate, ticker)
    df.index = pd.to_datetime(df.index)
    return df


@st.cache_data(ttl=3600)
def get_foreign_holding(ticker: str, months: int = 3) -> pd.DataFrame:
    fromdate, todate = date_range(months)
    try:
        df = stock.get_exhaustion_rates_of_foreign_investment_by_date(fromdate, todate, ticker)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800)
def get_index_ohlcv(ticker: str = "1001", months: int = 6) -> pd.DataFrame:
    fromdate, todate = date_range(months)
    df = stock.get_index_ohlcv_by_date(fromdate, todate, ticker)
    df.index = pd.to_datetime(df.index)
    return df


def get_ticker_name(ticker: str) -> str:
    try:
        return stock.get_market_ticker_name(ticker)
    except Exception:
        return ticker


def _naver_price(ticker: str) -> dict | None:
    """네이버 금융 현재가 (약 1~2분 지연)."""
    try:
        url = f"https://m.stock.naver.com/api/stock/{ticker}/basic"
        resp = requests.get(url, timeout=5,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        close = data.get("closePrice", "")
        if not close:
            return None
        price = int(str(close).replace(",", ""))
        change_pct = float(data.get("fluctuationsRatio", 0))
        change_val = int(str(data.get("compareToPreviousClosePrice", "0")).replace(",", ""))
        return {
            "price":      price,
            "change":     change_val,
            "change_pct": change_pct,
            "name":       data.get("stockName", ticker),
            "source":     "naver",
        }
    except Exception:
        return None


@st.cache_data(ttl=60)
def get_realtime_price(ticker: str) -> dict | None:
    """실시간 현재가. KIS API 우선(실시간) → 네이버 fallback(1~2분 지연)."""
    fetched_at = datetime.now().strftime("%H:%M:%S")

    # KIS API 우선 (실시간)
    try:
        from utils.kis_api import is_configured, get_price as _kis_price
        if is_configured():
            result = _kis_price(ticker)
            if result and result["price"] > 0:
                result["source"]     = "KIS실시간"
                result["fetched_at"] = fetched_at
                return result
    except Exception:
        pass

    # 네이버 fallback
    result = _naver_price(ticker)
    if result:
        result["fetched_at"] = fetched_at
        result["source"]     = "네이버"
    return result


INDEX_MAP = {
    "코스피": "1001",
    "코스닥": "2001",
    "코스피200": "1028",
}


@st.cache_data(ttl=1800)
def get_etf_ticker_list_cached() -> dict:
    """ETF 전체 목록 {이름: 코드} 반환."""
    date = last_trading_day()
    try:
        tickers = stock.get_etf_ticker_list(date)
        result = {}
        for t in tickers:
            try:
                name = stock.get_etf_ticker_name(t)
                result[name] = t
            except Exception:
                pass
        return result
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def get_etf_ohlcv(ticker: str, months: int = 6) -> pd.DataFrame:
    """ETF OHLCV 데이터 반환 (표준 컬럼명으로 정규화)."""
    fromdate, todate = date_range(months)
    try:
        df = stock.get_etf_ohlcv_by_date(fromdate, todate, ticker)
        df.index = pd.to_datetime(df.index)
        # pykrx ETF 컬럼: 시가,고가,저가,종가,거래량,거래대금,기초지수종가
        if len(df.columns) >= 6:
            df = df.iloc[:, :6]
            df.columns = ["시가", "고가", "저가", "종가", "거래량", "거래대금"]
        return df
    except Exception:
        return pd.DataFrame()
