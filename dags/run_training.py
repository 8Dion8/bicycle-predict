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


def train_time_series_with_folds(model, df, lag, horizon=24*7):

    # Load and create if necessary MLflow experiment
    try:
        experiment_id = mlflow.create_experiment("bicycle")
    except:
        experiment_id = mlflow.get_experiment_by_name("bicycle").experiment_id

    with mlflow.start_run(experiment_id=experiment_id, run_name='Bicycle Run'):
        X = df.drop('count', axis=1)
        y = df['count']

        # take last week of the dataset for validation
        X_train, X_test = X.iloc[:-horizon, :], X.iloc[-horizon:, :]
        y_train, y_test = y.iloc[:-horizon], y.iloc[-horizon:]

        # create, train and do inference of the model
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        signature = mlflow.models.infer_signature(X_train, predictions)

        # calculate MAE
        mae = np.round(mean_absolute_error(y_test, predictions), 3)
        mlflow.log_metric("mae", mae)
        mlflow.log_param("data lag", lag)

        logged_model = mlflow.sklearn.log_model(
            model,
            "bicycle_predict_model",
            registered_model_name="GBMBicycleDemandPredictor",
            signature=signature
        )





def train():
    df = pd.read_csv("/workdir/train.csv")

    # Переведём datetime в более точные атрибуты - по часам, дням, месяцам
    df['datetime'] = pd.to_datetime(df['datetime'])
    # set datetime as index
    df = df.set_index(df.datetime)
    # drop datetime column
    df.drop('datetime', axis=1, inplace=True)

    # create hour, day and month variables from datetime index
    df['hour'] = np.int64(df.index.hour)
    df['day'] = np.int64(df.index.day)
    df['month'] = np.int64(df.index.month)

    # drop casual and registered columns
    df.drop(['casual', 'registered'], axis=1, inplace=True)

    mlflow.lightgbm.autolog()

    # Initial train
    model = LGBMRegressor()
    train_time_series_with_folds(model, df, 0)

    # create 1 week lag variable by shifting the target value for 1 week
    df['count_prev_week_same_hour'] = df['count'].shift(24*7)

    # drop NaNs after feature engineering
    df.dropna(how='any', axis=0, inplace=True)

    # Train with 1 week lag
    model = LGBMRegressor()
    train_time_series_with_folds(model, df, 7)


main_dag = DAG(
    dag_id='main.dag',
    start_date=datetime(2023, 9, 5),
    schedule_interval=None
)

t1 = PythonOperator(
    task_id="train_model",
    python_callable=train,
    provide_context=True,
    dag=main_dag
)

t2 = BashOperator(
    task_id="bentoml_serve",
    bash_command="bentoml serve service:svc -p 3605",
    cwd="/workdir",
    dag=main_dag
)

t1 >> t2
