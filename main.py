import os
import requests
import json
from dotenv import load_dotenv

from mail_process import connect_to_mail, get_all_emails

load_dotenv()

# Получение ключа API Voiceflow и Project ID
VOICEFLOW_API_KEY = os.getenv('VOICEFLOW_API_KEY')
PROJECT_ID = os.getenv('PROJECT_ID')

# Основная логика
def interact_stream(user_id, data, mail, email_id):
    url = f"https://general-runtime.voiceflow.com/v2/project/{PROJECT_ID}/user/{user_id}/interact/stream"

    headers = {
        'Accept': 'text/event-stream',
        'Authorization': VOICEFLOW_API_KEY,
        'Content-Type': 'application/json'
    }

    # Отправляем POST запрос с параметрами и включаем поток (stream=True)
    response = requests.post(url, headers=headers, json=data, stream=True)

    if response.status_code == 200:
        print("Connected to stream, receiving data...\n")
        for line in response.iter_lines():
            if line:
                # Декодируем строку
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data:"):
                    # Извлекаем полезные данные после 'data:'
                    try:
                        parsed_data = json.loads(decoded_line[6:])
                        process_stream_data(parsed_data, mail, email_id)
                    except json.JSONDecodeError:
                        print(f"Unable to parse: {decoded_line}")
    else:
        print(f"Error: {response.status_code}")


def process_stream_data(data_re, mail, email_id):
    """Обрабатывает ответ от ИИ-агента и вызывает действия, если необходимо."""
    print("[Шаг] Обработка данных от ИИ-агента...")
    if "payload" in data_re and "slate" in data_re["payload"]:
        slate_content = data_re["payload"]["slate"]["content"]
        print("---- Сообщение от Voiceflow ----")
        for block in slate_content:
            for child in block['children']:
                message_text = child['text']
                print(message_text)

                # Проверка на наличие слова "Спам" в сообщении
                if "Спам" in message_text:
                    print("[Шаг] Обнаружено сообщение 'Спам'. Выполняется пометка письма как спам...")
                    mark_as_spam(mail, email_id)
        print("-------------------------------\n")


def mark_as_spam(mail, email_id):
    """Помечает письмо как спам."""
    print(f"[Шаг] Пометка письма с ID {email_id} как спам...")
    mail.move(email_id, "Спам")  # Перемещаем письмо в папку "Спам"
    print(f"[Шаг] Письмо с ID {email_id} перемещено в папку 'Спам'")


# Данные для взаимодействия
data = {
    "action": {
        "type": "launch"
    }
}


# Использование
def main():
    user_id = "your_user_id_here"  # Замените на реальный user_id

    mail = connect_to_mail()
    all_emails = get_all_emails(mail)
    for email_data in all_emails:
        text_mail = f"- ID: {email_data['id']}, Тема: {email_data['subject']}"
        email_id = email_data['id']  # Извлекаем ID письма для пометки спамом

        data_text = {
            "action": {
                "type": "text",
                'payload': f'{text_mail}'
            }
        }

        # Передаем mail и email_id в функцию обработки данных
        interact_stream(user_id, data_text, mail, email_id)
        process_stream_data(data_text, mail, email_id)

if __name__ == '__main__':
    main()
