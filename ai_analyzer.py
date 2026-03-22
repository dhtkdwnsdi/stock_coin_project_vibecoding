import os
import google.generativeai as genai
import streamlit as st

def initialize_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing in secrets.")
    genai.configure(api_key=api_key)

def generate_report(category: str, articles: list[dict]) -> str:
    """Gemini 2.5 Flash를 사용하여 전문 투자 보고서 형식의 마크다운 리포트 생성"""
    if not articles:
        return "### ⚠️ 수집 데이터 부족\n현재 선택하신 카테고리에 대해 최근 3일간 분석할 뉴스가 존재하지 않습니다."
        
    initialize_gemini()
    
    # 분석 대상 기사 텍스트 구성
    content_list = []
    for i, a in enumerate(articles, 1):
        content_list.append(f"기사 {i}\n제목: {a['title']}\n링크: {a['link']}\n요약: {a['summary'][:300]}")
        
    articles_text = "\n\n".join(content_list)
    
    # 가독성과 전문성을 극대화한 프롬프트
    prompt = f"""
당신은 글로벌 투자은행(IB)의 시니어 전략 분석가입니다. 
아래 제공된 '{category}' 관련 뉴스들을 바탕으로 고객(투자자)에게 전달할 **'Daily Insight Report'**를 작성하세요.

---
### [보고서 작성 가이드라인]
1. **시각적 구조화**: 
   - 각 섹션은 `###` 소제목을 사용하고 섹션 사이에는 `---` (구분선)을 넣어 가독성을 높이세요.
   - 문단은 짧게 유지하고, 핵심 키워드는 **볼드체**로 강조하세요.
   - 불렛 포인트(•)와 번호(1.)를 적절히 혼용하여 나열하세요.

2. **내용 구성**:
   - **[Executive Summary]**: 오늘 시장의 전체적인 분위기를 1문장으로 요약하고, '투자 심리 지수'를 (낙관/중립/비관) 중 하나로 제시하세요.
   - **[Key Topics & Analysis]**: 뉴스들을 2~3개의 핵심 토픽으로 클러스터링하여 심층 분석하세요. 단순히 뉴스를 나열하지 말고 '왜 중요한지'와 '시장 영향'을 서술하세요.
   - **[Reference]**: 분석에 참고한 기사 제목을 해당 섹션 하단에 [제목](링크) 형식으로 출처를 밝히세요.
   - **[Investment Strategy]**: 분석을 바탕으로 투자자가 취해야 할 단기/중기 대응 전략을 제언하세요.

3. **톤앤매너**: 전문적이고 객관적이며 통찰력 있는 어조를 유지하세요.
---

[분석할 뉴스 데이터]
{articles_text}

[결과물 언어: 한국어]
"""
    
    try:
        # 모델명은 현재 사용 가능한 gemini-2.5-flash 또는 gemini-2.5-pro를 권장합니다.
        model = genai.GenerativeModel("gemini-2.5-flash") 
        response = model.generate_content(prompt)
        
        # 결과물 출력 (내용이 바로 나오도록 가공)
        return response.text
    except Exception as e:
        return f"### ❌ 리포트 생성 중 오류 발생\n전문가 리포트를 생성하는 과정에서 기술적인 문제가 발생했습니다.\n{e}"

