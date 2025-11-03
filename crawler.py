import warnings
import ssl
import cloudscraper
from bs4 import BeautifulSoup
import logging

# SSL 관련 경고 숨기기
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')

def fetch_notices():
    url = "https://www.sungkyul.ac.kr/computer/4101/subview.do"

    # ✅ 기본 SSL context 생성 후 검증 완전 비활성화
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # ✅ scraper 생성 (Cloudflare 우회)
    scraper = cloudscraper.create_scraper(
        ssl_context=ctx,
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )

    try:
        response = scraper.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"❌ 크롤링 중 오류 발생: {e}")
        print(f"❌ 크롤링 중 오류 발생: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table.board-table.horizon1 tbody tr")

    if not rows:
        logging.warning("⚠️ 게시글을 찾지 못했습니다. 사이트 구조 변경 가능성 있음.")
        print("⚠️ 게시글을 찾지 못했습니다. 사이트 구조 변경 가능성 있음.")
        return []

    results = []
    for row in rows[:5]:
        a_tag = row.select_one("td.td-subject a")
        if not a_tag:
            continue
        title = a_tag.text.strip()
        href = a_tag["href"].strip()
        if not href.startswith("http"):
            href = "https://www.sungkyul.ac.kr" + href
        results.append({"title": title, "link": href})

    logging.info(f"✅ {len(results)}개의 공지를 가져왔습니다.")
    print(f"✅ 크롤링 완료 — {len(results)}개의 공지를 가져왔습니다.")
    return results


if __name__ == "__main__":
    notices = fetch_notices()
    if notices:
        print("\n--- 최신 공지사항 목록 ---")
        for n in notices:
            print(f"- {n['title']} ({n['link']})")
    else:
        print("새로운 공지가 없습니다.")
