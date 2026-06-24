import os
import time
import sys
from dotenv import load_dotenv

# Add current directory to path to import sheets_writer and ai_summarizer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_writer import connect_sheets
from ai_summarizer import summarize

def backfill():
    print("=== YouTube 기획 자산 백필(Backfill) 프로세스 시작 ===")
    load_dotenv()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    sheets_id = os.getenv("GOOGLE_SHEETS_ID")
    service_account_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    sheet = connect_sheets(sheets_id, service_account_b64)
    if not sheet:
        print("[오류] Google Sheets에 연결할 수 없습니다. 환경변수 설정을 확인하세요.")
        return
        
    try:
        ws = sheet.worksheet("issues")
    except Exception as e:
        print(f"[오류] 'issues' 워크시트를 찾을 수 없습니다: {e}")
        return
        
    all_rows = ws.get_all_values()
    if len(all_rows) <= 1:
        print("[정보] 시트에 백필할 데이터가 없습니다.")
        return
        
    rows_to_update = []
    for idx, row in enumerate(all_rows[1:], start=2):  # 헤더 제외하고 2행부터 시작
        # 컬럼 인덱스 10(youtube_title)이 비어있거나 부족한 경우 타겟 지정
        yt_title = row[10] if len(row) > 10 else ""
        title = row[2]
        summary = row[6]
        
        if not yt_title.strip() or yt_title == "AI 요약 실패 (API 키 또는 할당량 초과)":
            rows_to_update.append({
                "row_num": idx,
                "title": title,
                "summary": summary
            })
            
    if not rows_to_update:
        print("[완료] 모든 데이터에 이미 유튜브 기획안이 존재합니다. 백필이 필요하지 않습니다.")
        return
        
    print(f"[정보] 총 {len(rows_to_update)}개의 행에 유튜브 기획안 백필이 필요합니다.")
    
    for item in rows_to_update:
        row_num = item["row_num"]
        title = item["title"]
        summary = item["summary"]
        
        print(f"\n[AI 요약 진행] {row_num}행: {title}")
        ai_data = summarize(
            title=title,
            text=summary,
            gemini_key=gemini_key,
            groq_key=groq_key
        )
        
        if ai_data and ai_data.get("youtube_title"):
            yt_title = ai_data.get("youtube_title", "")
            tb_text = ai_data.get("thumbnail_text", "")
            int_title = ai_data.get("internal_title", "")
            
            try:
                # K(11열), L(12열), M(13열) 범위 업데이트
                ws.update(f"K{row_num}:M{row_num}", [[yt_title, tb_text, int_title]])
                print(f"[업데이트 완료] {row_num}행 유튜브 기획안 적용 성공!")
            except Exception as e:
                print(f"[오류] {row_num}행 업데이트 중 에러 발생: {e}")
        else:
            print(f"[경고] {row_num}행 AI 요약 생성 실패.")
            
        time.sleep(2)  # API 속도 제한 방지용 슬립
        
    print("\n=== 유튜브 기획 자산 백필 완료 ===")

if __name__ == "__main__":
    backfill()
