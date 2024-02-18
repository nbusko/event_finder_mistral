FROM python:3.9

RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean
RUN apt-get install -y \
    apt-utils \
    python3-pip \
    curl

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл requirements.txt в рабочую директорию
COPY requirements.txt .

# Устанавливаем необходимые зависимости из файла requirements.txt
RUN pip install -r requirements.txt

# Копируем файлы с исходным кодом приложения в рабочую директорию
COPY ./app .

# # Запускаем приложение при старте контейнера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]