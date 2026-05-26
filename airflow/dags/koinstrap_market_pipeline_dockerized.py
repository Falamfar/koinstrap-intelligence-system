from airflow import DAG 
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from docker.types import Mount 
import os 

# --- PRODUCTION SECRETS ---
# Airflow fetches this from its internal vault. 
# Safe, encrypted, and not visible in your code.
DB_PASS = os.getenv('PG_PASSWORD', 'fallback_if_missing')


GROQ_KEY = Variable.get("koinstrap_groq_api_key", default_var="missing")

docker_common_args = { 
    'image': 'koinstrap-api:latest',
    'docker_url': 'unix://var/run/docker.sock',
    'dns': ['8.8.8.8', '8.8.4.4'],
    'network_mode': 'koinstrap_default',
    'auto_remove': True,
    'mount_tmp_dir': False,
    'tty': True, # Explicit Logging: This streams container output to the Airflow UI
    'mounts': [
        Mount(
            source='/home/falamfar/koinstrap_platform/projects/koinstrap/scripts',
            target='/app/scripts',
            type='bind'
        )
    ],
    'environment': {
        'PYTHONUNBUFFERED': '1', # Explicit Logging: Forces real-time log streaming
        'PG_HOST': os.getenv('PG_HOST', 'koinstrap_db'),
        'PG_NAME': os.getenv('PG_NAME', 'koinstrap_ai'),
        'PG_USER': os.getenv('PG_USER', 'koinstrap_admin'),
        'PG_PORT': os.getenv('PG_PORT', '5432'),
        'DEBUG_PWD': DB_PASS,
        'PG_PASSWORD': DB_PASS, 
        'GROQ_API_KEY': GROQ_KEY, # This drops the key straight into the container's environment!
    }
}

default_args = {
    'owner': 'falamfar',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}    

with DAG(
    'konstrap_market_pipeline',
    default_args=default_args, 
    description='core market pipeline running every 5 minutes',
    schedule_interval='*/5 * * * *',
    start_date=datetime(2026, 4, 1), 
    catchup=False,
) as dag: 
    task_ingest = DockerOperator(task_id='ingest_coingecko', command='python3 /app/scripts/ingest_coingecko_v1.py', **docker_common_args)
    task_metrics = DockerOperator(task_id='compute_metrics', command='python3 /app/scripts/compute_metrics.py', **docker_common_args)  
    task_analyze = DockerOperator(task_id='analyze_crypto', command='python3 /app/scripts/analyze_crypto_metrics.py', **docker_common_args)
    task_confidence = DockerOperator(task_id='compute_confidence', command='python3 /app/scripts/compute_confidence_score.py', **docker_common_args)
    task_ml_features = DockerOperator(task_id='populate_ml_features', command='python3 /app/scripts/populate_ml_features.py', **docker_common_args)
    task_signal_factory = DockerOperator(task_id='signal_factory', command='python3 /app/scripts/koinstrap_signal_factory.py', **docker_common_args)

    task_ingest >> task_metrics >> task_analyze >> task_confidence >> task_ml_features >> task_signal_factory