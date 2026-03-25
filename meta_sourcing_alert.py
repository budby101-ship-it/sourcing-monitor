import requests
import json
from datetime import datetime, timedelta

# =====================
# 설정값 (본인 것으로 교체 완료)
# =====================
TELEGRAM_BOT_TOKEN = "8690375842:AAG9Upu-MByPoK4HQ002wdBRVSZU6fAo9qE"
TELEGRAM_CHAT_ID = "8161431561"
META_ACCESS_TOKEN = "1456657566257469|yXkZXxszw2lkcLFkqb4vv-T4jSY"

# =====================
# 검색 키워드 (원하는 대로 추가/수정 가능)
# =====================
KEYWORDS = [
    "영양제",
    "다이어트",
    "올리브오일",
    "콜라겐",
    "저속노화",
    "혈당",
    "체지방",
    "디톡스",
    "효소",
    "유산균",
]

# =====================
# 텔레그램 메시지 전송
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    res = requests.post(url, json=payload)
    return res.status_code

# =====================
# 메타 광고 라이브러리 조회
# =====================
def fetch_meta_ads(keyword):
    url = "https://graph.facebook.com/v21.0/ads_archive"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "ad_reached_countries": "KR",
        "search_terms": keyword,
        "ad_active_status": "ACTIVE",
        "ad_delivery_date_min": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "fields": "id,ad_creation_time,ad_creative_bodies,ad_creative_link_captions,ad_creative_link_descriptions,ad_creative_link_titles,page_name,publisher_platforms",
        "limit": 10,
    }

    res = requests.get(url, params=params)
    if res.status_code != 200:
        return []

    data = res.json()
    return data.get("data", [])

# =====================
# 메인 실행
# =====================
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    all_results = []
    seen_pages = set()

    for keyword in KEYWORDS:
        ads = fetch_meta_ads(keyword)
        for ad in ads:
            page_name = ad.get("page_name", "알 수 없음")
            if page_name in seen_pages:
                continue
            seen_pages.add(page_name)

            # 광고 본문 추출
            bodies = ad.get("ad_creative_bodies", [])
            body_text = bodies[0][:80] + "..." if bodies else "본문 없음"

            # 랜딩 URL 추출
            captions = ad.get("ad_creative_link_captions", [])
            landing_url = captions[0] if captions else "URL 없음"

            # 광고 시작일
            created = ad.get("ad_creation_time", "")[:10]

            all_results.append({
                "keyword": keyword,
                "page": page_name,
                "body": body_text,
                "url": landing_url,
                "created": created,
            })

    # 텔레그램 메시지 구성
    if not all_results:
        send_telegram(f"🔍 <b>[{now}] 소싱 알리미</b>\n\n신규 광고 없음")
        return

    message = f"🔍 <b>[{now}] 소싱 알리미</b>\n"
    message += f"총 <b>{len(all_results)}개</b> 신규 광고 감지\n"
    message += "─" * 20 + "\n\n"

    for r in all_results[:15]:  # 최대 15개
        message += f"🏷 <b>{r['page']}</b>\n"
        message += f"🔑 키워드: {r['keyword']}\n"
        message += f"📅 광고시작: {r['created']}\n"
        message += f"📝 {r['body']}\n"
        message += f"🔗 {r['url']}\n"
        message += "\n"

    # 메시지가 너무 길면 분할 전송
    if len(message) > 4000:
        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for chunk in chunks:
            send_telegram(chunk)
    else:
        send_telegram(message)

    print(f"[{now}] 완료 - {len(all_results)}개 광고 전송")

if __name__ == "__main__":
    main()
