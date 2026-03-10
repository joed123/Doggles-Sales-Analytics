"""
Shopify to AWS Pipeline (Updated with Line Items)
Extracts data from Shopify and loads to S3 + Athena for Power BI
"""

from etls.Shopify_Connect import connect_shopify
from etls.load import load_data_to_csv
from etls.load_to_aws import AWSDataLoader

from etls.Shopify_Get_Sales import (
    extract_orders,
    transform_order_data,
)

from etls.Shopify_Get_Inventory import (
    extract_products,
    transform_product_data,
)

from etls.Shopify_Get_Customers import (
    extract_customers,
    transform_customer_data,
)

from etls.Shopify_Get_Line_Items import (
    extract_line_items,
    transform_line_item_data,
)

from utils.constants import (
    SHOPIFY_STORE,
    SHOPIFY_ACCESS_TOKEN,
    OUTPUT_PATH,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME,
    ATHENA_DATABASE
)

import pandas as pd
from datetime import datetime


def shopify_orders_to_aws(days_back=7, limit=250, status='any', save_local=True):
    """
    Extract orders from Shopify and upload to AWS S3 + Athena

    Args:
        days_back: Number of days to look back for orders
        limit: Maximum number of orders to retrieve
        status: Order status filter ('any', 'open', 'closed', 'cancelled')
        save_local: Also save CSV locally

    Returns:
        tuple: (s3_uri, athena_table_name)
    """
    print("\n" + "=" * 70)
    print("SHOPIFY ORDERS → AWS PIPELINE")
    print("=" * 70)

    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    orders = extract_orders(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, days_back, limit, status)
    print(f"DEBUG: Extracted {len(orders)} orders")
    order_df = pd.DataFrame(orders)
    print(f"DEBUG: DataFrame shape: {order_df.shape}")
    order_df = transform_order_data(order_df)

    if save_local:
        file_path = f'{OUTPUT_PATH}/orders_latest.csv'
        load_data_to_csv(order_df, file_path)
        print(f"Local copy saved: {file_path}")

    aws_loader = AWSDataLoader(
        aws_access_key=AWS_ACCESS_KEY_ID,
        aws_secret_key=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
        bucket_name=S3_BUCKET_NAME
    )

    s3_uri, table_name = aws_loader.upload_dataframe_to_athena(
        df=order_df,
        table_name='shopify_orders',
        folder='shopify/orders',
        database_name=ATHENA_DATABASE
    )

    return s3_uri, table_name


def shopify_products_to_aws(limit=250, save_local=True):
    """
    Extract products from Shopify and upload to AWS S3 + Athena

    Args:
        limit: Maximum number of products to retrieve
        save_local: Also save CSV locally

    Returns:
        tuple: (s3_uri, athena_table_name)
    """
    print("\n" + "=" * 70)
    print("SHOPIFY PRODUCTS → AWS PIPELINE")
    print("=" * 70)

    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    products = extract_products(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, limit)
    product_df = pd.DataFrame(products)
    product_df = transform_product_data(product_df)

    if save_local:
        file_path = f'{OUTPUT_PATH}/products_latest.csv'
        load_data_to_csv(product_df, file_path)
        print(f"Local copy saved: {file_path}")

    aws_loader = AWSDataLoader(
        aws_access_key=AWS_ACCESS_KEY_ID,
        aws_secret_key=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
        bucket_name=S3_BUCKET_NAME
    )

    s3_uri, table_name = aws_loader.upload_dataframe_to_athena(
        df=product_df,
        table_name='shopify_products',
        folder='shopify/products',
        database_name=ATHENA_DATABASE
    )

    return s3_uri, table_name


