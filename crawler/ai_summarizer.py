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
목표: 제공된 원문 자료를 분석하여 '대중적 콘텐츠(유튜브, 블로그, 카드뉴스)'로의 가치를 정밀하게 평가하고, 전문 한글 요약을 만드세요.

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
   - **90~100점**: 팽창형/굴곡형 보형물 수술 결과, 환자 만족도, 여유증 수술 전후, 음경 확대수술과 같이 유튜브 콘텐츠나 블로그 글로 즉각 제작 시 조회수가 폭발할 대중적/상업적 킬러 소재.
   - **70~89점**: 일반적인 발기부전 치료제, 조루증 예방 요령, 일반적인 여유증 자가진단, 전립선 비대증 치료법(유로리프트 등) 등 환자 고관여 정보성 소재.
   - **30~69점**: 일반적인 전립선암 정기 선별검사(PSA) 가이드라인, 전립선염 예방법 등 정보성은 있으나 유튜브 소재로는 조금 심심한 건강 상식.
   - **0~29점**: 세포 단위 실험, 동물(쥐) 실험, 분자 생물학적 기전 연구(예: "Wnt/β-catenin 신호전달 조절 경로", "enzalutamide 저항성 기전"), 보험 수가 정책 변경 등. **대중 유튜브 콘텐츠화가 불가능한 학술용 자료는 무조건 0~20점대로 낮게 주어야 합니다.**

4. AI 요약평 (ai_reason):
   - 책정한 콘텐츠 점수의 이유와 함께, 이를 '유튜브, 블로그 등 어떤 콘텐츠'로 풀어내면 좋은지 활용 방향성을 1문장으로 명확히 제시하세요. (예: "여유증 자가 진단 및 수술 시기를 다루는 유튜브 스크립트 소재로 강추합니다.")

반드시 아래와 같은 JSON 형식으로만 응답해야 합니다 (Markdown 블록 제외, 순수 JSON 텍스트):
{{
  "summary": "한국어 요약 내용",
  "content_score": 85,
  "ai_reason": "점수 부여 근거 및 콘텐츠 기획 추천 방향"
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
목표: 제공된 원문 자료를 분석하여 '대중적 콘텐츠(유튜브, 블로그, 카드뉴스)'로의 가치를 평가하고 한글 요약을 만드세요.

[원문]
{text}

[요구사항]
1. 언어: **100% 순수한 한글**로만 작성하세요. **한자(Hanja), 중국어 간체자, 일본어 문자(예: 发现, 具有, 持ち, 農耕 등)는 어떠한 상황에서도 절대 쓰지 마십시오.** 모두 한글 단어(예: 발견, 지님, 농경 등)로 번역하여 사용하십시오.
2. 요약: 2~3문장 이내로 본론만 핵심 요약하세요.
3. 콘텐츠 가치 점수 (content_score):
   - 하이스트 비뇨의학과의 주력 과목인 **[남성 확대수술(메가덤, 메가필), 발기부전 보형물 수술(팽창형/굴곡형), 여유증 수술, 전립선 시술(유로리프트, 리줌)]**과의 직결도에 따라 점수를 부여하세요.
   - **90~100점**: 보형물 수술 만족도, 확대수술 전후 사례, 여유증 수술 가이드 등 대중 조회수가 높고 직접적인 유튜브/블로그 킬러 소재.
   - **70~89점**: 발기부전 신약, 조루증 관리법, 일반적 전립선 비대증 치료법 등 유용한 정보 소재.
   - **30~69점**: 일반적인 전립선암 정기 PSA 검사 통계 등 일반 상식 소재.
   - **0~29점**: 세포/분자 수준 메커니즘 기전 연구(예: "Wnt/β-catenin 신호 경로", "enzalutamide 저항성"), 실험용 쥐 연구 등 **유튜브 등 대중용 콘텐츠화가 불가능한 전문 학술 논문은 0~20점대**로 점수를 아주 낮게 책정하십시오.
4. AI 요약평 (ai_reason): 이 소재를 활용한 추천 콘텐츠 기획 방향(유튜브, 블로그 등)을 1문장으로 적으세요.

반드시 아래와 같은 JSON 형식으로만 응답해야 합니다 (순수 JSON):
{{
  "summary": "한국어 요약 내용",
  "content_score": 85,
  "ai_reason": "점수 부여 근거 및 콘텐츠 기획 추천 방향"
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
    """Gemini API를 메인으로 요약을 수행하고, 실패 시 Groq로 폴백. 둘 다 없으면 더미 데이터 반환."""
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
            
    # 3. 전체 실패 시 기본 더미 반환
    if not result:
        print("[AI 요약] API 키 누락 또는 호출 에러로 인해 로컬 더미 요약을 제공합니다.")
        result = generate_dummy_summary(title)
        
    # 출력 한글 정제 필터 적용 (일어/한자 제거)
    if result:
        if "summary" in result:
            result["summary"] = clean_leaks(result["summary"])
        if "ai_reason" in result:
            result["ai_reason"] = clean_leaks(result["ai_reason"])
            
    return result

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
