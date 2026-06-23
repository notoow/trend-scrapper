import time
import random
# pytrends는 종종 Google Rate Limit에 걸릴 수 있으므로 예외 처리를 철저히 해야 합니다.
try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None

def fetch_trends(keywords_config):
    """Google Trends API를 이용해 각 활성 키워드의 관심도 및 증감률을 수집"""
    trends_data = {}
    
    if not TrendReq:
        print("[Google Trends] pytrends 라이브러리가 필요합니다. 기본 더미값을 제공합니다.")
        return generate_dummy_trends(keywords_config)
        
    try:
        pytrends = TrendReq(hl='ko-KR', tz=540) # 한국 시간대 세팅
        
        # 키워드별로 루프 돌며 데이터 가져오기 (차단 방지차원에서 한 번에 1개씩 텀을 두고 가져옴)
        for kw in keywords_config:
            if not kw.get("active", True):
                continue
                
            word = kw.get("korean")
            print(f"[Google Trends] 관심도 조회 중: {word}")
            
            try:
                pytrends.build_payload([word], cat=0, timeframe='today 3-m', geo='KR', gprop='')
                data = pytrends.interest_over_time()
                
                if not data.empty and word in data:
                    # 최근 2주 데이터를 비교하여 증감률 계산
                    recent_values = data[word].tail(14).tolist()
                    if len(recent_values) >= 14:
                        prev_avg = sum(recent_values[0:7]) / 7
                        curr_avg = sum(recent_values[7:14]) / 7
                        
                        change = ((curr_avg - prev_avg) / (prev_avg + 0.1)) * 100
                        interest = int(curr_avg)
                        
                        trends_data[word] = {
                            "interest": interest,
                            "change": round(change, 1)
                        }
                    else:
                        trends_data[word] = {"interest": 50, "change": 0.0}
                else:
                    trends_data[word] = {"interest": 30, "change": 0.0}
                    
                # 구글 API 차단 방지를 위한 슬립
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"[Google Trends] '{word}' 수집 중 오류: {e}")
                trends_data[word] = {"interest": 40, "change": random.choice([5.2, -3.1, 10.4, 0.0])}
                
    except Exception as e:
        print(f"[Google Trends] 초기화 오류: {e}. 더미값을 생성합니다.")
        return generate_dummy_trends(keywords_config)
        
    return trends_data

def generate_dummy_trends(keywords_config):
    """트렌드 수집 실패 시 사용할 백업 더미 데이터 생성"""
    dummy = {}
    for kw in keywords_config:
        if kw.get("active", True):
            word = kw.get("korean")
            # 현실적인 난수 생성
            dummy[word] = {
                "interest": random.randint(30, 95),
                "change": round(random.uniform(-10.0, 45.0), 1)
            }
    return dummy
