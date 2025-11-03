import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_mail(subject, html_body, recipients, sender_email, sender_password):
    """
    Gmail SMTP를 이용해 HTML 형식 이메일을 전송합니다.
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
            logging.info(f"✅ 메일 전송 완료 ({len(recipients)}명): {', '.join(recipients)}")
    except smtplib.SMTPAuthenticationError:
        logging.error("❌ 인증 실패: Gmail 앱 비밀번호를 확인하세요.")
    except smtplib.SMTPConnectError:
        logging.error("❌ 서버 연결 실패: 네트워크 또는 방화벽 문제.")
    except smtplib.SMTPRecipientsRefused:
        logging.error("❌ 수신자 주소 거부됨: 이메일 주소 형식 확인 필요.")
    except Exception as e:
        logging.error(f"❌ 메일 전송 중 알 수 없는 오류 발생: {e}")
