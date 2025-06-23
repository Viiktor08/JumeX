FROM python:3.11-slim

WORKDIR /app

# Instala dependencias del sistema para mariadb, compilar y curl
RUN apt-get update && apt-get install -y libmariadb-dev gcc curl

# Instala wait-for-it
RUN curl -o /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

# Copia todos los archivos del microservicio
COPY . /app

# Instala las librerías necesarias
RUN pip install --no-cache-dir \
    flask \
    flask_sqlalchemy \
    flask_praetorian \
    flask_cors \
    requests \
    nvdlib \
    mariadb

# Usa wait-for-it como entrypoint
ENTRYPOINT ["wait-for-it.sh", "mariadb:3306", "--timeout=30", "--", "python", "app.py"]
