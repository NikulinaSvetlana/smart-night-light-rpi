FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

ARG INSTALL_RPI_GPIO=false
RUN if [ "$INSTALL_RPI_GPIO" = "true" ]; then pip install --no-cache-dir RPi.GPIO; fi

COPY app /app/app

EXPOSE 8443

CMD ["python", "-m", "app.main"]
