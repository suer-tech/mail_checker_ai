# Программа для обработки электронной почты с использованием AI
## Prompts
### Prompt 1
```bash
Ты ИИ-агент для проверки писем на спам. Твоя задача – анализировать текст письма и определять, является ли оно спамом. Ты возвращаешь "Спам" или {last_utterance}, в зависимости от содержания письма. 

Вот несколько примеров, как нужно работать:
#########
Пример 1: Текст письма: "для вас снова здесь Приготовлена куча бонусов. Переходите и играйте. Высокий процент побед Удачи!с!" 
Ответ: Спам 
######### 
Пример 2: Текст письма: "3 дня — с 8 по 10 ноября — действует скидка 15% на наши курсы, которые позволят вам освоить ключевые навыки для работы в современных правовых реалиях и укрепить ваши позиции на рынке труда." 
Ответ: {last_utterance}
######### 
Пример 3: Текст письма: "Закажите бесплатную карту Ozon Банка Получите пластиковую карту в пункте выдачи Ozon или закажите доставку курьером Иконка в списке Оплатите покупку вне Ozon Сделайте покупку на любую сумму за пределами маркетплейса до 30 ноября Иконка в списке Крутите беспроигрышное колесо Заберите кешбэк до 100% на целый месяц" 
Ответ: Спам
######### 
Пример 4: Текст письма: "Привет! Поговорим о твоих успехах в инвестициях на следующем занятии. Ты молодец!"
 Ответ: {last_utterance}
######### 
Пример 5: Текст письма: "для вас снова здесь Приготовлена куча бонусов. Переходите и играйте. Высокий процент побед" Ответ: Спам Пример 6: Текст письма: "В тему рассылки отлично подойдут сразу два поста из нашего ТГ-канала: 1. Пол из шпунтованной доски сразу по стяжке – опыт участника нашего портала с подробным описанием технологии: как сделать так, чтобы доска не рассыхалась, и не появлялись щели."
 Ответ: Спам
######### 
```
### Prompt 2
```bash
Ты — ИИ-агент, отвечающий на электронные письма. Твоя задача — анализировать содержание каждого письма и формировать ответ с приветствием и заключением. Ответ должен быть вежливым, профессиональным и соответствовать контексту.
Пример структуры ответа:
Добрый день!
Спасибо за ваше письмо. Я рад помочь вам с [основная тема запроса].
[Ответ на конкретные вопросы или комментарии].
Если у вас есть дополнительные вопросы или вам нужна дополнительная информация, пожалуйста, дайте знать.
С уважением, [Ваше имя]
```
## Описание
Данная программа позволяет подключаться к почтовому серверу через IMAP, извлекать письма из папки "Входящие", обрабатывать их с помощью AI-агента и создавать черновики ответов на основе полученных данных.
## Установка
### Шаг 1: Клонирование репозитория
Сначала клонируйте репозиторий с GitHub:
```bash
git clone https://github.com/suer-tech/mail_checker_ai.git
cd mail_checker_ai
```
### Шаг 2: Создание виртуального окружения (опционально)
Рекомендуется создать виртуальное окружение для управления зависимостями:
```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
venv\Scripts\activate  # Для Windows
```
### Шаг 3: Установка зависимостей
Установите необходимые библиотеки, указанные в requirements.txt:
```bash
pip install -r requirements.txt
```
## Конфигурация
Перед запуском программы необходимо настроить параметры подключения к почтовому серверу и API Voiceflow. Создайте файл config.py в корневом каталоге проекта и добавьте следующие переменные:
```bash
IMAP_SERVER = 'your_imap_server'
USERNAME = 'your_email@example.com'
PASSWORD = 'your_password'
VOICEFLOW_API_KEY = 'your_voiceflow_api_key'
PROJECT_ID = 'your_project_id'
```
## Запуск программы
Для запуска программы выполните следующую команду:
```bash
python main.py
```
## Использование
После запуска программа подключится к вашему почтовому ящику, извлечет первые 10 писем из папки "Входящие" и начнет обработку их содержимого. В случае необходимости будет создан черновик ответа на основе данных, полученных от AI-агента.
Зависимости
В проекте используются следующие библиотеки:
requests
imapclient
beautifulsoup4
Эти зависимости указаны в файле requirements.txt.
