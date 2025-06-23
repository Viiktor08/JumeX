FROM python:3.11-slim

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y libmariadb-dev gcc curl

# Instala wait-for-it
RUN curl -o /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

# Copia el código antes de instalar paquetes (buenas prácticas de cache)
COPY . /app

# Instala todas las dependencias de Python
RUN pip install --no-cache-dir \
    flask \
    flask_sqlalchemy \
    flask_cors \
    flask_restful \
    flask_praetorian \
    requests \
    mariadb \
    google-generativeai

# Usa wait-for-it como entrypoint
ENTRYPOINT ["wait-for-it.sh", "mariadb:3306", "--timeout=30", "--", "python", "app.py"]

