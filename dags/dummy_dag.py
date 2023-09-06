from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='test_bash.dag',
    start_date=datetime(2023, 9, 5),
    schedule_interval=None
) as dag:
    helloworld = BashOperator(
        task_id='print_hello_world',
        bash_command='echo HelloWorld'
    )