from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'koinstrap',
    'depends_on_past': False,
    'start_date': datetime(2026, 3, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='koinstrap_market_pipeline',
    default_args=default_args,
    description='market_data_pipeline: ingest - metrics - analysis - confidence',
    schedule_interval='*/5 * * * *', 
    catchup=False,
) as dag:

    # Use ABSOLUTE paths to avoid "File Not Found" errors in Airflow
    base_dir = '/home/falamfar/koinstrap_platform/projects/koinstrap'
    python_bin = f'{base_dir}/airflow_venv_311_py311/bin/python3'
    scripts_dir = f'{base_dir}/scripts'

    ingest_task = BashOperator(
        task_id='coingecko_ingest',
        bash_command=f'{python_bin} {scripts_dir}/ingest_coingecko_v1.py'
    )

    compute_metrics_task = BashOperator(
        task_id='compute_metrics',
        bash_command=f'{python_bin} {scripts_dir}/compute_metrics.py'
    )

    analysis_task = BashOperator(
        task_id='analysis',
        bash_command=f'{python_bin} {scripts_dir}/analyze_crypto_metrics.py'
    )

    confidence_task = BashOperator(
        task_id='compute_confidence',
        bash_command=f'{python_bin} {scripts_dir}/compute_confidence_score.py'
    )

    ml_feature_task = BashOperator(
        task_id='ml_feature_task',
        bash_command=f'{python_bin} {scripts_dir}/populate_ml_features.py'
    ) # Fixed the missing comma here by closing the object properly

    # Define the workflow
    ingest_task >> compute_metrics_task >> analysis_task >> confidence_task >> ml_feature_task