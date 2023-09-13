# bicycle-predict
```bash
$ git clone https://github.com/8Dion8/bicycle-predict.git
$ cd bicycle-predict
$ docker compose build && docker compose up
```
Теперь: 
* Pаходим на http://localhost:9100/
* Cоздаем bucket с названием modelbucket
* Cоздаем ключи доступа. ID и SECRET нужно записать в `.env`, примеры уже записаны.
```bash
$ docker compose down && docker compose build && docker compose up
```
Доступные порты:
* `http://localhost:9100/` - MinIO
* `http://localhost:8080/` - Airflow
* `http://localhost:5000/` - MLflow

После запуска `main.dag` в Airflow будет доступен еще `http://localhost:3000/` на котором можно протестировать модель в BentoML



