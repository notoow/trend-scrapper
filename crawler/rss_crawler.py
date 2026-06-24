import feedparser
import re
import urllib.parse
from datetime import datetime
import time

RSS_SOURCES = {
    # 커뮤니티 (Reddit)
    "Reddit Urology": "https://www.reddit.com/r/urology/.rss",
    "Reddit Sex": "https://www.reddit.com/r/sex/.rss",
    "Reddit Sexual Health": "https://www.reddit.com/r/sexualhealth/.rss",
    "Reddit Tinder": "https://www.reddit.com/r/tinder/.rss",
    "Reddit STD": "https://www.reddit.com/r/STD/.rss",
    "Reddit Sex Education": "https://www.reddit.com/r/sexeducation/.rss",
    
    # 뉴스 (국내/외)
    "CNN Health": "http://rss.cnn.com/rss/cnn_health.rss",
    "NYT Health": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    "헬스조선": "http://health.chosun.com/site/data/rss/rss.xml",
    "Yahoo Japan Life": "https://news.yahoo.co.jp/rss/categories/life.xml",
    "네이버 뉴스": "https://news.naver.com/rss/section/103"
}

def parse_date(date_str):
    """다양한 날짜 포맷을 datetime 객체로 변환"""
    try:
        # RFC 822 format (e.g. "Tue, 23 Jun 2026 06:00:00 GMT")
        return datetime.fromtimestamp(time.mktime(feedparser._parse_date(date_str)))
    except Exception:
        return datetime.now()

def fetch_rss(source_name, url):
    """RSS 피드를 수집하고 파싱"""
    print(f"[{source_name}] 수집 시작: {url}")
    try:
        # Reddit 등 일부 사이트는 User-Agent 헤더 요구
        feed = feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        entries = []
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            link = entry.get("link", "")
            pub_date_str = entry.get("published", entry.get("pubDate", ""))
            pub_date = parse_date(pub_date_str)
            
            entries.append({
                "title": title,
                "summary": summary,
                "link": link,
                "published_at": pub_date.isoformat(),
                "source": source_name
            })
        print(f"[{source_name}] 수집 완료: {len(entries)}건")
        return entries
    except Exception as e:
        print(f"[{source_name}] 수집 오류: {e}")
        return []

def filter_by_keywords(entries, keywords_config):
    """키워드 설정에 따라 관련성 높은 뉴스 필터링"""
    filtered_entries = []
    
    for entry in entries:
        matched_keywords = []
        matched_category = None
        
        content = (entry["title"] + " " + entry["summary"]).lower()
        
        for kw in keywords_config:
            if not kw.get("active", True):
                continue
                
            ko_kw = kw.get("korean", "").lower()
            en_kw = kw.get("english", "").lower()
            
            # 단어 경계(word boundary)를 고려한 간단 매칭
            if (ko_kw and ko_kw in content) or (en_kw and re.search(r'\b' + re.escape(en_kw) + r'\b', content)):
                matched_keywords.append(kw.get("korean"))
                matched_category = kw.get("category")
        
        if matched_keywords:
            entry_copy = entry.copy()
            entry_copy["matched_keywords"] = matched_keywords
            entry_copy["category"] = matched_category
            filtered_entries.append(entry_copy)
            
    return filtered_entries

import requests

