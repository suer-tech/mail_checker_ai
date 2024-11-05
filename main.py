import json
from email.mime.text import MIMEText
import requests
from imapclient import IMAPClient
import email
from email.header import decode_header
from config import IMAP_SERVER, USERNAME, PASSWORD, VOICEFLOW_API_KEY, PROJECT_ID

def connect_to_mail():
    print("[Шаг] Подключение к почте...")
    mail = IMAPClient(IMAP_SERVER, use_uid=True, ssl=True)
    mail.login(USERNAME, PASSWORD)
    print("[Шаг] Успешное подключение к почте")
    return mail

def get_all_emails(mail):
    print("[Шаг] Получение всех писем из папки 'Входящие'...")
    mail.select_folder("INBOX")
    messages = mail.search(['ALL'])
    all_emails = []

    print(f"[Шаг] Найдено {len(messages)} писем")

    for uid in messages:
        message_data = mail.fetch([uid], ['RFC822'])
        raw_email = message_data[uid][b'RFC822']
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')

        email_body = extract_email_body(msg)

        all_emails.append({
            'id': uid,
            'subject': subject,
            'body': email_body
        })

    print(f"[Шаг] Все письма успешно получены")
    return all_emails

def extract_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
    else:
        return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8')

def create_draft(reply_text, original_email, mail):
    """Создает черновик письма и сохраняет его на сервере."""
    print(f"[Шаг] Создание черновика для ответа на письмо...")

    # Формируем MIME сообщение для черновика с указанием кодировки UTF-8
    msg = MIMEText(reply_text, _charset='utf-8')  # Указываем кодировку UTF-8
    msg['Subject'] = "Re: " + original_email[b'ENVELOPE'].subject.decode('utf-8')
    msg['From'] = USERNAME  # Используем переменную username
    msg['To'] = f"{original_email[b'ENVELOPE'].from_[0].mailbox.decode('utf-8')}@{original_email[b'ENVELOPE'].from_[0].host.decode('utf-8')}"

    # Печатаем текст черновика
    print(f"Текст черновика:\n{reply_text}")

    # Сохраняем черновик на сервере в папке "Черновики"
    try:
        # Кодируем сообщение в байты с использованием UTF-8
        raw_msg = msg.as_bytes()
        mail.append('Черновики', raw_msg, flags=['\\Draft'], msg_time=None)
        print("[Шаг] Черновик успешно сохранен в папке 'Черновики'")
    except Exception as e:
        print(f"[Ошибка] Не удалось сохранить черновик: {e}")

def interact_stream(user_id, data, mail, email_id):
    url = f"https://general-runtime.voiceflow.com/v2/project/{PROJECT_ID}/user/{user_id}/interact/stream"

    headers = {
        'Accept': 'text/event-stream',
        'Authorization': VOICEFLOW_API_KEY,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data, stream=True)

    if response.status_code == 200:
        print("Connected to stream, receiving data...\n")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data:"):
                    try:
                        parsed_data = json.loads(decoded_line[6:])
                        process_stream_data(parsed_data, mail, email_id)
                    except json.JSONDecodeError:
                        print(f"Unable to parse: {decoded_line}")
    else:
        print(f"Error: {response.status_code}")

def process_stream_data(data_re, mail, email_id):
    """Обрабатывает ответ от ИИ-агента и вызывает действия."""
    print("[Шаг] Обработка данных от ИИ-агента...")

    if "payload" in data_re and "slate" in data_re["payload"]:
        slate_content = data_re["payload"]["slate"]["content"]

        spam_detected = False  # Флаг для отслеживания наличия спама

        for block in slate_content:
            for child in block['children']:
                message_text = child['text']
                print(message_text)

                if "Спам" in message_text:
                    spam_detected = True
                    print("[Шаг] Обнаружено сообщение 'Спам'. Выполняется пометка письма как спам...")
                    mark_as_spam(mail, email_id)

                # Если спам не обнаружен, создаем черновик письма
                if not spam_detected:
                    try:
                        original_mail = mail.fetch(email_id, ['ENVELOPE'])[email_id]
                        create_draft(message_text, original_mail, mail)  # Создаем черновик с текстом последнего сообщения
                    except Exception as e:
                        print(f"[Ошибка] Не удалось получить оригинальное письмо: {e}")

def mark_as_spam(mail, email_id):
    print(f"[Шаг] Пометка письма с ID {email_id} как спам...")
    mail.move(email_id, "Спам")
    print(f"[Шаг] Письмо с ID {email_id} перемещено в папку 'Спам'")

# Основная логика
data = {
    "action": {
        "type": "launch"
    }
}

def main():
    user_id = "your_user_id_here"

    mail = connect_to_mail()
    all_emails = get_all_emails(mail)

    for email_data in all_emails:
        text_mail = f"- ID: {email_data['id']}, Тема: {email_data['subject']}"
        email_id = email_data['id']

        data_text = {
            "action": {
                "type": "text",
                'payload': f'{text_mail}'
            }
        }

        interact_stream(user_id, data_text, mail, email_id)

if __name__ == '__main__':
    main()