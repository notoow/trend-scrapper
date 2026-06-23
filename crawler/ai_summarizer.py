import os
import random
import json

# API 라이브러리 임포트 예외 처리
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None

def summarize_with_gemini(text, api_key):
    """Gemini API를 사용해 한국어로 요약 및 점수화 수행"""
    if not genai or not api_key:
        raise ValueError("Gemini 라이브러리가 없거나 API 키가 설정되지 않았습니다.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
역할: 당신은 대한민국 최고의 남성 비뇨의학과 전문 의원인 '하이스트 비뇨의학과'의 콘텐츠 마케터 겸 전문 의학 번역가입니다.
목표: 제공된 원문 자료를 분석하여 '대중적 콘텐츠(유튜브, 블로그, 카드뉴스)'로의 가치를 정밀하게 평가하고, 전문 한글 요약 및 유튜브 기획 콘텐츠 세트를 만드세요.

[원문]
{text}

[요구사항 - 절대적 기준]
1. 언어 스타일:
   - **반드시 100% 순수하고 자연스러운 한국어(한글)로만 대답하세요.**
   - **한자(Hanja) 또는 중국어 간체자/일본어 문자(예: 发现, 具有, 持ち, 農耕, 具体的 등)는 어떠한 경우에도 절대 사용하지 말고, 전부 한국어 음독 및 뜻풀이 한글(예: 발견, 지님, 농경, 구체적)로만 적으십시오.**
   - 일반 대중이 읽는 채널이므로 전문 의학 용어는 초등학생도 이해할 수 있게 쉽게 풀어서 서술하세요.

2. 요약 (summary):
   - 원문의 내용을 2~3문장 이내로 핵심만 명확히 요약하세요.
   - 미사여구나 서론("본 논문은~", "연구 결과에 따르면~")을 모두 생략하고, 즉시 내용으로 들어가도록 작성하세요.

3. 콘텐츠 가치 점수 (content_score: 0~100 사이 정수):
   - 하이스트 비뇨의학과의 주력 진료 과목인 **[남성 확대수술(메가덤, 메가필), 발기부전 보형물 수술(팽창형/굴곡형), 여유증 수술, 전립선 시술(유로리프트, 리줌)]**과의 관련성에 따라 점수를 부여하세요.
   - 특히 **셀럽/가십성 비뇨의학 뉴스(예: 호날두의 성기 필러/보톡스 시술설, 해외 유명인 여유증, 스포츠 스타 요로결석 등)**나 자극적인 성 건강 소재는 대중 유튜브 킬러 콘텐츠로서 **95~100점**의 최고점을 책정하세요.
   - **90~100점**: 보형물 만족도, 확대수술 전후 사례, 여유증 수술 전후, 가십성 셀럽 비뇨의학 뉴스 등 조회수 폭발 소재.
   - **70~89점**: 일반적인 발기부전 신약, 조루증 예방 요령, 일반적인 여유증 자가진단, 전립선 비대증 치료법(유로리프트 등) 등 정보성 소재.
   - **30~69점**: 일반적인 전립선암 정기 선별검사(PSA) 가이드라인, 전립선염 예방법 등 건강 상식.
   - **0~29점**: 세포 단위 실험, 동물(쥐) 실험, 분자 생물학적 기전 연구(예: "Wnt/β-catenin 신호 경로"), 학술용 자료.

4. 유튜브 기획 자산 생성 (핵심):
   - 이 뉴스를 바탕으로 유튜브 영상을 기획한다고 가정하고 아래 3가지 항목을 **자극적이고 클릭하고 싶게** 제작하세요:
     - `youtube_title`: 시청자의 호기심을 유발하는 유튜브 제목 (예: "호날두가 거기로 간 진짜 이유? 비뇨의학과 의사가 알려줌", "남자들이 겪는 가슴 튀어나오는 병의 진실")
     - `thumbnail_text`: 유튜브 썸네일에 들어갈 4~8글자 내외의 강렬한 썸네일 카피 문구 (예: "호날두가 한 수술?", "가슴 나온 남자들 필독")
     - `internal_title`: 병원 마케팅팀 내부용 기획 제목 (예: "셀럽 시술 이슈 분석 및 여유증 수술 치료법 제안")

반드시 아래와 같은 JSON 형식으로만 응답해야 합니다 (Markdown 블록 제외, 순수 JSON 텍스트):
{{
  "summary": "한국어 요약 내용",
  "content_score": 85,
  "ai_reason": "점수 부여 근거 및 콘텐츠 기획 추천 방향",
  "youtube_title": "자극적인 유튜브 제목 카피",
  "thumbnail_text": "강렬한 썸네일 문구",
  "internal_title": "콘텐츠 기획용 내부 제목"
}}
"""
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text.strip())

def summarize_with_groq(text, api_key):
    """Groq LLaMA 3.3 API를 사용해 한국어로 요약 및 점수화 수행 (폴백 용도)"""
    if not Groq or not api_key:
        raise ValueError("Groq 라이브러리가 없거나 API 키가 설정되지 않았습니다.")
        
    client = Groq(api_key=api_key)
    
    prompt = f"""
역할: 대한민국 최고의 남성 비뇨의학과 전문 의원 '하이스트 비뇨의학과'의 콘텐츠 마케터 겸 의학 번역가.
목표: 제공된 원문 자료를 분석하여 '대중적 콘텐츠(유튜브, 블로그, 카드뉴스)'로의 가치를 평가하고 한글 요약 및 유튜브 기획 세트를 만드세요.

[원문]
{text}

[요구사항]
1. 언어: **100% 순수한 한글**로만 작성하세요. 한자, 중국어 간체자, 일본어 문자(예: 发现, 具有, 持ち, 農耕 등)는 절대 금지입니다.
2. 요약: 2~3문장 이내로 본론만 핵심 요약하세요.
3. 콘텐츠 가치 점수 (content_score):
   - 하이스트 비뇨의학과의 주력 과목인 **[남성 확대수술(메가덤, 메가필), 발기부전 보형물 수술(팽창형/굴곡형), 여유증 수술, 전립선 시술(유로리프트, 리줌)]**과의 관련성에 따라 점수를 부여하세요.
   - 특히 **셀럽/가십성 비뇨의학 뉴스(예: 호날두의 성기 필러/보톡스 시술설, 해외 유명인 여유증, 스포츠 스타 요로결석 등)**는 대중 유튜브 킬러 콘텐츠로서 **95~100점**의 최고점을 책정하세요.
   - 전문 학술 기전 연구, 쥐 실험은 무조건 0~20점대로 주어야 합니다.
4. AI 요약평 (ai_reason): 콘텐츠 추천 및 활용 방안 1문장.
5. 유튜브 기획 (클릭하고 싶게 자극적으로 만드세요):
   - `youtube_title`: 시청자 호기심 유발용 유튜브 제목
   - `thumbnail_text`: 썸네일에 들어갈 4~8글자 내외 강렬한 썸네일 카피 문구
   - `internal_title`: 콘텐츠 마케팅팀 내부용 기획 제목

반드시 아래와 같은 JSON 형식으로만 응답해야 합니다 (순수 JSON):
{{
  "summary": "한국어 요약 내용",
  "content_score": 85,
  "ai_reason": "점수 부여 근거 및 콘텐츠 기획 추천 방향",
  "youtube_title": "유튜브 제목",
  "thumbnail_text": "썸네일 문구",
  "internal_title": "기획용 내부 제목"
}}
"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    
    return json.loads(chat_completion.choices[0].message.content.strip())

import re

def clean_leaks(text):
    """일어/한자 문자 누수 클리닝 필터"""
    if not isinstance(text, str):
        return text
        
    replacements = {
        "雄激": "남성호르몬(안드로겐) ",
        "ホルモン": "호르몬",
        "发现": "발견",
        "具有": "지님",
        "具体的": "구체적",
        "農耕": "농경",
        "农耕": "농경",
        "エピソード": "에피소드",
        "에피ソ드": "에피소드",
        "평가하여": "평가하여",
        "평가되어": "평가되어",
        "evaluation": "평가"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    # 가타카나/히라가나 문자 제거 (\u3040-\u309F, \u30A0-\u30FF)
    text = re.sub(r'[\u3040-\u309F\u30A0-\u30FF]+', '', text)
    
    # 한자 문자 제거 (\u4e00-\u9fff)
    text = re.sub(r'[\u4e00-\u9fff]+', '', text)
    
    # 불필요한 이중 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def summarize(title, text, gemini_key=None, groq_key=None):
    """Gemini API를 메인으로 요약을 수행하고, 실패 시 Groq로 폴백. 둘 다 없거나 실패하면 실패 상태를 반환."""
    combined_text = f"제목: {title}\n본문 요약: {text}"
    result = None
    
    # 1. Gemini 시도
    if gemini_key:
        try:
            print("[AI 요약] Gemini API 요약 시도 중...")
            result = summarize_with_gemini(combined_text, gemini_key)
        except Exception as e:
            print(f"[AI 요약] Gemini 실패: {e}")
            
    # 2. Groq 폴백 시도
    if not result and groq_key:
        try:
            print("[AI 요약] Groq API 요약 시도 중...")
            result = summarize_with_groq(combined_text, groq_key)
        except Exception as e:
            print(f"[AI 요약] Groq 실패: {e}")
            
    # 3. 전체 실패 시 기본 에러 표시 구조 반환
    if not result:
        print("[AI 요약] API 키 누락 또는 호출 에러로 요약에 실패했습니다.")
        result = {
            "summary": "AI 요약 실패 (API 키 또는 할당량 초과)",
            "content_score": 0,
            "ai_reason": "AI API 분석 불가",
            "youtube_title": "",
            "thumbnail_text": "",
            "internal_title": ""
        }
        
    # 출력 한글 정제 필터 적용 (일어/한자 제거)
    if result:
        if "summary" in result:
            result["summary"] = clean_leaks(result["summary"])
        if "ai_reason" in result:
            result["ai_reason"] = clean_leaks(result["ai_reason"])
        if "youtube_title" in result:
            result["youtube_title"] = clean_leaks(result["youtube_title"])
        if "thumbnail_text" in result:
            result["thumbnail_text"] = clean_leaks(result["thumbnail_text"])
        if "internal_title" in result:
            result["internal_title"] = clean_leaks(result["internal_title"])
            
    return result
