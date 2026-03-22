import streamlit as st
from datetime import datetime, timezone
import github_db
import rss_fetcher
import ai_analyzer
import stock_data
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# UI Configuration
st.set_page_config(page_title="AI Insight Newsroom", page_icon="📰", layout="wide")

# Default Data Structures
DEFAULT_FEEDS = {
    "국내주식": [],
    "미국주식": [],
    "코인": [],
    "매크로": []
}

def load_data():
    feeds = github_db.load_json("feeds.json", DEFAULT_FEEDS)
    archive = github_db.load_json("archive.json", {})
    stats = github_db.load_json("stats.json", {"visits": 0, "last_updated": ""})
    stock_archive = github_db.load_json("stock_archive.json", {})
    coin_archive = github_db.load_json("coin_archive.json", {})
    ticker_cache = github_db.load_json("ticker_cache.json", {})
    commodity_archive = github_db.load_json("commodity_archive.json", {})
    personas = github_db.load_json("personas.json", [])
    return feeds, archive, stats, stock_archive, coin_archive, ticker_cache, commodity_archive, personas

def save_ticker_cache(cache):
    github_db.save_json("ticker_cache.json", cache, "Update ticker cache")

def save_commodity_archive(com_archive):
    github_db.save_json("commodity_archive.json", com_archive, "Update commodity_archive.json via Commodity Analysis")

def save_personas(personas_data):
    github_db.save_json("personas.json", personas_data, "Update personas via Admin")

def record_api_usage(stats, category: str, detail = None):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if "api_usage" not in stats:
        stats["api_usage"] = {}
    if today_str not in stats["api_usage"]:
        stats["api_usage"][today_str] = {"메뉴별": {}, "페르소나별": {}}
        
    day_stats = stats["api_usage"][today_str]
    if category:
        day_stats["메뉴별"][category] = day_stats["메뉴별"].get(category, 0) + 1
    if detail:
        day_stats["페르소나별"][detail] = day_stats["페르소나별"].get(detail, 0) + 1
        
    save_stats(stats)

def save_feeds(feeds):
    github_db.save_json("feeds.json", feeds, "Update feeds.json via Admin")

def save_archive(archive):
    github_db.save_json("archive.json", archive, "Update archive.json via AI Run")

def save_stats(stats):
    github_db.save_json("stats.json", stats, "Update stats.json")

def save_stock_archive(stock_archive):
    github_db.save_json("stock_archive.json", stock_archive, "Update stock_archive.json via Stock Analysis")

def save_coin_archive(coin_archive):
    github_db.save_json("coin_archive.json", coin_archive, "Update coin_archive.json via Coin Analysis")

def show_adsense():
    """Renders a Google AdSense block using st.components.v1.html."""
    try:
        client_id = st.secrets.get("ADSENSE_CLIENT_ID", "")
        slot_id = st.secrets.get("ADSENSE_SLOT_ID", "")
    except Exception:
        client_id = ""
        slot_id = ""
        
    if not client_id or not slot_id:
        return # Skip rendering if credentials are not configured
        
    adsense_code = f"""
    <div style="text-align: center;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client_id}"
         crossorigin="anonymous"></script>
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="{client_id}"
         data-ad-slot="{slot_id}"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>
         (adsbygoogle = window.adsbygoogle || []).push({{}});
    </script>
    </div>
    """
    import streamlit.components.v1 as components
    components.html(adsense_code, height=250)

