from datetime import datetime, timedelta 
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner':'koinstrap',
    'depends_on_past':False,
    'start_date':datetime(2026, 3, 3),
    'retries':1,
    'retry_delay':timedelta(minutes=2)
}

dag = DAG(
    dag_id='reddit_social_sentiment',
    default_args=default_args,
    description='Ingest Reddit social sentiment data',
    schedule_interval='*/15 * * * *',
    catchup=False
)

# Task 1 (scrape reddit)
reddit_task = BashOperator(
    task_id='reddit_task',
    bash_command=(

        # Activate the correct Python virtual environment
        'source ~/koinstrap_platform/projects/koinstrap/airflow_venv_311_py311/bin/activate && '
        # Run the Reddit script
        'python3 /home/falamfar/koinstrap_platform/projects/koinstrap/scripts/reddit_ingest.py'
    ),
    dag=dag
) 

reddit_task 