def generate_stock_analysis(company_name: str, tech_data: dict) -> str:
    """Generates an expert stock analysis report based on technical indicators."""
    if not tech_data:
        return f"### ⚠️ 주가 데이터 오류\n'{company_name}'에 대한 주가 데이터를 가져오는 데 실패했습니다. 종목명을 확인해주세요."
        
    initialize_gemini()
    
    month_hist_list = []
    for k, v in tech_data.get('month_history', {}).items():
        if isinstance(v, dict):
            month_hist_list.append(f"{k}: 종가 {v.get('Close', 0):.2f}, 거래량 {v.get('Volume', 0)}")
        else:
            month_hist_list.append(f"{k}: 종가 {v:.2f}")
    month_hist_str = "\n".join(month_hist_list)
    
    prompt = f"""
당신은 글로벌 탑티어 투자은행(IB)의 수석 차트 전문가이자 실전 투자 전략가입니다.
아래 제공된 '{company_name}' (Ticker: {tech_data.get('ticker')})의 일일 주가 및 이동평균선 데이터를 바탕으로, 
다음 항목이 포함된 심층 종목 분석 보고서를 작성하세요.

[제공된 주가 데이터]
- 기준일: {tech_data.get('last_updated')}
- 현재가: {tech_data.get('current_price')} {tech_data.get('currency')}
- 거래량: {tech_data.get('volume')}
- 당일 종가 (1일): {tech_data.get('MA_1', 'N/A')}
- 7일 이동평균선: {tech_data.get('MA_7', 'N/A')}
- 30일 이동평균선: {tech_data.get('MA_30', 'N/A')}
- 60일 이동평균선: {tech_data.get('MA_60', 'N/A')}
- 120일 이동평균선: {tech_data.get('MA_120', 'N/A')}

[최근 1개월 일별 종가 추이]
{month_hist_str}

[보고서 작성 가이드라인]
1. **시각적 구조화**: `###` 소제목과 `---` 구분선을 사용하여 섹션을 명확히 구분하세요. 핵심 키워드와 가격은 **볼드체**로 강조하세요.
2. **내용 구성**:
   - **[Market Overview : 현재가 및 추세 스냅샷]**: 현재가와 거래량을 바탕으로 오늘의 종목 상태를 2~3줄로 조망하세요.
   - **[Technical Analysis : 이동평균선 정밀 분석]**: 제공된 1, 7, 30, 60, 120일 이평선의 배열 흐름을 해석하고 진단하세요.
   - **[Trading Insights : 1개월 가격 패턴 및 매매 타점]**: 방금 제공된 1개월 종가 흐름 데이터를 분석하여 지지선/저항선을 파악하고, 현재 시점의 단기 진입 타점 혹은 매도/관망 포지션에 대한 구체적인 '트레이딩 전략'을 반드시 포함하세요!
   - **[Macro & Sentiment : 매크로 관점 및 업황 시그널]**: 해당 기업이 속한 섹터의 글로벌 매크로 환경(금리 통화정책 등)을 분석하세요.
   - **[Investment Strategy : 기간별 전망 및 주가 시나리오]**: 단/중/장기 전망을 정리하세요.
3. **톤앤매너**: 통계와 기술적 지표를 근거로 날카롭고 전문적인 어조를 유지하세요.

결과물 언어: 한국어
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"### ❌ 종목 분석 중 오류 발생\n{e}"

def generate_coin_analysis(coin_name: str, tech_data: dict) -> str:
    """Generates an expert crypto analysis report based on technical indicators."""
    if not tech_data:
        return f"### ⚠️ 가격 데이터 오류\n'{coin_name}'에 대한 데이터를 가져오는 데 실패했습니다. 코인명을 확인해주세요."
        
    initialize_gemini()
    
    month_hist_list = []
    for k, v in tech_data.get('month_history', {}).items():
        if isinstance(v, dict):
            month_hist_list.append(f"{k}: 종가 {v.get('Close', 0):.2f}, 거래량 {v.get('Volume', 0)}")
        else:
            month_hist_list.append(f"{k}: 종가 {v:.2f}")
    month_hist_str = "\n".join(month_hist_list)
    
    prompt = f"""
당신은 글로벌 수준의 웹3/크립토 전문 수석 애널리스트이자 차트 분석가입니다.
아래 제공된 '{coin_name}' (Ticker: {tech_data.get('ticker')})의 일일 시세 및 이동평균선 데이터를 바탕으로, 
다음 항목이 포함된 심층 코인 분석 보고서를 작성하세요.

[제공된 시세 데이터]
- 기준일: {tech_data.get('last_updated')}
- 현재가: {tech_data.get('current_price')} {tech_data.get('currency')}
- 거래량: {tech_data.get('volume')}
- 당일 종가 (1일): {tech_data.get('MA_1', 'N/A')}
- 7일 이동평균선: {tech_data.get('MA_7', 'N/A')}
- 30일 이동평균선: {tech_data.get('MA_30', 'N/A')}
- 60일 이동평균선: {tech_data.get('MA_60', 'N/A')}
- 120일 이동평균선: {tech_data.get('MA_120', 'N/A')}

[최근 1개월 종가 추이]
{month_hist_str}

