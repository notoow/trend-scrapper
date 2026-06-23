import feedparser
import re
import urllib.parse
from datetime import datetime
import time

RSS_SOURCES = {
    "BBC Health": "http://feeds.bbci.co.uk/news/health/rss.xml",
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1yQGjS7s7gN1m2tL-6T-2Q/?limit=50", # 임시 pubmed rss URL 예시
    "Reddit Urology": "https://www.reddit.com/r/urology/.rss",
    "네이버 뉴스": "https://news.naver.com/rss/section/103" # 생활/문화 카테고리
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
            
            # 단어 경계(word boundary)를 고려한 간단 매칭
            if (ko_kw and ko_kw in title_summary) or (en_kw and re.search(r'\b' + re.escape(en_kw) + r'\b', title_summary)):
                matched_keywords.append(kw.get("korean"))
                matched_category = kw.get("category")
        
        if matched_keywords:
            entry_copy = entry.copy()
            entry_copy["matched_keywords"] = matched_keywords
            entry_copy["category"] = matched_category
            filtered_entries.append(entry_copy)
            
    return filtered_entries

def crawl_all(keywords_config, newsapi_key=None):
    """모든 RSS + PubMed API + NewsAPI 소스 수집 및 키워드 필터링 진행"""
    all_raw_entries = []
    
    # 1. 기존 RSS 소스 수집
    for name, url in RSS_SOURCES.items():
        if name == "PubMed": 
            continue # PubMed는 API로 더 풍부하게 긁어올 것이므로 RSS 수집은 스킵
        all_raw_entries.extend(fetch_rss(name, url))
        
    # 2. PubMed 2026년도 API 다이렉트 검색 결과 추가
    all_raw_entries.extend(fetch_pubmed_api(keywords_config))
    
    # 3. NewsAPI 검색 결과 추가
    if newsapi_key:
        all_raw_entries.extend(fetch_news_api(keywords_config, newsapi_key))
        
    filtered = filter_by_keywords(all_raw_entries, keywords_config)
    print(f"전체 수집: {len(all_raw_entries)}건 -> 필터링 통과: {len(filtered)}건")
    return filtered
