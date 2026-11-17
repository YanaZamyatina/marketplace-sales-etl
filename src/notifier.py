import smtplib
from email.message import EmailMessage
from config.settings import (
    EMAIL_ENABLED,
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_TO,
)
from src.logger import init_logger

log = init_logger(__name__)


def send_email_report(subject: str, body: str):
    """Отправляет текстовое уведомление на электронную почту через SSL"""
    if not EMAIL_ENABLED:
        log.info("Отправка Email отключена в настройках")
        return

    if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_TO]):
        log.warning("Не заданы данные почты в .env. Письмо не отправлено")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        log.info(f"Отчет успешно отправлен на {EMAIL_TO}")
    except Exception as e:
        log.error(f"Не удалось отправить Email: {e}")
