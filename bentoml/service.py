import bentoml
from bentoml.io import PandasDataFrame
import mlflow
import pandas as pd
import numpy as np

# Get trained model
experiment_id = mlflow.get_experiment_by_name("bicycle").experiment_id
run_id = list(mlflow.search_runs(experiment_ids=[experiment_id])['run_id'])[-1] # last trained model
logged_model_uri = f"s3://modelbucket/{experiment_id}/{run_id}/artifacts/bicycle_predict_model/"
bento_model_runner = bentoml.mlflow.import_model('bicycle_predict_model', logged_model_uri).to_runner()


svc = bentoml.Service("bicycle_predict_service", runners = [bento_model_runner])

# Get sample data for IO description
df = pd.read_csv("/workdir/test.csv")
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.set_index(df.datetime)
df.drop('datetime', axis=1, inplace=True)
df['hour'] = np.int64(df.index.hour)
df['day'] = np.int64(df.index.day)
df['month'] = np.int64(df.index.month)

input_spec = PandasDataFrame.from_sample(df.sample(1))




@svc.api(input=input_spec, output=bentoml.io.NumpyNdarray(dtype=np.int64))
def predict(input_arr):
    return bento_model_runner.predict.run(input_arr)