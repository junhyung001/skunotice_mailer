# 📬 Sungkyul Notice Mailer

성결대학교 컴퓨터공학과 공지사항을 매일 자동으로 확인하고, 새로운 공지가 올라오면 이메일로 알려주는 Python 기반 자동화 시스템입니다.
GitHub Actions를 이용해 매일 오전 9시에 자동 실행되며, 크롤링・DB저장・메일발송까지 전 과정을 자동 처리합니다.

---

## 🧱 프로젝트 구조

```
📦 skunotice-mailer/
 ┣ 📜 main.py             # 메인 제어 로직
 ┣ 📜 crawler.py          # 공지사항 크롤러 (cloudscraper + BeautifulSoup)
 ┣ 📜 mailer.py           # Gmail SMTP 메일 발송 모듈
 ┣ 📜 requirements.txt    # 의존성 패키지 목록
 ┗ 📁 .github/workflows/
     ┗ 📜 notice.yml      # GitHub Actions 자동 실행 설정
```

---

## ⚙️ 주요 기능

| 기능                     | 설명                                          |
| ---------------------- | ------------------------------------------- |
| **공지사항 크롤링**           | Sungkyul Univ. 컴퓨터공학과 게시판에서 최신 5개의 공지 자동 수집 |
| **DB 저장/중복 체크**        | SQLite로 이전 공지와 중복 여부 판단                     |
| **이메일 자동 발송**          | 새 공지가 있을 때 HTML 템플릿으로 자동 메일 발송              |
| **에러 리포트 메일**          | 실행 중 오류 발생 시 관리자에게 자동 보고 메일 전송              |
| **GitHub Actions 자동화** | 매일 오전 9시(UTC 0시)에 자동 실행                     |

---

## 🧩 사용 기술

* **Python 3.11**
* **BeautifulSoup4 / cloudscraper**
* **SQLite3**
* **smtplib / email.mime**
* **GitHub Actions (CI/CD & Scheduler)**
* **dotenv (환경 변수 관리)**

---

## 📦 설치 및 설정

### 1️⃣ 의존성 설치

```bash
pip install -r requirements.txt
```

### 2️⃣ 환경 변수 (.env)

로컬 테스트 시 프로젝트 루트에 `.env` 파일 생성:

```
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECEIVER_EMAILS=receiver1@gmail.com,receiver2@gmail.com
```

### 3️⃣ GitHub Secrets 등록

GitHub → Settings → Secrets and variables → Actions
아래 항목 추가:

| Key               | Value 예시                                                                            |
| ----------------- | ----------------------------------------------------------------------------------- |
| `SENDER_EMAIL`    | [your_email@gmail.com](mailto:your_email@gmail.com)                                 |
| `SENDER_PASSWORD` | 16자리 앱 비밀번호                                                                         |
| `RECEIVER_EMAILS` | [user1@gmail.com](mailto:user1@gmail.com),[user2@gmail.com](mailto:user2@gmail.com) |

---

## ⚡ 자동 실행 (GitHub Actions)

`.github/workflows/notice.yml` 파일의 cron 스케줄러가 매일 오전 9시(KST)에 실행됩니다.

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 기준 0시 → 한국 오전 9시
```

> 수동 실행도 “Actions → Run workflow”에서 가능합니다.

---

## 🧠 작동 방식

1. **crawler.py** 가 성결대 컴공 게시판 HTML을 파싱
2. 새 공지인지 DB(`db.sqlite3`)에서 확인
3. 새 공지가 있다면 HTML 메일 템플릿으로 내용 생성
4. Gmail SMTP를 통해 수신자 리스트로 전송
5. 에러 발생 시 관리자(발신자)에게 오류 리포트 메일 발송

---

## 📜 로그 예시

```
[2025-11-03 09:00:02] INFO: ✅ 3개의 공지를 가져왔습니다.
[2025-11-03 09:00:03] INFO: ✅ 1개의 새 공지를 메일로 전송했습니다!
[2025-11-03 09:00:03] INFO: ✅ 메일 전송 완료 (2명): user1@gmail.com, user2@gmail.com
```

---

## 🚀 향후 개선 계획

* [ ] “공지 없음”일 때도 요약 리포트 메일 전송
* [ ] 크롤링 대상 확장 (학교 공지 전체 등)
* [ ] Webhook 연동 (Slack / Discord 알림)
* [ ] Docker 기반 배포 환경 구성

---

## 📄 라이선스

MIT License © 2025 Junhyeong Jo
