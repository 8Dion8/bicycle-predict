from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime


create_dag = DAG(
    dag_id='create_bucket.dag',
    start_date=datetime(2023, 9, 5),
    schedule_interval=None
)

t1 = BashOperator(
    task_id="set_alias",
    bash_command="mc alias s local http://minio:3601",
    dag=create_dag
)

t2 = BashOperator(
    task_id="create_bucket",
    bash_command="mc mb local/modelbucket admin password",
    dag=create_dag
)

t1 >> t2