[보고서 작성 가이드라인]
1. **시각적 구조화**: `###` 소제목과 `---` 구분선을 사용하여 섹션을 명확히 구분하세요. 핵심 키워드와 가격은 **볼드체**로 강조하세요.
2. **내용 구성**:
   - **[Market Overview : 현재가 및 추세 스냅샷]**: 현재가와 거래량을 바탕으로 오늘의 코인 상태를 2~3줄로 조망하세요.
   - **[Technical Analysis : 이동평균선 정밀 분석]**: 이동평균선 배열 흐름을 해석하여 현재 차트의 기술적 위치를 평가하세요.
   - **[Trading Insights : 1개월 가격 패턴 및 매매 타점]**: 제공된 최근 1개월 종가 흐름을 바탕으로 지지저항 패턴을 도출하고, 아주 구체적인 단기 트레이딩 전략(매수 타점, 익절/손절가 제언 등)을 제시하세요!
   - **[Crypto & Macro : 온체인 이슈 및 매크로 시그널]**: 해당 코인의 메인넷, 웹3 동향 및 글로벌 매크로 환경(ETF, 금리 등)을 분석하세요.
   - **[Investment Strategy : 기간별 전망 및 대응 시나리오]**: 단/중/장기 전망을 정리하세요.
3. **톤앤매너**: 통계와 지표를 근거로 전문적이고 날카로운 어조를 유지하세요.

결과물 언어: 한국어
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"### ❌ 코인 분석 중 오류 발생\n{e}"

def generate_commodity_analysis(commodity_name: str, tech_data: dict) -> str:
    """Generates an expert commodity analysis report based on technical indicators."""
    if not tech_data:
        return f"### ⚠️ 가격 데이터 오류\n'{commodity_name}'에 대한 데이터를 가져오는 데 실패했습니다. 원자재명을 확인해주세요."
        
    initialize_gemini()
    
    month_hist_list = []
    for k, v in tech_data.get('month_history', {}).items():
        if isinstance(v, dict):
            month_hist_list.append(f"{k}: 종가 {v.get('Close', 0):.2f}, 거래량 {v.get('Volume', 0)}")
        else:
            month_hist_list.append(f"{k}: 종가 {v:.2f}")
    month_hist_str = "\n".join(month_hist_list)
    
    prompt = f"""
당신은 글로벌 원자재(Commodity) 시장 전문 수석 애널리스트이자 실전 트레이더입니다.
아래 제공된 '{commodity_name}' (Ticker: {tech_data.get('ticker')})의 원자재 선물 일일 시세 및 이동평균선 데이터를 바탕으로, 
다음 항목이 포함된 심층 원자재 분석 보고서를 작성하세요.

[제공된 시세 데이터]
- 기준일: {tech_data.get('last_updated')}
- 현재가: {tech_data.get('current_price')} {tech_data.get('currency')}
- 거래량: {tech_data.get('volume')}
- 당일 종가 (1일): {tech_data.get('MA_1', 'N/A')}
- 7일 이동평균선: {tech_data.get('MA_7', 'N/A')}
- 30일 이동평균선: {tech_data.get('MA_30', 'N/A')}
- 60일 이동평균선: {tech_data.get('MA_60', 'N/A')}
- 120일 이동평균선: {tech_data.get('MA_120', 'N/A')}

[최근 1개월 종가 추이]
{month_hist_str}

[보고서 작성 가이드라인]
1. **시각적 구조화**: `###` 소제목과 `---` 구분선을 사용하여 섹션을 명확히 구분하세요. 핵심 키워드와 주요 지지/저항 라인은 **볼드체**로 강조하세요.
2. **내용 구성**:
   - **[Market Overview : 원자재 현재가 스냅샷]**: 현재가와 거래량을 바탕으로 오늘의 추세를 2~3줄로 조망하세요.
   - **[Technical Analysis : 차트 및 기술적 분석]**: 이동평균선 배열과 최근 1개월 가격 지표를 해석하여 방향성을 평가하세요.
   - **[Trading Insights : 단기 매매 타점 및 전략]**: 최근 종가 흐름을 바탕으로 지지/저항 패턴을 도출하고, 구체적인 단기 포지션 진입/청산 전략을 제시하세요.
   - **[Macro & Supply-Demand : 매크로 및 수요/공급 변수]**: {commodity_name}에 영향을 미치는 주요 거시경제 지표(달러 인덱스, 금리 등)나 원자재 특유의 지정학적 이슈, 수요/공급 요인을 종합 분석하세요.
   - **[Investment Strategy : 기간별 전망 및 대응 시나리오]**: 단/중/장기 전망을 정리하세요.
3. **톤앤매너**: 통계와 지표를 근거로 날카롭고 전문적인 어조를 유지하세요.

결과물 언어: 한국어
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"### ❌ 원자재 분석 중 오류 발생\n{e}"