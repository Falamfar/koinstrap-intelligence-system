from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from docker.types import Mount
import os 

DB_PASS = os.getenv('PG_PASSWORD', 'fallback_if_missing')

docker_common_args = {
    'image': 'koinstrap-api:latest',
    'docker_url': 'unix://var/run/docker.sock',
    'dns': ['8.8.8.8', '8.8.4.4'],
    'network_mode': 'koinstrap_default',
    'auto_remove': True,
    'mount_tmp_dir': False,
    'tty': True,

    'mounts': [
        Mount(
            source='/home/ubuntu/koinstrap-intelligence-system/scripts',
            target='/app/scripts',
            type='bind'
        )
    ],

    'environment': {
        'PYTHONUNBUFFERED': '1',
        'PG_HOST': os.getenv('PG_HOST', 'koinstrap_db'),
        'PG_NAME': os.getenv('PG_NAME', 'koinstrap_ai'),
        'PG_USER': os.getenv('PG_USER', 'koinstrap_admin'),
        'PG_PASSWORD': DB_PASS,
        'PG_PORT': os.getenv('PG_PORT', '5432'),
    }
}

default_args = {
    'owner': 'falamfar',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'koinstrap_social_sentiment_docker',
    default_args=default_args,
    schedule_interval='*/15 * * * *',
    start_date=datetime(2026, 4, 1),
    catchup=False,
) as dag:

    reddit_ingest = DockerOperator(
        task_id='reddit_ingest',
        command='python3 /app/scripts/reddit_ingest.py',
        **docker_common_args
    )
