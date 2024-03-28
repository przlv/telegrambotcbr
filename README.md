Бот для совещаний

Чтобы запустить необходимо установить все зависимости и создать конфиг.

Создать файл config.py:
TOKEN = <Токен телеграмм бота>
SECRET_CODE = <Секретный код для бота>

Создать папку data и поместить туда ExcelFile под именем data.xlsx
С полями: telegram_id |	name_user |	hotel |	arrival | departure | maintainer


😊 Желательно создать виртуальное окружение 😊
python -m venv venv

После установить зависимости
pip install -r requirements.txt

Запускать main.py либо через IDE, либо в cmd:
python .path/main.py
