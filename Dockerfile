FROM apache/airflow:2.7.0

WORKDIR /workdir

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         python-dev libgomp1 libpq-dev gcc git \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt .
COPY train.csv .
COPY test.csv .
# COPY bentoml/bentofile.yaml .
COPY bentoml/service.py .

RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r requirements.txt --use-deprecated=legacy-resolver
