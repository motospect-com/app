# Użyj oficjalnego obrazu Python
FROM python:3.9-slim

# Dodaj ścieżkę do zainstalowanych pakietów do PATH
ENV PATH="/root/.local/bin:${PATH}"

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj pliki z zależnościami i zainstaluj je
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Skopiuj resztę kodu aplikacji
COPY . .

# FastAPI domyślnie działa na porcie 8000
EXPOSE 8000
