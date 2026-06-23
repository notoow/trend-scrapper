import os
import json
from dotenv import load_dotenv

# 로컬 모듈 임포트
from rss_crawler import crawl_all
from trends_fetcher import fetch_trends
from ai_summarizer import summarize
from sheets_writer import connect_sheets, setup_worksheets, write_issues, write_trends

def load_keywords():
    """keywords.json 파일 로드"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "keywords.json")
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Main] keywords.json 파싱 오류: {e}")
            
    # 기본 폴백 키워드 반환
    return [
        {"korean": "발기부전", "english": "erectile dysfunction", "category": "발기부전", "active": True},
        {"korean": "팽창형 보형물", "english": "inflatable penile prosthesis", "category": "보형물 수술", "active": True},
        {"korean": "여유증", "english": "gynecomastia", "category": "여유증", "active": True}
    ]

def main():
    print("=== 하이스트 이슈 트래커 크롤링 파이프라인 시작 ===")
    
    # 1. 환경 변수 로드 (.env 파일이 있으면 적용됨)
    load_dotenv()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    sheets_id = os.getenv("GOOGLE_SHEETS_ID")
    service_account_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    # 2. 키워드 목록 로드
    keywords_config = load_keywords()
    print(f"[Main] 로드된 키워드 개수: {len(keywords_config)}개")
    
    # 3. Google Trends 가져오기
    trends_data = fetch_trends(keywords_config)
    print(f"[Main] Google Trends 수집 완료 (키워드 {len(trends_data)}개)")
    
    # 4. RSS 및 API 크롤러 실행
    newsapi_key = os.getenv("NEWSAPI_KEY")
    filtered_issues = crawl_all(keywords_config, newsapi_key=newsapi_key)
    print(f"[Main] 키워드 필터링 통과 이슈: {len(filtered_issues)}건")
    
    # 5. AI 요약 수행 및 트렌드 점수 맵핑
    for idx, issue in enumerate(filtered_issues):
        print(f"[Main] AI 요약 진행 중 ({idx+1}/{len(filtered_issues)}): {issue['title']}")
        
        # 키워드 매칭 트렌드 점수 계산
        matched_kw = issue.get("matched_keywords", [])
        max_trend_score = 0
        for kw in matched_kw:
            if kw in trends_data:
                max_trend_score = max(max_trend_score, trends_data[kw].get("interest", 0))
        issue["trend_score"] = max_trend_score
        
        # AI 요약 호출
        ai_result = summarize(
            title=issue["title"],
            text=issue["summary"],
            gemini_key=gemini_key,
            groq_key=groq_key
        )
        issue["ai_data"] = ai_result
        
    # 6. Google Sheets에 결과 저장
    sheet = connect_sheets(sheets_id, service_account_b64)
    if sheet:
        setup_worksheets(sheet)
        write_issues(sheet, filtered_issues)
        write_trends(sheet, trends_data)
        print("[Main] 스프레드시트 업데이트 최종 완료.")
    else:
        print("[Main] Google Sheets 연결 스킵 (인증 키가 지정되지 않아 로컬 파일 출력으로 대체합니다.)")
        # 디버그용 파일 출력
        output_path = "crawler_result_debug.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(filtered_issues, f, ensure_ascii=False, indent=2)
        print(f"[Main] 디버그용 결과 파일 저장됨: {output_path}")
        
    print("=== 하이스트 이슈 트래커 크롤링 파이프라인 종료 ===")

if __name__ == "__main__":
    main()
