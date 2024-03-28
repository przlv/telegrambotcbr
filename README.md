Бот для совещаний

Чтобы запустить необходимо установить все зависимости и создать конфиг.

Создать файл config.py:<br />
TOKEN = <Токен телеграмм бота><br />
SECRET_CODE = <Секретный код для бота><br />

Создать папку data и поместить туда ExcelFile под именем data.xlsx<br />
С полями: telegram_id |	name_user |	hotel |	arrival | departure | maintainer<br />
<br />

😊 Желательно создать виртуальное окружение 😊<br />
python -m venv venv

После установить зависимости<br />
pip install -r requirements.txt

Запускать main.py либо через IDE, либо в cmd:<br />
python .path/main.py


Дерево проекта:<br />
app/<br />
├── __init__.py<br />
├── patterns.py<br />
├── telegramBot.py<br />
├── data/<br />
│   └── data.xlsx<br />
├── venv/<br />
├── .gitignore<br />
├── config.py<br />
├── main.py<br />
├── README.md<br />
└── requirements.txt<br />
