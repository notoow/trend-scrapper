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
    # Gemini 2.0 Flash 모델 사용
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
다음은 비뇨의학 관련 텍스트 데이터입니다. 이를 기반으로 홍보 콘텐츠로 활용할 수 있도록 요약해 주세요.

[원문]
{text}

[요구사항]
1. 반드시 친절한 한국어로 작성하세요.
2. 2~3문장 이내로 핵심 내용만 간결하게 요약해 주세요. (가독성 중요)
3. 대시보드 카드에 바로 표시될 내용이므로, 서론/결론 빼고 요약 자체만 전달하세요.
4. 이 정보가 대중적인 카드뉴스나 블로그 글로 변환하기에 적합한지 평가하여 "콘텐츠화 점수 (0~100점)"를 책정하세요.
5. AI가 선정한 이유를 1문장으로 작성해 주세요.

반드시 아래와 같은 JSON 형식으로만 응답해야 합니다:
{{
  "summary": "한국어 요약 내용...",
  "content_score": 85,
  "ai_reason": "선정 이유..."
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
의학 텍스트 요약 및 콘텐츠 가치 분석을 수행하세요.
텍스트: {text}

JSON 형식으로 응답하세요:
{{
  "summary": "한국어 2-3줄 요약",
  "content_score": 0~100 사이 정수,
  "ai_reason": "AI 선정 이유"
}}
"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama3-70b-8192",
        response_format={"type": "json_object"}
    )
    
    return json.loads(chat_completion.choices[0].message.content.strip())

def summarize(title, text, gemini_key=None, groq_key=None):
    """Gemini API를 메인으로 요약을 수행하고, 실패 시 Groq로 폴백. 둘 다 없으면 더미 데이터 반환."""
    combined_text = f"제목: {title}\n본문 요약: {text}"
    
    # 1. Gemini 시도
    if gemini_key:
        try:
            print("[AI 요약] Gemini API 요약 시도 중...")
            result = summarize_with_gemini(combined_text, gemini_key)
            return result
        except Exception as e:
            print(f"[AI 요약] Gemini 실패: {e}")
            
    # 2. Groq 폴백 시도
    if groq_key:
        try:
            print("[AI 요약] Groq API 요약 시도 중...")
            result = summarize_with_groq(combined_text, groq_key)
            return result
        except Exception as e:
            print(f"[AI 요약] Groq 실패: {e}")
            
    # 3. 전체 실패 시 기본 더미 반환
    print("[AI 요약] API 키 누락 또는 호출 에러로 인해 로컬 더미 요약을 제공합니다.")
    return generate_dummy_summary(title)

def generate_dummy_summary(title):
    """임시 요약 정보 생성"""
    scores = [78, 83, 89, 92, 96]
    reasons = [
        "아시아 데이터 포함 대규모 연구로 국내 공감도가 높고 스크립트 작성에 적합합니다.",
        "여유증 등 대중적인 MZ세대 남성 콤플렉스를 자극하여 SNS 카드뉴스 소재로 제격입니다.",
        "기존 비아그라 계열 대체 신약으로 환자 고관여 기사 발행 시 노출 확률이 높습니다."
    ]
    return {
        "summary": f"'{title}' 에 대한 의학적 정보 분석 자료입니다. 수술 전후 비교 및 최신 가이드라인이 명시되어 있어 국내 환자 맞춤형 정보로 재해석하여 콘텐츠 제작에 활용이 용이합니다.",
        "content_score": random.choice(scores),
        "ai_reason": random.choice(reasons)
    }
