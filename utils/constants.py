import os

# Shopify credentials - READ FROM ENVIRONMENT VARIABLES
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

# Output path for CSV files
OUTPUT_PATH = '/opt/airflow/output'

# AWS Configuration - READ FROM ENVIRONMENT VARIABLES
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Athena Configuration
ATHENA_DATABASE = os.getenv('ATHENA_DATABASE', 'shopify_data')
ATHENA_OUTPUT_LOCATION = f's3://{S3_BUCKET_NAME}/athena-results/'