# -----------------
# Main App
# -----------------
def main():
    st.title("📰 AI Insight Newsroom")
    
    # Load data
    try:
        feeds, archive, stats, stock_archive, coin_archive, ticker_cache, commodity_archive, personas = load_data()
    except Exception as e:
        st.error(f"데이터 로드 실패 (GitHub 연동 및 Secrets 설정을 확인하세요): {e}")
        return
        
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("메뉴", [
        "뉴스룸 (Newsroom)", 
        "개별 종목 분석 (Stock)", 
        "개별 종목 분석 (Coin)", 
        "개별 종목 분석 (Commodity)",
        "투자 자문 (Advisory)",
        "관리자 대시보드 (Admin)"
    ])
    
    if page == "뉴스룸 (Newsroom)":
        render_newsroom(archive)
    elif page == "개별 종목 분석 (Stock)":
        render_stock_analysis(stock_archive, ticker_cache, stats)
    elif page == "개별 종목 분석 (Coin)":
        render_coin_analysis(coin_archive, ticker_cache, stats)
    elif page == "개별 종목 분석 (Commodity)":
        render_commodity_analysis(commodity_archive, ticker_cache, stats)
    elif page == "투자 자문 (Advisory)":
        render_advisory(personas, stats)
    else:
        render_admin(feeds, archive, stats, personas)
        
    if page != "관리자 대시보드 (Admin)":
        st.write("---")
        show_adsense()

def render_newsroom(archive):
    st.header("오늘의 핵심 뉴스 요약")
    
    if not archive:
        st.info("아직 생성된 리포트가 없습니다. 관리자 대시보드에서 분석을 실행해주세요.")
        return
        
    # Get available dates (sorted descending)
    dates = sorted(list(archive.keys()), reverse=True)
    
    # Sidebar Date Selection
    selected_date = st.sidebar.selectbox("과거 리포트 보기", dates)
    
    st.subheader(f"📅 {selected_date} 리포트")
    
    report_data = archive[selected_date]
    
    # Create Tabs for Categories
    categories = ["국내주식", "미국주식", "코인", "매크로"]
    tabs = st.tabs(categories)
    
    for i, cat in enumerate(categories):
        with tabs[i]:
            if cat in report_data:
                st.markdown(report_data[cat])
            else:
                st.info(f"{cat} 카테고리의 데이터가 없습니다.")

def draw_price_chart(month_history: dict, title: str):
    """Draws a combined line and bar chart using matplotlib and seaborn."""
    if not month_history:
        return
        
    # Assuming month_history is like {date_str: {'Close': price, 'Volume': volume}}
    df = pd.DataFrame.from_dict(month_history, orient='index')
    df.index.name = 'Date'
    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['Date'])
    
    import platform
    if platform.system() == 'Darwin':
        font_name = 'AppleGothic'
    elif platform.system() == 'Windows':
        font_name = 'Malgun Gothic'
    else:
        font_name = 'NanumGothic'
        
    sns.set_theme(style="whitegrid", rc={"font.family": font_name, "axes.unicode_minus": False})
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    # Line chart on ax1 (Close Price) using pure matplotlib to avoid seaborn categoricals
    ax1.plot(df['Date'], df['Close'], marker='o', color='#1f77b4', label='종가 (좌측 축)')
    ax1.set_ylabel('종가 (Price)', color='#1f77b4')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    ax1.set_title(f"[{title}] 최근 1개월 종가 및 거래량 추이", fontsize=14, fontweight='bold')
    
    # Bar chart on twin ax2 (Volume)
    ax2 = ax1.twinx()
    ax2.bar(df['Date'], df['Volume'], alpha=0.25, color='gray', label='거래량 (우측 축)')
    ax2.set_ylabel('거래량 (Volume)', color='gray')
    ax2.tick_params(axis='y', labelcolor='gray')
    
    # Add legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    
    # Format x-axis dates
    fig.autofmt_xdate(rotation=45)
    
    # Show in Streamlit
    st.pyplot(fig)

def get_stock_category(ticker: str) -> str:
    ticker_up = ticker.upper()
    if ticker_up.endswith(".KS") or ticker_up.endswith(".KQ"):
        return "한국주식"
    elif "-" in ticker_up: # e.g., BTC-USD
        return "코인"
    else:
        return "미국주식"

def create_pdf_from_md(md_text, title):
    import markdown
    from fpdf import FPDF
    import os

    html = markdown.markdown(md_text)
    pdf = FPDF()
    
    font_path_reg = 'C:/Windows/Fonts/malgun.ttf'
    font_path_bd = 'C:/Windows/Fonts/malgunbd.ttf'
    
    if os.path.exists(font_path_reg) and os.path.exists(font_path_bd):
        pdf.add_font("Malgun", style="", fname=font_path_reg)
        pdf.add_font("Malgun", style="B", fname=font_path_bd)
        pdf.set_font("Malgun", size=12)
    else:
        pdf.set_font("Helvetica", size=12)

    pdf.add_page()
    pdf.write_html(html)
    return bytes(pdf.output())

