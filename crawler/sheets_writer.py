import json
import base64
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

def get_creds_from_env(env_json_base64):
    """Base64로 인코딩된 서비스 계정 JSON 문자열로부터 Credentials 반환"""
    if not Credentials:
        raise ImportError("google-auth 라이브러리가 필요합니다.")
        
    try:
        decoded = base64.b64decode(env_json_base64).decode('utf-8')
        info = json.loads(decoded)
    except Exception:
        # 인코딩이 안 되어 있는 일반 JSON String 대응
        info = json.loads(env_json_base64)
        
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    return Credentials.from_service_account_info(info, scopes=scopes)

def connect_sheets(sheets_id, service_account_json_base64):
    """Google Sheets 연결 및 스프레드시트 객체 반환"""
    if not gspread:
        print("[Google Sheets] gspread 라이브러리가 설치되지 않았습니다.")
        return None
        
    if not sheets_id or not service_account_json_base64:
        print("[Google Sheets] 시트 ID 혹은 인증 JSON 환경변수가 비어있습니다.")
        return None
        
    try:
        creds = get_creds_from_env(service_account_json_base64)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheets_id)
        print(f"[Google Sheets] 성공적으로 스프레드시트에 연결되었습니다: {sheet.title}")
        return sheet
    except Exception as e:
        import traceback
        print(f"[Google Sheets] 스프레드시트 연결 실패 상세 에러:")
        traceback.print_exc()
        return None

def setup_worksheets(sheet):
    """필요한 시트들이 없으면 자동으로 생성하고 헤더를 추가"""
    if not sheet:
        return
        
    # 1. issues 시트 설정
    try:
        issues_ws = sheet.worksheet("issues")
    except Exception:
        issues_ws = sheet.add_worksheet(title="issues", rows="1000", cols="10")
        issues_ws.append_row(["id", "date", "title", "source", "url", "category", "summary", "ai_reason", "content_score", "trend_score"])
        
    # 2. trends 시트 설정
    try:
        trends_ws = sheet.worksheet("trends")
    except Exception:
        trends_ws = sheet.add_worksheet(title="trends", rows="1000", cols="4")
        trends_ws.append_row(["date", "keyword", "interest", "change"])
        
    # 3. bookmarks 시트 설정
    try:
        bookmarks_ws = sheet.worksheet("bookmarks")
    except Exception:
        bookmarks_ws = sheet.add_worksheet(title="bookmarks", rows="1000", cols="6")
        bookmarks_ws.append_row(["issue_id", "author", "tag", "memo", "idea", "status"])

def write_issues(sheet, issues):
    """수집된 이슈들을 issues 시트에 일괄 추가 (중복 URL 제외)"""
    if not sheet or not issues:
        return
        
    try:
        ws = sheet.worksheet("issues")
        existing_urls = ws.col_values(5)[1:] # 5번째 열은 URL
        
        rows_to_add = []
        import uuid
        from datetime import datetime
        
        for issue in issues:
            url = issue.get("link")
            if url in existing_urls:
                continue # 중복 링크 제외
                
            issue_id = str(uuid.uuid4())[:8]
            date_str = issue.get("published_at", datetime.now().isoformat())
            title = issue.get("title")
            source = issue.get("source")
            category = issue.get("category", "일반")
            
            ai_data = issue.get("ai_data", {})
            summary = ai_data.get("summary", "")
            ai_reason = ai_data.get("ai_reason", "")
            score = ai_data.get("content_score", 50)
            
            trend_score = issue.get("trend_score", 0)
            
            rows_to_add.append([
                issue_id, date_str, title, source, url, category, summary, ai_reason, score, trend_score
            ])
            
        if rows_to_add:
            # 일괄 쓰기(Append)로 요청 쿼터 아끼기
            ws.append_rows(rows_to_add)
            print(f"[Google Sheets] {len(rows_to_add)}개의 새로운 이슈 저장 완료.")
        else:
            print("[Google Sheets] 새로 추가할 이슈가 없습니다.")
            
    except Exception as e:
        print(f"[Google Sheets] 이슈 저장 중 오류: {e}")

def write_trends(sheet, trends_data):
    """trends_data를 trends 시트에 저장"""
    if not sheet or not trends_data:
        return
        
    try:
        ws = sheet.worksheet("trends")
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        rows_to_add = []
        for kw, val in trends_data.items():
            rows_to_add.append([
                date_str, kw, val["interest"], val["change"]
            ])
            
        if rows_to_add:
            ws.append_rows(rows_to_add)
            print(f"[Google Sheets] {len(rows_to_add)}개의 키워드 트렌드 지수 업데이트 완료.")
            
    except Exception as e:
        print(f"[Google Sheets] 트렌드 지수 저장 오류: {e}")
