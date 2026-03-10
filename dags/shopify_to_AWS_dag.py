"""
Airflow DAG: Shopify to AWS Pipeline
Set to runs weekly every Monday at 6:00 AM, you can change this below
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, '/opt/airflow')

from pipelines.Shopify_Pipeline_AWS import (
    shopify_orders_to_aws,
    shopify_products_to_aws,
    shopify_customers_to_aws,
    shopify_line_items_to_aws,
)


SALES_REPORT_QUERY ="""
        FROM product_views
        SHOW
            count AS product_view_count,
            product_id,
            variant_id
        SINCE -7d
        GROUP BY
            product_id,
            variant_id
        ORDER BY
            product_view_count DESC
        LIMIT 5000
    """

# Default arguments for the DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'shopify_to_aws_weekly',
    default_args=default_args,
    description='Weekly Shopify data sync to AWS S3 + Athena',
    schedule_interval='0 6 * * 1',  # Change weekly run here
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['shopify', 'aws', 'etl', 'weekly'],
)


def upload_orders(**context):
    """Task to upload orders to AWS"""
    print("Starting Orders upload...")
    s3_uri, table = shopify_orders_to_aws(
        days_back=30,  # Get last 30 days of orders
        limit=250,
        save_local=True
    )
    print(f"Orders uploaded: {table}")
    return {'s3_uri': s3_uri, 'table': table}


def upload_products(**context):
    """Task to upload products to AWS"""
    print("Starting Products upload...")
    s3_uri, table = shopify_products_to_aws(
        limit=250,
        save_local=True
    )
    print(f"Products uploaded: {table}")
    return {'s3_uri': s3_uri, 'table': table}


def upload_customers(**context):
    """Task to upload customers to AWS"""
    print("Starting Customers upload...")
    s3_uri, table = shopify_customers_to_aws(
        limit=250,
        save_local=True
    )
    print(f"Customers uploaded: {table}")
    return {'s3_uri': s3_uri, 'table': table}

def upload_line_items(**context):
    """Task to upload order line items to AWS"""
    print("Starting Line Items upload...")
    s3_uri, table = shopify_line_items_to_aws(
        days_back=30,
        limit=250,
        save_local=True
    )
    print(f"Line Items uploaded: {table}")
    return {'s3_uri': s3_uri, 'table': table}


def print_summary(**context):
    """Print pipeline summary"""
    ti = context['ti']

    orders_result = ti.xcom_pull(task_ids='upload_orders')
    products_result = ti.xcom_pull(task_ids='upload_products')
    customers_result = ti.xcom_pull(task_ids='upload_customers')

    print("\n" + "=" * 70)
    print("WEEKLY PIPELINE SUMMARY")
    print("=" * 70)
    print(f"\nOrders: {orders_result['table']}")
    print(f"Products: {products_result['table']}")
    print(f"Analytics: {customers_result['table']}")
    print("\n" + "=" * 70)


# Define tasks
task_upload_orders = PythonOperator(
    task_id='upload_orders',
    python_callable=upload_orders,
    dag=dag,
)

task_upload_products = PythonOperator(
    task_id='upload_products',
    python_callable=upload_products,
    dag=dag,
)

task_upload_customers = PythonOperator(
    task_id='upload_customers',
    python_callable=upload_customers,
    dag=dag,
)

task_upload_line_items = PythonOperator(
    task_id='upload_line_items',
    python_callable=upload_line_items,
    dag=dag,
)

task_summary = PythonOperator(
    task_id='print_summary',
    python_callable=print_summary,
    dag=dag,
)

# Set task dependencies
# Products and Orders can run in parallel, Analytics depends on Products
[task_upload_orders, task_upload_products, task_upload_customers, task_upload_line_items] >> task_summary