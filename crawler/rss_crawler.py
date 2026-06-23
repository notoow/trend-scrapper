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

def crawl_all(keywords_config):
    """모든 RSS 소스 수집 및 키워드 필터링 진행"""
    all_raw_entries = []
    for name, url in RSS_SOURCES.items():
        all_raw_entries.extend(fetch_rss(name, url))
        
    filtered = filter_by_keywords(all_raw_entries, keywords_config)
    print(f"전체 수집: {len(all_raw_entries)}건 -> 필터링 통과: {len(filtered)}건")
    return filtered
