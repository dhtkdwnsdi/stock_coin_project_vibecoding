import yfinance as yf
import pandas as pd
import google.generativeai as genai
import streamlit as st
import os

def initialize_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing in secrets.")
    genai.configure(api_key=api_key)

def get_ticker_from_name(company_name: str) -> str:
    """Use Gemini to map a company name to a Yahoo Finance ticker."""
    initialize_gemini()
    prompt = f"""
다음 주식 종목명/회사명을 Yahoo Finance에서 검색 가능한 Ticker 심볼로 정확히 변환해주세요.
예시:
'삼성전자' -> '005930.KS'
'카카오' -> '035720.KS'
'현대차' -> '005380.KS'
'SK하이닉스' -> '000660.KS'
'애플' 또는 'Apple' -> 'AAPL'
'테슬라' 또는 'Tesla' -> 'TSLA'

종목/회사명: '{company_name}'
답변은 오직 Ticker 심볼(예: 005930.KS 또는 AAPL) 문자열만 반환하세요.
"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content(prompt)
        ticker = response.text.strip().replace("'", "").replace('"', '').replace('`', '')
        # Basic validation: ensure no extra info
        if " " in ticker or "\n" in ticker:
            ticker = ticker.split()[0]
        return ticker
    except Exception as e:
        st.error(f"Ticker 조회 중 오류 발생 (Gemini API): {e}")
        return ""

def get_coin_ticker_from_name(coin_name: str) -> str:
    """Use Gemini to map a cryptocurrency name to a Yahoo Finance ticker (-USD)."""
    initialize_gemini()
    prompt = f"""
다음 가상자산/암호화폐(Cryptocurrency) 이름을 Yahoo Finance에서 검색 가능한 Ticker 심볼로 정확히 변환해주세요.
주의: 반드시 뒷부분에 '-USD'가 붙어야 합니다.
예시:
'비트코인' 또는 'Bitcoin' -> 'BTC-USD'
'이더리움' -> 'ETH-USD'
'리플' -> 'XRP-USD'
'솔라나' -> 'SOL-USD'
'아스타' 또는 'Astar' -> 'ASTR-USD'

가상자산명: '{coin_name}'
답변은 오직 Ticker 심볼(예: BTC-USD) 문자열만 반환하세요.
"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content(prompt)
        ticker = response.text.strip().replace("'", "").replace('"', '').replace('`', '')
        if " " in ticker or "\n" in ticker:
            ticker = ticker.split()[0]
        if not ticker.upper().endswith("-USD"):
            ticker += "-USD"
        return ticker.upper()
    except Exception as e:
        st.error(f"코인 Ticker 조회 중 오류 발생 (Gemini API): {e}")
        return ""

def get_commodity_ticker_from_name(commodity_name: str) -> str:
    """Use Gemini to map a commodity name to a Yahoo Finance futures ticker."""
    initialize_gemini()
    prompt = f"""
다음 원자재(Commodity) 이름을 Yahoo Finance에서 검색 가능한 최전월물 선물(Futures) Ticker 심볼로 정확히 변환해주세요.
주의: Yahoo Finance의 원자재 선물 Ticker는 보통 '=F'로 끝납니다.
예시:
'금' 또는 'Gold' -> 'GC=F'
'은' 또는 'Silver' -> 'SI=F'
'원유' 또는 'WTI', 'Crude Oil' -> 'CL=F'
'천연가스' -> 'NG=F'
'구리' 또는 'Copper' -> 'HG=F'
'밀' 또는 '밀가루', 'Wheat' -> 'ZW=F'
'대두' 또는 '콩' -> 'ZS=F'
'옥수수' -> 'ZC=F'

원자재명: '{commodity_name}'
답변은 오직 Ticker 심볼(예: GC=F) 문자열만 반환하세요.
"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content(prompt)
        ticker = response.text.strip().replace("'", "").replace('"', '').replace('`', '')
        if " " in ticker or "\n" in ticker:
            ticker = ticker.split()[0]
        return ticker.upper()
    except Exception as e:
        st.error(f"원자재 Ticker 조회 중 오류 발생 (Gemini API): {e}")
        return ""

def fetch_stock_technical_data(ticker_symbol: str) -> dict | None:
    """Fetches stock history and calculates relevant technical indicators."""
    stock = yf.Ticker(ticker_symbol)
    
    # Needs enough history to compute 120-day MA
    hist = stock.history(period="1y")
    
    if hist.empty:
        return None
        
    # Extract last 1 month (~30 calendar days) of daily closing prices and volume
    last_1m = hist.tail(30)
    month_history = {}
    for idx, row in last_1m.iterrows():
        date_str = str(idx).split()[0]
        month_history[date_str] = {
            "Close": float(row['Close']),
            "Volume": int(row['Volume'])
        }
        
    hist['MA_1'] = hist['Close'] # 당일 종가
    hist['MA_7'] = hist['Close'].rolling(window=7).mean()
    hist['MA_30'] = hist['Close'].rolling(window=30).mean()
    hist['MA_60'] = hist['Close'].rolling(window=60).mean()
    hist['MA_120'] = hist['Close'].rolling(window=120).mean()
    
    # Get the latest row containing valid calculated MA
    latest = hist.iloc[-1]
    
    # Get additional info if available
    info = {}
    try:
        info = stock.info
    except Exception:
        pass
        
    company_long_name = info.get('longName', ticker_symbol)
    currency = info.get('currency', 'USD/KRW')
    
    data = {
        "ticker": ticker_symbol,
        "name": company_long_name,
        "currency": currency,
        "current_price": float(latest['Close']),
        "volume": int(latest['Volume']),
        "MA_1": float(latest['MA_1']) if pd.notna(latest['MA_1']) else None,
        "MA_7": float(latest['MA_7']) if pd.notna(latest['MA_7']) else None,
        "MA_30": float(latest['MA_30']) if pd.notna(latest['MA_30']) else None,
        "MA_60": float(latest['MA_60']) if pd.notna(latest['MA_60']) else None,
        "MA_120": float(latest['MA_120']) if pd.notna(latest['MA_120']) else None,
        "last_updated": str(latest.name).split()[0],
        "month_history": month_history
    }
    return data