def fetch_pubmed_api(keywords_config):
    """PubMed E-utilities API를 통해 2026년도 비뇨의학 관련 실제 최신 논문을 수집"""
    print("[PubMed API] 2026년도 최신 학술 논문 검색 중...")
    
    # 2026년도 발행된 활성 영문 키워드 빌드
    english_terms = []
    for kw in keywords_config:
        if kw.get("active", True) and kw.get("english"):
            english_terms.append(f'"{kw.get("english")}"')
            
    if not english_terms:
        return []
        
    query_terms = " OR ".join(english_terms)
    # 2026년도 한정 검색 쿼리
    query = f"({query_terms}) AND 2026[Date - Publication]"
    encoded_query = urllib.parse.quote(query)
    
    # esearch를 통해 최근 PMID 검색
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_query}&retmode=json&retmax=15"
    
    try:
        r = requests.get(search_url, timeout=10)
        data = r.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            print("[PubMed API] 조건에 맞는 2026년 논문이 없습니다.")
            return []
            
        print(f"[PubMed API] {len(id_list)}개 논문 ID 검색 완료. 상세 정보(Summary) 로드 중...")
        
        # esummary를 통해 상세 메타데이터 검색
        ids_str = ",".join(id_list)
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_str}&retmode=json"
        r_sum = requests.get(summary_url, timeout=10)
        sum_data = r_sum.json()
        
        results = sum_data.get("result", {})
        entries = []
        
        for pmid in id_list:
            paper = results.get(pmid)
            if not paper:
                continue
                
            title = paper.get("title", "")
            pubdate_str = paper.get("pubdate", "2026-01-01")
            
            authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])])
            journal = paper.get("source", "PubMed Journal")
            summary = f"Journal: {journal} | Authors: {authors} | Published Date: {pubdate_str}"
            
            entries.append({
                "title": title,
                "summary": summary,
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "published_at": f"2026-06-23T00:00:00Z",
                "source": "PubMed"
            })
            
        print(f"[PubMed API] 최종 {len(entries)}개 학술 논문 로드 성공.")
        return entries
        
    except Exception as e:
        print(f"[PubMed API] 수집 오류: {e}")
        return []

def fetch_news_api(keywords_config, api_key):
    """NewsAPI를 사용하여 비뇨의학 관련 2026년 글로벌 뉴스를 직접 검색 수집"""
    if not api_key:
        return []
        
    print("[NewsAPI] 글로벌 뉴스 검색 중...")
    
    english_terms = []
    for kw in keywords_config:
        if kw.get("active", True) and kw.get("english"):
            english_terms.append(kw.get("english"))
            
    if not english_terms:
        return []
        
    # 적절히 OR로 연결
    query = " OR ".join(english_terms[:4]) # 쿼리 길이 제약 대비
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://newsapi.org/v2/everything?q={encoded_query}&from=2026-01-01&language=en&sortBy=publishedAt&pageSize=15&apiKey={api_key}"
    
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if data.get("status") != "ok":
            print(f"[NewsAPI] 에러: {data.get('message')}")
            return []
            
        articles = data.get("articles", [])
        entries = []
        
        for art in articles:
            entries.append({
                "title": art.get("title", ""),
                "summary": art.get("description", art.get("content", "")),
                "link": art.get("url", ""),
                "published_at": art.get("publishedAt", "2026-06-23T00:00:00Z"),
                "source": art.get("source", {}).get("name", "NewsAPI")
            })
            
        print(f"[NewsAPI] {len(entries)}개 글로벌 뉴스 로드 완료.")
        return entries
    except Exception as e:
        print(f"[NewsAPI] 수집 오류: {e}")
        return []

import requests

def fetch_arxiv_api(keywords_config):
    """arXiv API를 통해 비뇨의학 및 성건강 관련 최근 2026년도 학술 논문을 수집"""
    print("[arXiv API] 학술 논문 검색 중...")
    english_terms = []
    for kw in keywords_config:
        if kw.get("active", True) and kw.get("english"):
            english_terms.append(f'all:"{kw.get("english")}"')
            
    if not english_terms:
        return []
        
    query = "+OR+".join(english_terms[:6])  # 검색 한도 준수
    url = f"http://export.arxiv.org/api/query?search_query={query}&max_results=10&sortBy=submittedDate&sortOrder=descending"
    
    try:
        r = requests.get(url, timeout=10)
        feed = feedparser.parse(r.text)
        entries = []
        for entry in feed.entries:
            title = entry.get("title", "").replace("\n", " ").strip()
            summary = entry.get("summary", "").replace("\n", " ").strip()
            link = entry.get("link", "")
            pub_date = entry.get("published", datetime.now().isoformat())
            
            entries.append({
                "title": title,
                "summary": summary,
                "link": link,
                "published_at": pub_date,
                "source": "arXiv"
            })
        print(f"[arXiv API] 수집 완료: {len(entries)}건")
        return entries
    except Exception as e:
        print(f"[arXiv API] 수집 오류: {e}")
        return []

