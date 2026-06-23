# 🏥 HAIST Issue Tracker

**하이스트 비뇨의학과** 이슈 트래킹 대시보드

글로벌 비뇨의학 뉴스·논문을 자동 수집하고, AI가 요약·분석하여 콘텐츠 제작에 활용할 수 있는 이슈 대시보드입니다.

## 🏗 Architecture

```
GitHub Actions (Cron: 06:00 / 12:00 / 18:00 KST)
        │
        ▼
Python Crawler (RSS + Google Trends)
        │
        ▼
AI Summarizer (Gemini 2.0 Flash / Groq LLaMA 3.3)
        │
        ▼
Google Sheets (DB + 팀 협업)
        │
        ▼
GitHub Pages (정적 대시보드)
```

## 📁 Project Structure

```
trend-scrapper/
├── .github/workflows/crawl.yml    # 자동 크롤링 스케줄
├── crawler/
│   ├── keywords.json              # 크롤링 키워드 목록
│   ├── rss_crawler.py             # RSS 수집
│   ├── trends_fetcher.py          # Google Trends 수집
│   ├── ai_summarizer.py           # AI 요약 (Gemini/Groq)
│   ├── sheets_writer.py           # Google Sheets 저장
│   └── main.py                    # 파이프라인 오케스트레이터
├── frontend/
│   ├── index.html                 # 메인 대시보드
│   ├── style.css                  # 스타일시트
│   └── app.js                     # Sheets API 호출 + 렌더링
├── .env.example                   # 환경 변수 템플릿
├── requirements.txt               # Python 패키지
└── README.md
```

## 🚀 Getting Started

### 1. Clone & Setup

```bash
git clone https://github.com/notoow/trend-scrapper.git
cd trend-scrapper
cp .env.example .env
# .env 파일에 API 키 입력
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. API Keys Required

| Key | 발급처 | 용도 |
|-----|--------|------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | AI 요약 (메인) |
| `GROQ_API_KEY` | [Groq Console](https://console.groq.com/) | AI 요약 (백업) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | [Google Cloud Console](https://console.cloud.google.com/) | Sheets API 인증 |
| `GOOGLE_SHEETS_ID` | Google Sheets URL | 데이터 저장 시트 |
| `NEWSAPI_KEY` | [NewsAPI.org](https://newsapi.org/) | 영문 뉴스 수집 |

### 4. Run Crawler

```bash
python crawler/main.py
```

### 5. View Dashboard

`frontend/index.html`을 브라우저에서 열거나, GitHub Pages로 배포합니다.

## 💰 Cost

**₩0/월** — 전체 무료 스택 운영

## 📄 License

Internal use only — 하이스트 비뇨의학과 콘텐츠팀
