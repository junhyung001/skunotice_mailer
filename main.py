import sqlite3
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from crawler import fetch_notices
from mailer import send_mail

DB_PATH = "db.sqlite3"

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            title TEXT PRIMARY KEY,
            link TEXT
        )
    """)
    conn.commit()
    return conn, cur

def is_new(cur, title):
    cur.execute("SELECT 1 FROM notices WHERE title = ?", (title,))
    return cur.fetchone() is None

def save(cur, title, link):
    try:
        cur.execute("INSERT OR IGNORE INTO notices (title, link) VALUES (?, ?)", (title, link))
        cur.connection.commit()
    except Exception as e:
        logging.error(f"❌ DB 저장 오류: {e}")

def main():
    setup_logger()
    load_dotenv()

    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_emails = os.getenv("RECEIVER_EMAILS", "").split(",")

    conn, cur = init_db()
    try:
        notices = fetch_notices()
        new_notices = [n for n in notices if is_new(cur, n["title"])]

        if not new_notices:
            logging.info("🔔 새로운 공지가 없습니다.")
        else:
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
                save(cur, n["title"], n["link"])

            html_body += """
                </ul>
                <div class="footer">
                    본 메일은 자동 발송되었습니다.<br>
                    더 이상 수신을 원치 않으면 관리자에게 문의해주세요.
                </div>
            </body>
            </html>
            """

            send_mail(
                subject="[성결대 컴공과] 새로운 공지사항 알림",
                html_body=html_body,
                recipients=receiver_emails,
                sender_email=sender_email,
                sender_password=sender_password
            )
            logging.info(f"✅ {len(new_notices)}개의 새 공지를 메일로 전송했습니다!")

    except Exception as e:
        logging.error(f"🚨 메인 루틴 오류: {e}")
        # 오류 발생 시 관리자에게 에러 리포트 메일 전송
        error_report = f"""
        <html><body>
        <h3>❌ 자동 공지 메일 시스템 오류 발생</h3>
        <p>{str(e)}</p>
        <p>발생 시각: {datetime.now()}</p>
        </body></html>
        """
        send_mail(
            subject="[성결대 공지 메일 시스템] 오류 발생",
            html_body=error_report,
            recipients=[sender_email],
            sender_email=sender_email,
            sender_password=sender_password
        )

    finally:
        conn.close()

if __name__ == "__main__":
    main()
