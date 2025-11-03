import cloudscraper
from bs4 import BeautifulSoup
import logging

def fetch_notices():
    url = "https://www.sungkyul.ac.kr/computer/4101/subview.do"
    scraper = cloudscraper.create_scraper()

    try:
        response = scraper.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"❌ 크롤링 중 오류 발생: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table.board-table.horizon1 tbody tr")

    if not rows:
        logging.warning("⚠️ 게시글을 찾지 못했습니다. 사이트 구조 변경 가능성 있음.")
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
    return results
