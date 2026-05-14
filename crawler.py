import logging
import re
import ssl
import urllib3
import warnings

import certifi
import cloudscraper
from bs4 import BeautifulSoup

# ⚙️ SSL 관련 경고 무시
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def normalize_text(value):
    return " ".join(str(value or "").split())


def extract_notice_id(a_tag):
    href = a_tag.get("href", "").strip()
    match = re.search(r"/bbs/[^/]+/\d+/(\d+)/artclView\.do", href)
    if match:
        return match.group(1)

    onclick = a_tag.get("onclick", "")
    match = re.search(r"jf_viewArtcl\('[^']+',\s*'[^']+',\s*'([^']+)'\)", onclick)
    if match:
        return match.group(1)

    return None


def build_notice_key(notice_id=None, url=None, title="", notice_date=""):
    if notice_id:
        return f"id:{normalize_text(notice_id)}"
    if url:
        return f"url:{normalize_text(url)}"
    return f"title_date:{normalize_text(title)}|{normalize_text(notice_date)}"


def fetch_notices():
    url = "https://www.sungkyul.ac.kr/computer/4101/subview.do"

    # ✅ SSLContext 구성 (모든 환경 호환)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # ✅ Cloudflare 우회 + SSLContext 적용
    scraper = cloudscraper.create_scraper(
        ssl_context=ssl_context,
        browser={"browser": "chrome", "platform": "windows", "mobile": False},
    )

    try:
        response = scraper.get(url, timeout=10, verify=False)
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
    for row in rows:
        a_tag = row.select_one("td.td-subject a")
        date_tag = row.select_one("td.td-date")
        if not a_tag:
            continue

        title = a_tag.text.strip()
        notice_date = date_tag.text.strip() if date_tag else ""
        href = a_tag.get("href", "").strip()
        if not href.startswith("http"):
            href = "https://www.sungkyul.ac.kr" + href

        notice_id = extract_notice_id(a_tag)
        notice_key = build_notice_key(notice_id=notice_id, url=href, title=title, notice_date=notice_date)

        results.append(
            {
                "title": title,
                "link": href,
                "url": href,
                "date": notice_date,
                "notice_id": notice_id,
                "notice_key": notice_key,
            }
        )

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
