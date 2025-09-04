# Firmware mock publisher container
FROM python:3.11-slim

WORKDIR /app

# Install deps
RUN pip install --no-cache-dir paho-mqtt numpy

COPY publisher.py /app/publisher.py

ENV MQTT_BROKER_HOST=mosquitto \
    MQTT_BROKER_PORT=1883 \
    MQTT_BASE_TOPIC=motospect/v1 \
    PUBLISH_HZ=1

CMD ["python", "-u", "/app/publisher.py"]