def fetch_google_news(keywords_config):
    """Google News RSS 검색을 이용해 각 키워드별 고관여 기사들을 정밀 타겟 수집"""
    print("[Google News Search] 키워드 기반 관련 뉴스 타겟 수집 중...")
    entries = []
    
    # 1. 한국어 키워드 검색
    for kw in keywords_config:
        if not kw.get("active", True):
            continue
            
        ko_word = kw.get("korean")
        if not ko_word:
            continue
            
        encoded_query = urllib.parse.quote(ko_word)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            feed = feedparser.parse(url, agent='Mozilla/5.0')
            count = 0
            for entry in feed.entries:
                if count >= 3:
                    break
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")
                pub_date_str = entry.get("published", "")
                pub_date = parse_date(pub_date_str)
                
                # 출처 이름 파싱 (예: "제목 - 신문사명"에서 신문사명 추출)
                src_name = "구글 뉴스"
                if " - " in title:
                    parts = title.split(" - ")
                    title_clean = " - ".join(parts[:-1])
                    src_name = parts[-1]
                else:
                    title_clean = title
                
                entries.append({
                    "title": title_clean,
                    "summary": summary,
                    "link": link,
                    "published_at": pub_date.isoformat(),
                    "source": src_name
                })
                count += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"[Google News KR] '{ko_word}' 검색 오류: {e}")
            
    # 2. 영어 키워드 검색
    for kw in keywords_config:
        if not kw.get("active", True):
            continue
            
        en_word = kw.get("english")
        if not en_word:
            continue
            
        encoded_query = urllib.parse.quote(en_word)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=US&ceid=US:en"
        
        try:
            feed = feedparser.parse(url, agent='Mozilla/5.0')
            count = 0
            for entry in feed.entries:
                if count >= 2:
                    break
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                pub_date_str = entry.get("published", "")
                pub_date = parse_date(pub_date_str)
                
                src_name = "Google News"
                if " - " in title:
                    parts = title.split(" - ")
                    title_clean = " - ".join(parts[:-1])
                    src_name = parts[-1]
                else:
                    title_clean = title
                
                entries.append({
                    "title": title_clean,
                    "summary": summary,
                    "link": link,
                    "published_at": pub_date.isoformat(),
                    "source": src_name
                })
                count += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"[Google News Global] '{en_word}' 검색 오류: {e}")
            
    print(f"[Google News Search] 최종 검색 수집 완료: {len(entries)}건")
    return entries

def filter_by_keywords(entries, keywords_config):
    """키워드 설정에 따라 관련성 높은 뉴스 필터링"""
    filtered_entries = []
    
    for entry in entries:
        matched_keywords = []
        matched_category = None
        
        title_summary = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
        
        for kw in keywords_config:
            if not kw.get("active", True):
                continue
                
            ko_kw = kw.get("korean", "").lower()
            en_kw = kw.get("english", "").lower()
            
            # 단어 경계 혹은 포함 매치 (소문자 영어 단어 매칭 유연성 부여)
            if (ko_kw and ko_kw in title_summary) or (en_kw and en_kw in title_summary):
                matched_keywords.append(kw.get("korean"))
                matched_category = kw.get("category")
        
        if matched_keywords:
            entry_copy = entry.copy()
            entry_copy["matched_keywords"] = matched_keywords
            entry_copy["category"] = matched_category
            filtered_entries.append(entry_copy)
            
    return filtered_entries

def crawl_all(keywords_config, newsapi_key=None):
    """모든 RSS + PubMed API + arXiv API + Google News Search 소스 수집 및 키워드 필터링 진행"""
    all_raw_entries = []
    
    # 1. RSS 소스 수집 (Reddit 커뮤니티 및 주요 뉴스)
    for name, url in RSS_SOURCES.items():
        if name in ["PubMed", "arXiv"]: 
            continue
        all_raw_entries.extend(fetch_rss(name, url))
        
    # 2. PubMed API 수집
    all_raw_entries.extend(fetch_pubmed_api(keywords_config))
    
    # 3. arXiv API 수집
    all_raw_entries.extend(fetch_arxiv_api(keywords_config))
    
    # 4. Google News Search API 수집 (키워드 매칭 극대화)
    all_raw_entries.extend(fetch_google_news(keywords_config))
    
    # 5. NewsAPI 검색 결과 추가 (설정 시)
    if newsapi_key:
        all_raw_entries.extend(fetch_news_api(keywords_config, newsapi_key))
        
    filtered = filter_by_keywords(all_raw_entries, keywords_config)
    print(f"전체 수집: {len(all_raw_entries)}건 -> 필터링 통과: {len(filtered)}건")
    return filtered
