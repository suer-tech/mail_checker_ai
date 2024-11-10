import json
from email.mime.text import MIMEText
import requests
from imapclient import IMAPClient
import email
from email.header import decode_header
from config import IMAP_SERVER, USERNAME, PASSWORD, VOICEFLOW_API_KEY, PROJECT_ID
from bs4 import BeautifulSoup


def connect_to_mail():
    print("[Шаг] Подключение к почте...")
    mail = IMAPClient(IMAP_SERVER, use_uid=True, ssl=True)
    mail.login(USERNAME, PASSWORD)
    print("[Шаг] Успешное подключение к почте")
    return mail


def get_first_n_emails(mail, n=10):
    print(f"[Шаг] Получение первых {n} писем из папки 'Входящие'...")
    mail.select_folder("INBOX")
    messages = mail.search(['ALL'])

    # Ограничиваем количество загружаемых писем до n
    messages = messages[:n]
    all_emails = []

    print(f"[Шаг] Найдено {len(messages)} писем")

    for uid in messages:
        message_data = mail.fetch([uid], ['RFC822'])
        raw_email = message_data[uid][b'RFC822']
        msg = email.message_from_bytes(raw_email)

        subject = decode_subject(msg.get("Subject"))
        email_body = extract_email_body(msg)

        all_emails.append({
            'id': uid,
            'subject': subject,
            'body': email_body
        })

    print(f"[Шаг] Первые {n} письма успешно получены")
    return all_emails


def decode_subject(subject_header):
    if subject_header is not None:
        decoded_subjects = decode_header(subject_header)
        subject_parts = []
        for subject, encoding in decoded_subjects:
            if isinstance(subject, bytes):
                if encoding is not None:
                    try:
                        subject_parts.append(subject.decode(encoding))
                    except LookupError:
                        subject_parts.append(subject.decode('utf-8', errors='ignore'))
                else:
                    subject_parts.append(subject.decode('utf-8', errors='ignore'))
            else:
                subject_parts.append(subject)
        return ''.join(subject_parts)
    else:
        return "Без темы"


def extract_email_body(msg):
    """Извлекает текстовое содержимое письма."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                body += safe_decode(part.get_payload(decode=True), part.get_content_charset())
            elif content_type == "text/html" and "attachment" not in content_disposition:
                html_body = safe_decode(part.get_payload(decode=True), part.get_content_charset())
                body += html_to_text(html_body)  # Преобразуем HTML в текст

    else:  # Если не многосоставное сообщение
        body += safe_decode(msg.get_payload(decode=True), msg.get_content_charset())

    return body.strip()


def html_to_text(html):
    """Преобразует HTML в текст (простой вариант)."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


def safe_decode(payload, charset):
    """Безопасное декодирование с обработкой ошибок."""
    if charset is None:  # Если кодировка не указана
        charset = 'utf-8'  # Используем UTF-8 по умолчанию

    try:
        return payload.decode(charset)
    except (LookupError, UnicodeDecodeError):
        return payload.decode('ISO-8859-1', errors='ignore')


def create_draft(reply_text, original_email, mail):
    """Создает черновик письма и сохраняет его на сервере."""
    print(f"[Шаг] Создание черновика для ответа на письмо...")

    # Убедитесь, что reply_text содержит только текст ответа
    msg = MIMEText(reply_text.strip(), _charset='utf-8')
    msg['Subject'] = "Re: " + original_email[b'ENVELOPE'].subject.decode('utf-8')
    msg['From'] = USERNAME
    msg[
        'To'] = f"{original_email[b'ENVELOPE'].from_[0].mailbox.decode('utf-8')}@{original_email[b'ENVELOPE'].from_[0].host.decode('utf-8')}"

    print(f"Текст черновика:\n{reply_text.strip()}")

    try:
        raw_msg = msg.as_bytes()
        mail.append('Черновики', raw_msg, flags=['\\Draft'], msg_time=None)
        print("[Шаг] Черновик успешно сохранен в папке 'Черновики'")
    except Exception as e:
        print(f"[Ошибка] Не удалось сохранить черновик: {e}")


def process_stream_data(data_re, mail, email_id):
    """Обрабатывает ответ от ИИ-агента и вызывает действия."""
    print("[Шаг] Обработка данных от ИИ-агента...")

    if email_id not in last_responses_by_email_id:
        last_responses_by_email_id[email_id] = None  # Инициализируем значение для данного письма

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

                # Сохраняем только последний ответ для данного письма
                last_responses_by_email_id[email_id] = message_text

        # Если спам не обнаружен и есть последний ответ
        if not spam_detected and last_responses_by_email_id[email_id]:
            combined_response_text = last_responses_by_email_id[email_id]  # Берем только последний ответ

            try:
                original_mail = mail.fetch(email_id, ['ENVELOPE'])[email_id]
                create_draft(combined_response_text.strip(), original_mail,
                             mail)  # Создаем черновик с последним текстом ответа
            except Exception as e:
                print(f"[Ошибка] Не удалось получить оригинальное письмо: {e}")



def interact_stream(user_id, data, mail, email_id):
    url = f"https://general-runtime.voiceflow.com/v2/project/{PROJECT_ID}/user/{user_id}/interact/stream"

    headers = {
        'Accept': 'text/event-stream',
        'Authorization': VOICEFLOW_API_KEY,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data, stream=True)

    if response.status_code == 200:
        print("Подключено к потоку, получение данных...\n")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data:"):
                    try:
                        parsed_data = json.loads(decoded_line[6:])
                        process_stream_data(parsed_data, mail, email_id)
                    except json.JSONDecodeError:
                        print(f"Не удалось разобрать: {decoded_line}")
    else:
        print(f"Ошибка: {response.status_code}")


# Словарь для хранения последнего ответа на каждое письмо
last_responses_by_email_id = {}


def process_stream_data(data_re, mail, email_id):
    """Обрабатывает ответ от ИИ-агента и вызывает действия."""
    print("[Шаг] Обработка данных от ИИ-агента...")
    if email_id not in last_responses_by_email_id:
        last_responses_by_email_id[email_id] = []  # Измените на список

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

                # Сохраняем все ответы
                last_responses_by_email_id[email_id].append(message_text)

        # Если спам не обнаружен и есть ответы
        if not spam_detected and last_responses_by_email_id[email_id]:
            combined_response_text = "\n".join(last_responses_by_email_id[email_id])  # Объединяем все ответы
            try:
                original_mail = mail.fetch(email_id, ['ENVELOPE'])[email_id]
                create_draft(combined_response_text.strip(), original_mail, mail)  # Создаем черновик с полным текстом
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

    # Получаем только первые 10 писем
    all_emails = get_first_n_emails(mail)  # Изменено на новую функцию

    for email_data in all_emails:
        text_mail = f"{email_data['body']}"  # Отправляем только тело письма без ID и темы
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