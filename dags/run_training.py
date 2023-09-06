from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.decorators import task
from datetime import datetime
import mlflow
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error
import numpy as np

MLFLOW_CONN_ID = "mlflow_default"

def train_time_series_with_folds(model, df, horizon=24*7):
    try:
        experiment_id = mlflow.create_experiment("bicycle")
    except:
        experiment_id = mlflow.get_experiment_by_name("bicycle").experiment_id
    
    with mlflow.start_run(experiment_id=experiment_id, run_name='Bicycle Experiment'):
        X = df.drop('count', axis=1)
        y = df['count']
        
        #take last week of the dataset for validation
        X_train, X_test = X.iloc[:-horizon,:], X.iloc[-horizon:,:]
        y_train, y_test = y.iloc[:-horizon], y.iloc[-horizon:]
        
        #create, train and do inference of the model
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        signature = mlflow.models.infer_signature(X_train, predictions)
        
        #calculate MAE
        mae = np.round(mean_absolute_error(y_test, predictions), 3)
        mlflow.log_metric("mae", mae)

        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="GBMBicycleDemandPredictor",
            signature=signature
        )

train_dag = DAG(
    dag_id='run_train.dag',
    start_date=datetime(2023, 9, 5),
    schedule_interval=None
)



def train():

    #mlflow.set_tracking_uri("s3://rL6cri6U8RcVgGc9F94K:q4ZoKJmO74pbgOeL6GUF3ivoI8C4OVmW8TgfD1Mp@localhost:9000")

    #mlflow.set_tracking_uri(mlflow.get_tracking_uri())

    df = pd.read_csv("/workdir/train.csv")
    # ------------------------------------------------------------------------
    # Переведём datetime в более точные атрибуты - по часам, дням, месяцам
    # ------------------------------------------------------------------------
    df['datetime'] = pd.to_datetime(df['datetime'])
    #set datetime as index
    df = df.set_index(df.datetime)

    #drop datetime column
    df.drop('datetime', axis=1, inplace=True)

    #create hour, day and month variables from datetime index
    df['hour'] = df.index.hour
    df['day'] = df.index.day
    df['month'] = df.index.month

    #drop casual and registered columns
    df.drop(['casual', 'registered'], axis=1, inplace=True)

    #create 1 week lag variable by shifting the target value for 1 week
    df['count_prev_week_same_hour'] = df['count'].shift(24*7)

    #drop NaNs after feature engineering
    df.dropna(how='any', axis=0, inplace=True)
    model = LGBMRegressor(random_state=42)

    train_time_series_with_folds(model, df)

t1 = PythonOperator(
    task_id = "train_model", 
    python_callable = train,
    provide_context = True,
    dag=train_dag
)


t1