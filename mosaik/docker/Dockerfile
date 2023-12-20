FROM python:3.9.1

RUN apt-get update  && apt-get install -y --no-install-recommends build-essential swig libsundials-dev libboost-all-dev && apt-get purge -y --auto-remove && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

CMD tail -f /dev/null