def shopify_customers_to_aws(limit=250, save_local=True):
    """
    Extract customers from Shopify and upload to AWS S3 + Athena

    Args:
        limit: Maximum number of customers per page
        save_local: Also save CSV locally

    Returns:
        tuple: (s3_uri, athena_table_name)
    """
    print("\n" + "=" * 70)
    print("SHOPIFY CUSTOMERS → AWS PIPELINE")
    print("=" * 70)

    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    customers = extract_customers(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, limit=limit)
    customer_df = pd.DataFrame(customers)
    customer_df = transform_customer_data(customer_df)

    if save_local:
        file_path = f'{OUTPUT_PATH}/customers_latest.csv'
        load_data_to_csv(customer_df, file_path)
        print(f"Local copy saved: {file_path}")

    aws_loader = AWSDataLoader(
        aws_access_key=AWS_ACCESS_KEY_ID,
        aws_secret_key=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
        bucket_name=S3_BUCKET_NAME
    )

    s3_uri, table_name = aws_loader.upload_dataframe_to_athena(
        df=customer_df,
        table_name='shopify_customers',
        folder='shopify/customers',
        database_name=ATHENA_DATABASE
    )

    return s3_uri, table_name


def shopify_line_items_to_aws(days_back=30, limit=250, status='any', save_local=True):
    """
    Extract order line items from Shopify and upload to AWS S3 + Athena.
    This is the key table that connects orders to products.

    Args:
        days_back: Number of days to look back for orders
        limit: Max orders per page
        status: Order status filter
        save_local: Also save CSV locally

    Returns:
        tuple: (s3_uri, athena_table_name)
    """
    print("\n" + "=" * 70)
    print("SHOPIFY LINE ITEMS → AWS PIPELINE")
    print("=" * 70)

    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    line_items = extract_line_items(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, days_back, limit, status)
    print(f"DEBUG: Extracted {len(line_items)} line items")
    line_items_df = pd.DataFrame(line_items)
    print(f"DEBUG: DataFrame shape: {line_items_df.shape}")
    line_items_df = transform_line_item_data(line_items_df)

    if save_local:
        file_path = f'{OUTPUT_PATH}/line_items_latest.csv'
        load_data_to_csv(line_items_df, file_path)
        print(f"Local copy saved: {file_path}")

    aws_loader = AWSDataLoader(
        aws_access_key=AWS_ACCESS_KEY_ID,
        aws_secret_key=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
        bucket_name=S3_BUCKET_NAME
    )

    s3_uri, table_name = aws_loader.upload_dataframe_to_athena(
        df=line_items_df,
        table_name='shopify_line_items',
        folder='shopify/line_items',
        database_name=ATHENA_DATABASE
    )

    return s3_uri, table_name


def run_full_pipeline_to_aws(days_back=30, limit=250):
    """
    Run complete pipeline: Orders + Products + Customers + Line Items → AWS

    Args:
        days_back: Days to look back for orders
        limit: Max products to retrieve
    """
    print("STARTING FULL SHOPIFY → AWS DATA PIPELINE")

    results = {}

    try:
        # 1. Upload Orders
        s3_uri, table = shopify_orders_to_aws(days_back=days_back, limit=limit)
        results['orders'] = {'s3_uri': s3_uri, 'table': table}

        # 2. Upload Products
        s3_uri, table = shopify_products_to_aws(limit=limit)
        results['products'] = {'s3_uri': s3_uri, 'table': table}

        # 3. Upload Customers
        s3_uri, table = shopify_customers_to_aws(limit=limit)
        results['customers'] = {'s3_uri': s3_uri, 'table': table}

        # 4. Upload Line Items
        s3_uri, table = shopify_line_items_to_aws(days_back=days_back, limit=limit)
        results['line_items'] = {'s3_uri': s3_uri, 'table': table}

        # Print summary
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nData uploaded to AWS Athena:")
        for data_type, info in results.items():
            print(f"   • {data_type.upper()}: {info['table']}")

        print("\nConnect Power BI to Athena:")
        print(f"   Database: {ATHENA_DATABASE}")
        print(f"   Region: {AWS_REGION}")
        print(f"   S3 Output: s3://{S3_BUCKET_NAME}/athena-results/")
        print("\n" + "=" * 70 + "\n")

        return results

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = run_full_pipeline_to_aws(days_back=30, limit=250)
