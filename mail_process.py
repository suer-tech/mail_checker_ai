import os
from imapclient import IMAPClient
import email
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

# Конфигурация почты
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
imap_server = os.getenv("IMAP_SERVER")

def connect_to_mail():
    print("[Шаг] Подключение к почте...")
    # Подключение к IMAP серверу
    mail = IMAPClient(imap_server, use_uid=True, ssl=True)
    mail.login(username, password)
    print("[Шаг] Успешное подключение к почте")
    return mail


def get_all_emails(mail):
    print("[Шаг] Получение всех писем из папки 'Входящие'...")
    # Выбор папки "Входящие"
    mail.select_folder("INBOX")

    # Поиск всех писем
    messages = mail.search(['ALL'])
    all_emails = []

    print(f"[Шаг] Найдено {len(messages)} писем")

    for uid in messages:
        message_data = mail.fetch([uid], ['RFC822'])
        raw_email = message_data[uid][b'RFC822']
        msg = email.message_from_bytes(raw_email)

        # Декодирование заголовков
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')

        # Извлечение текста письма
        email_body = extract_email_body(msg)

        all_emails.append({
            'id': uid,
            'subject': subject,
            'body': email_body
        })

    print(f"[Шаг] Все письма успешно получены")
    return all_emails

def extract_email_body(msg):
    """Извлекает текстовое содержимое письма."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
    else:
        print("[Шаг] Письмо не многокомпонентное")
        return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8')