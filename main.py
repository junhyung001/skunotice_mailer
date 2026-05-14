import logging
import os
import re
import sqlite3
from datetime import datetime

from dotenv import load_dotenv

from crawler import fetch_notices
from mailer import send_mail

DB_PATH = "db.sqlite3"


def setup_logger():
    # ✅ 절대 경로 기반으로 logs 디렉터리 생성 (GitHub Actions + 로컬 완벽 호환)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "notice.log")

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")],
    )


def normalize_text(value):
    return " ".join(str(value or "").split())


def extract_notice_id(url):
    if not url:
        return None
    match = re.search(r"/bbs/[^/]+/\d+/(\d+)/artclView\.do", url)
    if match:
        return match.group(1)
    return None


def build_notice_key(notice_id=None, url=None, title="", notice_date=""):
    if notice_id:
        return f"id:{normalize_text(notice_id)}"
    if url:
        return f"url:{normalize_text(url)}"
    return f"title_date:{normalize_text(title)}|{normalize_text(notice_date)}"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (
            title TEXT PRIMARY KEY,
            link TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_notices (
            notice_key TEXT PRIMARY KEY,
            notice_id TEXT,
            url TEXT,
            title TEXT NOT NULL,
            notice_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    backfill_seen_notices(cur)
    return conn, cur


def backfill_seen_notices(cur):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notices'")
    if cur.fetchone() is None:
        return

    cur.execute("SELECT title, link FROM notices")
    legacy_rows = cur.fetchall()
    for title, link in legacy_rows:
        notice_id = extract_notice_id(link)
        notice_key = build_notice_key(notice_id=notice_id, url=link, title=title)
        cur.execute(
            """
            INSERT OR IGNORE INTO seen_notices (notice_key, notice_id, url, title, notice_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (notice_key, notice_id, link, title, None),
        )
    cur.connection.commit()


def is_new(cur, notice):
    notice_key = notice["notice_key"]
    cur.execute("SELECT 1 FROM seen_notices WHERE notice_key = ?", (notice_key,))
    return cur.fetchone() is None


def save(cur, title, link, commit=True):
    try:
        cur.execute("INSERT OR IGNORE INTO notices (title, link) VALUES (?, ?)", (title, link))
        if commit:
            cur.connection.commit()
    except Exception as e:
        logging.error(f"❌ DB 저장 오류: {e}")


def save_seen_notice(cur, notice, commit=True):
    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO seen_notices (notice_key, notice_id, url, title, notice_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                notice["notice_key"],
                notice.get("notice_id"),
                notice.get("url") or notice.get("link"),
                notice["title"],
                notice.get("date"),
            ),
        )
        if commit:
            cur.connection.commit()
    except Exception as e:
        logging.error(f"❌ 신규 공지 저장 오류: {e}")


def persist_new_notices(cur, notices):
    try:
        for notice in notices:
            cur.execute("INSERT OR IGNORE INTO notices (title, link) VALUES (?, ?)", (notice["title"], notice["link"]))
            cur.execute(
                """
                INSERT OR IGNORE INTO seen_notices (notice_key, notice_id, url, title, notice_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    notice["notice_key"],
                    notice.get("notice_id"),
                    notice.get("url") or notice.get("link"),
                    notice["title"],
                    notice.get("date"),
                ),
            )
        cur.connection.commit()
    except Exception as e:
        cur.connection.rollback()
        logging.error(f"❌ 신규 공지 일괄 저장 오류: {e}")


def main():
    setup_logger()
    load_dotenv()

    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_emails = os.getenv("RECEIVER_EMAILS", "").split(",")

    conn, cur = init_db()
    try:
        notices = fetch_notices()
        new_notices = [n for n in notices if is_new(cur, n)]

        # ✅ 새 공지가 있는 경우에만 메일 발송
        if new_notices:
            html_body = """
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    h2 { color: #0056b3; }
                    ul { padding-left: 20px; }
                    li { margin-bottom: 10px; }
                    a { color: #1a73e8; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                    .footer { margin-top: 30px; font-size: 12px; color: #777; }
                </style>
            </head>
            <body>
                <h2>📢 성결대학교 컴퓨터공학과 새로운 공지사항</h2>
                <ul>
            """
            for n in new_notices:
                html_body += f'<li><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>'
            html_body += """
                </ul>
                <div class="footer">
                    본 메일은 자동 발송되었습니다.<br>
                    더 이상 수신을 원치 않으면 관리자에게 문의해주세요.
                </div>
            </body>
            </html>
            """

            mail_sent = send_mail(
                subject="[성결대 컴공과] 새로운 공지사항 알림",
                html_body=html_body,
                recipients=receiver_emails,
                sender_email=sender_email,
                sender_password=sender_password,
            )
            if mail_sent:
                persist_new_notices(cur, new_notices)
                logging.info(f"✅ {len(new_notices)}개의 새 공지를 메일로 전송했습니다!")
            else:
                logging.error("❌ 메일 전송 실패로 신규 공지 저장을 보류했습니다.")
        else:
            logging.info("🔔 새로운 공지가 없어 메일 발송을 건너뜁니다.")

    except Exception as e:
        logging.error(f"🚨 메인 루틴 오류: {e}")
        error_report = f"""
        <html><body>
        <h3>❌ 자동 공지 메일 시스템 오류 발생</h3>
        <p>{str(e)}</p>
        <p>발생 시각: {datetime.now()}</p>
        </body></html>
        """
        send_mail(
            subject="[성결대 공지 시스템] 오류 발생",
            html_body=error_report,
            recipients=[sender_email],
            sender_email=sender_email,
            sender_password=sender_password,
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
