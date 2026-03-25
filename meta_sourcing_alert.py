import requests
import os
from datetime import datetime, timedelta

# =====================
# 환경변수에서 읽어오기
# =====================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")

# =====================
# 검색 키워드
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
        "disable_web_page_preview": True,
    }
    res = requests.post(url, json=payload)
    print(f"텔레그램 전송: {res.status_code}")
    return res.status_code

# =====================
# 메타 광고 라이브러리 조회 (사용자 토큰 방식)
# =====================
def fetch_meta_ads(keyword):
    url = "https://graph.facebook.com/v21.0/ads_archive"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "ad_reached_countries": "['KR']",
        "search_terms": keyword,
        "ad_active_status": "ACTIVE",
        "fields": "id,ad_creation_time,ad_creative_bodies,ad_creative_link_captions,page_name",
        "limit": 5,
    }

    res = requests.get(url, params=params)
    print(f"[{keyword}] 상태코드: {res.status_code}")

    if res.status_code != 200:
        print(f"[{keyword}] 응답: {res.text[:200]}")
        return []

    data = res.json()
    results = data.get("data", [])
    print(f"[{keyword}] {len(results)}개 광고 발견")
    return results

# =====================
# 메인 실행
# =====================
def main():
    print("=" * 30)
    print("소싱 알리미 시작")
    print(f"실행시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"TELEGRAM_BOT_TOKEN: {'OK' if TELEGRAM_BOT_TOKEN else 'MISSING'}")
    print(f"TELEGRAM_CHAT_ID: {'OK' if TELEGRAM_CHAT_ID else 'MISSING'}")
    print(f"META_ACCESS_TOKEN: {'OK' if META_ACCESS_TOKEN else 'MISSING'}")
    print("=" * 30)

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

            bodies = ad.get("ad_creative_bodies", [])
            body_text = bodies[0][:80] + "..." if bodies else "본문 없음"

            captions = ad.get("ad_creative_link_captions", [])
            landing_url = captions[0] if captions else "URL 없음"

            created = ad.get("ad_creation_time", "")[:10]

            all_results.append({
                "keyword": keyword,
                "page": page_name,
                "body": body_text,
                "url": landing_url,
                "created": created,
            })

    print(f"총 {len(all_results)}개 결과 수집")

    if not all_results:
        msg = f"🔍 <b>[{now}] 소싱 알리미</b>\n\n오늘은 신규 광고 없음"
        send_telegram(msg)
        return

    message = f"🔍 <b>[{now}] 소싱 알리미</b>\n"
    message += f"총 <b>{len(all_results)}개</b> 광고 감지\n"
    message += "─" * 20 + "\n\n"

    for r in all_results[:15]:
        message += f"🏷 <b>{r['page']}</b>\n"
        message += f"🔑 {r['keyword']} | 📅 {r['created']}\n"
        message += f"📝 {r['body']}\n"
        message += f"🔗 {r['url']}\n\n"

    if len(message) > 4000:
        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for chunk in chunks:
            send_telegram(chunk)
    else:
        send_telegram(message)

    print("완료!")

if __name__ == "__main__":
    main()