def render_stock_analysis(stock_archive, ticker_cache, stats):
    st.header("📈 개별 종목 심층 분석")
    st.write("주식 종목명이나 회사명을 입력하면, 실시간 주가 데이터와 이동평균선 등 기술적 지표를 추출하여 AI 전문가의 분석 보고서를 생성합니다.")
    
    company_name = st.text_input("종목명 입력 (예: 삼성전자, 애플, 카카오 등)").strip()
    
    if st.button("🚀 종목 분석 시작", type="primary"):
        if not company_name:
            st.warning("종목명을 입력해주세요.")
            return
            
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Initialize JSON layer
        if today_str not in stock_archive:
            stock_archive[today_str] = {}
            
        # 1. Check stock_archive.json for existing cache (by name or ticker)
        cached_entry = {}
        for key, data in stock_archive[today_str].items():
            if company_name.upper() == key.upper() or company_name.upper() == data.get("ticker", "").upper():
                cached_entry = data
                break

        if cached_entry:
            st.success(f"✅ 오늘 자로 이미 분석이 완료된 종목입니다 (GitHub JSON 활용). \n\n➡️ **분류**: {cached_entry.get('category', '알 수 없음')} | **Ticker**: {cached_entry.get('ticker', '')}")
            
            if "month_history" in cached_entry and isinstance(cached_entry["month_history"], dict):
                draw_price_chart(cached_entry["month_history"], str(cached_entry.get("name", company_name)))
                
            report_text = cached_entry.get("report", "")
            st.markdown(report_text)
            
            try:
                pdf_bytes = create_pdf_from_md(report_text, str(cached_entry.get("name", company_name)))
                st.download_button(
                    label="📄 PDF 리포트 다운로드",
                    data=pdf_bytes,
                    file_name=f"{cached_entry.get('name', company_name)}_분석리포트.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.warning(f"PDF 생성에 실패했습니다: {e}")
                
            return

        # 2. API Calls & Analysis
        with st.spinner(f"'{company_name}'의 Ticker를 찾고 주가 데이터를 수집하는 중..."):
            if company_name in ticker_cache:
                ticker = ticker_cache[company_name]
                st.toast(f"✅ 캐시에서 Ticker를 불러왔습니다: {ticker}")
            else:
                ticker = stock_data.get_ticker_from_name(company_name)
                record_api_usage(stats, "주식 분석 (Ticker검색)")
                if ticker:
                    ticker_cache[company_name] = ticker
                    save_ticker_cache(ticker_cache)
                    
            if not ticker:
                st.error("종목에 해당하는 Ticker를 찾지 못했습니다. 정확한 이름이나 영어 명칭을 사용해보세요.")
                return
                
            st.toast(f"찾은 Ticker: {ticker} | 주가 데이터 분석 중...")
            tech_data = stock_data.fetch_stock_technical_data(ticker)
            
            if not tech_data:
                st.error("주가 데이터를 가져오는 데 실패했습니다 (상장폐지되었거나 일시적 오류일 수 있습니다).")
                return
                
        with st.spinner("AI 차트 전문가가 데이터를 바탕으로 보고서를 작성 중입니다..."):
            report = ai_analyzer.generate_stock_analysis(company_name, tech_data)
            record_api_usage(stats, "주식 분석")
            
        st.success("✅ 분석 완료!")
        
        if tech_data and "month_history" in tech_data and isinstance(tech_data["month_history"], dict):
            draw_price_chart(tech_data["month_history"], str(company_name))
            
        st.markdown(report)
        
        try:
            pdf_bytes = create_pdf_from_md(report, str(company_name))
            st.download_button(
                label="📄 PDF 리포트 다운로드",
                data=pdf_bytes,
                file_name=f"{company_name}_분석리포트.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.warning(f"PDF 생성에 실패했습니다: {e}")
        
        # 3. Save to distinct stock_archive.json
        if not report.startswith("### ❌") and not report.startswith("### ⚠️"):
            category = get_stock_category(ticker)
            stock_archive[today_str][company_name] = {
                "name": company_name,
                "ticker": ticker,
                "category": category,
                "report": report,
                "month_history": tech_data.get("month_history", {})
            }
            try:
                save_stock_archive(stock_archive)
                st.toast("✅ 오늘자 리포트가 전용 stock_archive.json에 저장되었습니다.")
            except Exception as e:
                st.warning(f"데이터베이스 저장 실패 (GitHub 권한 확인 요망): {e}")

def render_coin_analysis(coin_archive, ticker_cache, stats):
    st.header("🪙 가상자산/코인 심층 분석")
    st.write("코인명(예: 비트코인, 아스타)을 입력하면, 실시간 가격 데이터와 기술적 지표를 바탕으로 웹3 크립토 전문가의 분석 보고서를 생성합니다.")
    
    coin_name = st.text_input("코인명 입력 (예: 비트코인, 이더리움, 아스타 등)").strip()
    
    if st.button("🚀 코인 분석 시작", type="primary"):
        if not coin_name:
            st.warning("코인명을 입력해주세요.")
            return
            
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Initialize JSON layer
        if today_str not in coin_archive:
            coin_archive[today_str] = {}
            
        # 1. Check coin_archive.json for cache
        cached_entry = {}
        for key, data in coin_archive[today_str].items():
            if coin_name.upper() == key.upper() or coin_name.upper() == data.get("ticker", "").upper():
                cached_entry = data
                break

        if cached_entry:
            st.success(f"✅ 오늘 자로 이미 분석이 완료된 코인입니다 (GitHub JSON 활용). \n\n➡️ **Ticker**: {cached_entry.get('ticker', '')}")
            
            if "month_history" in cached_entry and isinstance(cached_entry["month_history"], dict):
                draw_price_chart(cached_entry["month_history"], str(cached_entry.get("name", coin_name)))
                
            report_text = cached_entry.get("report", "")
            st.markdown(report_text)
            
            try:
                pdf_bytes = create_pdf_from_md(report_text, str(cached_entry.get("name", coin_name)))
                st.download_button(
                    label="📄 PDF 리포트 다운로드",
                    data=pdf_bytes,
                    file_name=f"{cached_entry.get('name', coin_name)}_분석리포트.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.warning(f"PDF 생성에 실패했습니다: {e}")
                
            return

        # 2. API Calls & Analysis
        with st.spinner(f"'{coin_name}'의 Ticker를 찾고 시세 데이터를 수집하는 중..."):
            if coin_name in ticker_cache:
                ticker = ticker_cache[coin_name]
                st.toast(f"✅ 캐시에서 코인 Ticker를 불러왔습니다: {ticker}")
            else:
                ticker = stock_data.get_coin_ticker_from_name(coin_name)
                record_api_usage(stats, "코인 분석 (Ticker검색)")
                if ticker:
                    ticker_cache[coin_name] = ticker
                    save_ticker_cache(ticker_cache)
                    
            if not ticker:
                st.error("코인에 해당하는 Ticker를 찾지 못했습니다. 정확한 이름이나 영어 명칭을 사용해보세요.")
                return
                
            st.toast(f"찾은 코인 Ticker: {ticker} | 시세 데이터 분석 중...")
            tech_data = stock_data.fetch_stock_technical_data(ticker)
            
            if not tech_data:
                st.error("시세 데이터를 가져오는 데 실패했습니다 (검색 불가하거나 일시적 오류일 수 있습니다).")
                return
                
        with st.spinner("웹3 수석 애널리스트가 온체인 지표와 매크로를 결합하여 보고서를 작성 중입니다..."):
            report = ai_analyzer.generate_coin_analysis(coin_name, tech_data)
            record_api_usage(stats, "코인 분석")
            
        st.success("✅ 분석 완료!")
        
        if tech_data and "month_history" in tech_data and isinstance(tech_data["month_history"], dict):
            draw_price_chart(tech_data["month_history"], str(coin_name))
            
        st.markdown(report)
        
        try:
            pdf_bytes = create_pdf_from_md(report, str(coin_name))
            st.download_button(
                label="📄 PDF 리포트 다운로드",
                data=pdf_bytes,
                file_name=f"{coin_name}_분석리포트.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.warning(f"PDF 생성에 실패했습니다: {e}")
        
        # 3. Save to distinct coin_archive.json
        if not report.startswith("### ❌") and not report.startswith("### ⚠️"):
            coin_archive[today_str][coin_name] = {
                "name": coin_name,
                "ticker": ticker,
                "category": "코인",
                "report": report,
                "month_history": tech_data.get("month_history", {})
            }
            try:
                save_coin_archive(coin_archive)
                st.toast("✅ 오늘자 리포트가 전용 coin_archive.json에 저장되었습니다.")
            except Exception as e:
                st.warning(f"데이터베이스 저장 실패 (GitHub 권한 확인 요망): {e}")

def render_commodity_analysis(commodity_archive, ticker_cache, stats):
    st.header("🛢️ 개별 종목 심층 분석 (원자재)")
    st.write("원자재명(예: 금, 은, 원유, 구리, 밀 등)을 입력하면, 실시간 선물 시세와 기술적 지표를 바탕으로 원자재 전문가의 분석 보고서를 생성합니다.")
    
    com_name = st.text_input("원자재명 입력 (예: 금, 원유, WTI, 구리 등)").strip()
    
    if st.button("🚀 원자재 분석 시작", type="primary"):
        if not com_name:
            st.warning("원자재명을 입력해주세요.")
            return
            
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if today_str not in commodity_archive:
            commodity_archive[today_str] = {}
            
        cached_entry = {}
        for key, data in commodity_archive[today_str].items():
            if com_name.upper() == key.upper() or com_name.upper() == data.get("ticker", "").upper():
                cached_entry = data
                break

        if cached_entry:
            st.success(f"✅ 오늘 자로 이미 분석이 완료된 원자재입니다 (GitHub JSON 활용). \n\n➡️ **Ticker**: {cached_entry.get('ticker', '')}")
            
            if "month_history" in cached_entry and isinstance(cached_entry["month_history"], dict):
                draw_price_chart(cached_entry["month_history"], str(cached_entry.get("name", com_name)))
                
            report_text = cached_entry.get("report", "")
            st.markdown(report_text)
            
            try:
                pdf_bytes = create_pdf_from_md(report_text, str(cached_entry.get("name", com_name)))
                st.download_button(
                    label="📄 PDF 리포트 다운로드",
                    data=pdf_bytes,
                    file_name=f"{cached_entry.get('name', com_name)}_분석리포트.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.warning(f"PDF 생성에 실패했습니다: {e}")
                
            return

        with st.spinner(f"'{com_name}'의 Ticker를 찾고 시세 데이터를 수집하는 중..."):
            if com_name in ticker_cache:
                ticker = ticker_cache[com_name]
                st.toast(f"✅ 캐시에서 원자재 Ticker를 불러왔습니다: {ticker}")
            else:
                ticker = stock_data.get_commodity_ticker_from_name(com_name)
                record_api_usage(stats, "원자재 분석 (Ticker검색)")
                if ticker:
                    ticker_cache[com_name] = ticker
                    save_ticker_cache(ticker_cache)
                    
            if not ticker:
                st.error("원자재에 해당하는 Ticker를 찾지 못했습니다. 정확한 이름이나 영어 명칭을 사용해보세요.")
                return
                
            st.toast(f"찾은 원자재 Ticker: {ticker} | 시세 데이터 수집 중...")
            tech_data = stock_data.fetch_stock_technical_data(ticker)
            
            if not tech_data:
                st.error("시세 데이터를 가져오는 데 실패했습니다 (검색 불가하거나 일시적 오류일 수 있습니다).")
                return
                
        with st.spinner("전문 애널리스트가 거시경제와 수급을 결합하여 보고서를 작성 중입니다..."):
            report = ai_analyzer.generate_commodity_analysis(com_name, tech_data)
            record_api_usage(stats, "원자재 분석")
            
        st.success("✅ 분석 완료!")
        
        if tech_data and "month_history" in tech_data and isinstance(tech_data["month_history"], dict):
            draw_price_chart(tech_data["month_history"], str(com_name))
            
        st.markdown(report)
        
        try:
            pdf_bytes = create_pdf_from_md(report, str(com_name))
            st.download_button(
                label="📄 PDF 리포트 다운로드",
                data=pdf_bytes,
                file_name=f"{com_name}_분석리포트.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.warning(f"PDF 생성에 실패했습니다: {e}")
        
        if not report.startswith("### ❌") and not report.startswith("### ⚠️"):
            commodity_archive[today_str][com_name] = {
                "name": com_name,
                "ticker": ticker,
                "category": "원자재",
                "report": report,
                "month_history": tech_data.get("month_history", {})
            }
            try:
                save_commodity_archive(commodity_archive)
                st.toast("✅ 오늘자 리포트가 전용 commodity_archive.json에 저장되었습니다.")
            except Exception as e:
                st.warning(f"데이터베이스 저장 실패 (GitHub 권한 확인 요망): {e}")

def render_advisory(personas, stats):
    st.header("🤝 투자 자문 (AI 페르소나)")
    
    if not personas:
        st.info("현재 등록된 투자 자문 페르소나가 없습니다. 관리자 대시보드에서 등록해주세요.")
        return
        
    if "selected_persona_id" not in st.session_state:
        st.session_state.selected_persona_id = None
        
    if st.session_state.selected_persona_id is None:
        st.write("원하시는 전문가를 선택하여 투자 자문 채팅을 시작하세요.")
        
        cols = st.columns(3)
        for idx, p in enumerate(personas):
            col = cols[idx % 3]
            with col:
                st.markdown(f"#### {p.get('name')}")
                # Render base64 image
                img_b64 = p.get('image_b64')
                if img_b64:
                    st.markdown(f'<img src="{img_b64}" width="150" style="border-radius:50%; margin-bottom:10px;">', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="width:150px; height:150px; border-radius:50%; background-color:#ddd; margin-bottom:10px; display:flex; align-items:center; justify-content:center;">No Image</div>', unsafe_allow_html=True)
                
                st.caption(p.get('traits', ''))
                if st.button("💬 자문 받기", key=f"chat_btn_{p['id']}"):
                    st.session_state.selected_persona_id = p['id']
                    st.rerun()
    else:
        # Chat Interface
        p = next((x for x in personas if x['id'] == st.session_state.selected_persona_id), None)
        if not p:
            st.session_state.selected_persona_id = None
            st.rerun()
            
        if st.button("⬅️ 전문가 목록으로 돌아가기"):
            st.session_state.selected_persona_id = None
            st.rerun()
            
        st.subheader(f"💬 {p['name']}와(과)의 투자 자문 채팅")
        st.caption(f"특징: {p['traits']}")
        
        chat_history_key = f"chat_{p['id']}"
        if chat_history_key not in st.session_state:
            st.session_state[chat_history_key] = []
            
        for msg in st.session_state[chat_history_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        user_input = st.chat_input(f"{p['name']}에게 투자와 관련된 질문을 해보세요...")
        if user_input:
            st.session_state[chat_history_key].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("분석 중...")
                
                import google.generativeai as genai
                from stock_data import initialize_gemini
                
                try:
                    initialize_gemini()
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    # Construct conversation history
                    history_text = f"System Instruction (You must exactly follow this persona):\n{p['instructions']}\n\n"
                    for m in st.session_state[chat_history_key]:
                        history_text += f"{'User' if m['role']=='user' else 'You'}: {m['content']}\n"
                        
                    response = model.generate_content(history_text)
                    reply = response.text
                    record_api_usage(stats, "투자 자문", detail=p['name'])
                    message_placeholder.markdown(reply)
                    st.session_state[chat_history_key].append({"role": "assistant", "content": reply})
                except Exception as e:
                    message_placeholder.error(f"오류가 발생했습니다: {e}")

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["ADMIN_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("관리자 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("관리자 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        st.error("비밀번호가 틀렸습니다. 다시 시도하세요.")
        return False
    else:
        return True

def render_admin(feeds, archive, stats, personas):
    if not check_password():
        return
        
    st.header("🛠️ 관리자 대시보드")
    
    tab_persona, tab_rss, tab_stats = st.tabs(["👥 페르소나 관리", "🔗 RSS 뉴스 관리", "📊 시스템 통계 및 분석"])
    
    with tab_persona:
        st.subheader("투자 자문 페르소나 전문가 관리")
        st.write("투자 자문 챗봇에서 활동할 전문가를 관리합니다. (최대 6명)")
        
        if personas:
            st.write("---")
            for i, p in enumerate(personas):
                with st.expander(f"👤 {p['name']} - {p['traits']}", expanded=False):
                    col_img, col_info, col_del = st.columns([1, 4, 1])
                    if p.get('image_b64'):
                        col_img.markdown(f'<img src="{p["image_b64"]}" width="80" style="border-radius:10%;">', unsafe_allow_html=True)
                    else:
                        col_img.write("이미지 없음")
                        
                    col_info.write(f"**지침**: {p['instructions'][:80]}...")
                    
                    if col_del.button("삭제", key=f"del_p_{p['id']}"):
                        personas[:] = [x for x in personas if x['id'] != p['id']]
                        save_personas(personas)
                        st.success("해당 페르소나가 삭제되었습니다.")
                        st.rerun()
                        
                    st.divider()
                    st.markdown("##### ✏️ 정보 수정")
                    with st.form(f"edit_form_{p['id']}", clear_on_submit=False):
                        new_name = st.text_input("이름", value=p['name'])
                        new_traits = st.text_input("특징 표시", value=p['traits'])
                        new_inst = st.text_area("AI 지침 (시스템 프롬프트)", value=p['instructions'], height=150)
                        new_img = st.file_uploader("새 이미지 업로드 (선택, PNG/JPG)", type=["png", "jpg", "jpeg"], key=f"img_edit_{p['id']}")
                        
                        if st.form_submit_button("수정 저장"):
                            if not new_name or not new_inst:
                                st.error("이름과 지침은 필수입니다.")
                            else:
                                p['name'] = new_name
                                p['traits'] = new_traits
                                p['instructions'] = new_inst
                                if new_img is not None:
                                    import base64
                                    bytes_data = new_img.getvalue()
                                    b64_str = base64.b64encode(bytes_data).decode()
                                    p['image_b64'] = f"data:{new_img.type};base64,{b64_str}"
                                
                                save_personas(personas)
                                st.success("수정이 완료되었습니다!")
                                st.rerun()

        st.divider()
        if len(personas) >= 6:
            st.info("💡 페르소나는 최대 6명까지만 등록 가능합니다. 추가하려면 위에서 기존 항목을 삭제하세요.")
        else:
            st.write("#### ➕ 새로운 페르소나 등록")
            with st.form("add_persona_form", clear_on_submit=True):
                p_name = st.text_input("이름 (예: 워렌 버핏 AI)")
                p_traits = st.text_input("특징 표시 (예: 가치투자의 대가)")
                p_inst = st.text_area("AI 지침 (시스템 프롬프트)", placeholder="투자 철학이나 답변 어조를 적어주세요.", height=150)
                p_img = st.file_uploader("전문가 프로필 이미지 (권장: 1:1 비율)", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("신규 등록하기"):
                    if not p_name or not p_inst:
                        st.error("이름과 AI 지침은 필수 항목입니다.")
                    else:
                        import uuid
                        import base64
                        
                        b64_img = ""
                        if p_img is not None:
                            bytes_data = p_img.getvalue()
                            b64_str = base64.b64encode(bytes_data).decode()
                            b64_img = f"data:{p_img.type};base64,{b64_str}"
                            
                        new_p = {
                            "id": str(uuid.uuid4()),
                            "name": p_name,
                            "traits": p_traits,
                            "instructions": p_inst,
                            "image_b64": b64_img
                        }
                        personas.append(new_p)
                        save_personas(personas)
                        st.success(f"{p_name} 전문가가 성공적으로 등재되었습니다!")
                        st.rerun()
                        
    with tab_rss:
        st.subheader("RSS 피드 주소 관리")
        categories = ["국내주식", "미국주식", "코인", "매크로"]
        selected_cat = st.selectbox("카테고리 선택", categories)
        current_feeds = feeds.get(selected_cat, [])
        
        with st.form("add_feed_form", clear_on_submit=True):
            new_url = st.text_input(f"새 {selected_cat} RSS URL 추가")
            if st.form_submit_button("추가") and new_url:
                if new_url not in current_feeds:
                    feeds[selected_cat].append(new_url)
                    save_feeds(feeds)
                    st.success("피드가 추가되었습니다.")
                    st.rerun()
                    
        st.write(f"현재 등록된 **{selected_cat}** 피드 목록:")
        for i, url in enumerate(current_feeds):
            col1, col2 = st.columns([8, 1])
            col1.code(url)
            if col2.button("삭제", key=f"del_rss_{selected_cat}_{i}"):
                feeds[selected_cat].remove(url)
                save_feeds(feeds)
                st.success("피드가 삭제되었습니다.")
                st.rerun()
                
    with tab_stats:
        st.subheader("시스템 통계 및 뉴스 분석 실행")
        st.write(f"**마지막 뉴스 수집/분석 시간**: {stats.get('last_updated', '기록 없음')}")
        
        st.write("---")
        st.write("#### 📈 최근 API 사용량 통계")
        api_usage = stats.get("api_usage", {})
        if api_usage:
            date_keys = sorted(list(api_usage.keys()), reverse=True)
            sel_date = st.selectbox("조회할 날짜", date_keys)
            
            day_data = api_usage[sel_date]
            
            col_menu, col_persona = st.columns(2)
            with col_menu:
                st.write("**메뉴별 호출 수**")
                if day_data.get("메뉴별"):
                    st.dataframe(pd.DataFrame(list(day_data["메뉴별"].items()), columns=["메뉴", "호출 횟수"]), use_container_width=True)
                else:
                    st.info("호출 기록 없음")
                    
            with col_persona:
                st.write("**페르소나별 호출 수**")
                if day_data.get("페르소나별"):
                    st.dataframe(pd.DataFrame(list(day_data["페르소나별"].items()), columns=["페르소나", "호출 횟수"]), use_container_width=True)
                else:
                    st.info("호출 기록 없음")
        else:
            st.info("아직 API 사용 기록이 없습니다.")
            
        st.write("---")
        st.write("등록된 RSS 피드들을 수집하여 Gemini AI로 카테고리별 요약 리포트를 생성합니다. (몇 분 가량 소요될 수 있습니다.)")
        
        if st.button("🚀 뉴스 수집 및 분석 일괄 시작", type="primary"):
            with st.spinner("AI가 최신 뉴스를 수집하고 분석 중입니다... 잠시만 기다려주세요."):
                today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                
                if today_str not in archive:
                    archive[today_str] = {}
                    
                for cat in ["국내주식", "미국주식", "코인", "매크로"]:
                    cat_urls = feeds.get(cat, [])
                    if not cat_urls:
                        archive[today_str][cat] = "이 카테고리에는 등록된 RSS 피드가 없습니다."
                        continue
                        
                    st.toast(f"{cat} 기사 수집 중...")
                    articles = rss_fetcher.fetch_and_filter_feeds(cat_urls, days_limit=3)
                    
                    if articles:
                        st.toast(f"{cat} 기사들을 바탕으로 AI 브리핑 작성 중...")
                        report_md = ai_analyzer.generate_report(cat, articles)
                        record_api_usage(stats, f"뉴스룸({cat})")
                        archive[today_str][cat] = report_md
                    else:
                        archive[today_str][cat] = "최근 3일간 수집된 뉴스가 없습니다."
                
                save_archive(archive)
                stats["last_updated"] = datetime.now(timezone.utc).isoformat()
                save_stats(stats)
                
                st.success("🎉 분석이 완료되었습니다! 좌측의 '뉴스룸' 메뉴에서 리포트를 확인하세요.")

if __name__ == "__main__":
    main()
