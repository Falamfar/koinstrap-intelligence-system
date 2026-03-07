from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default settings for all tasks
default_args = {
    'owner': 'koinstrap',
    'depends_on_past': False,
    'start_date': datetime(2026, 3, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Define the DAG
with DAG(
    dag_id = 'koinstrap_market_pipeline',
    default_args=default_args,
    description = 'market_data_pipeline: ingest - metrics - analysis - confidence',
    schedule_interval = '*/5 * * * *', #every 5 miinutes
    catchup = False,
) as dag:

    venv_path = '~/koinstrap_platform/projects/koinstrap/airflow_venv_311_py311/bin/activate'
    scripts_path = '~/koinstrap_platform/projects/koinstrap/scripts'

    ingest_task = BashOperator(
        task_id = 'coingecko_ingest',
        bash_command = f'source {venv_path} && python3 {scripts_path}/ingest_coingecko_v1.py'
    )

    compute_metrics_task = BashOperator(
        task_id = 'compute_metrics',
        bash_command = f'source {venv_path} && python3 {scripts_path}/compute_metrics.py'
    )

    analysis_task = BashOperator(
        task_id = 'analysis',
        bash_command = f'source {venv_path} && python3 {scripts_path}/analyze_crypto_metrics.py'
    )

    confidence_task = BashOperator(
        task_id = 'compute_confidence',
        bash_command = f'source {venv_path} && python3 {scripts_path}/compute_confidence_score.py'
    )

    ingest_task >> compute_metrics_task >> analysis_task >> confidence_task

