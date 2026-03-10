from etls.Shopify_Connect import connect_shopify

from etls.load import load_data_to_csv

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
    transform_customer_data
)

from utils.constants import SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, OUTPUT_PATH
import pandas as pd


def shopify_orders_pipeline(file_name: str, days_back=7, limit=250, status='any'):
    """
    Pipeline to extract orders from Shopify using REST API

    Args:
        file_name: Name for the output file (without extension)
        days_back: Number of days to look back for orders
        limit: Maximum number of orders to retrieve
        status: Order status filter ('any', 'open', 'closed', 'cancelled')
    """
    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    orders = extract_orders(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, days_back, limit, status)

    order_df = pd.DataFrame(orders)
    order_df = transform_order_data(order_df)

    file_path = f'{OUTPUT_PATH}/{file_name}.csv'
    load_data_to_csv(order_df, file_path)

    return file_path


def shopify_products_pipeline(file_name: str, limit=250):
    """
    Pipeline to extract products from Shopify using REST API

    Args:
        file_name: Name for the output file (without extension)
        limit: Maximum number of products to retrieve
    """
    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    products = extract_products(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, limit)

    product_df = pd.DataFrame(products)
    product_df = transform_product_data(product_df)

    file_path = f'{OUTPUT_PATH}/{file_name}.csv'
    load_data_to_csv(product_df, file_path)

    return file_path


def shopify_customers_pipeline(file_name: str, limit=250):
    """
    Pipeline to extract customers from Shopify using REST API

    Args:
        file_name: Name for the output file (without extension)
        limit: Maximum number of customers per page
    """
    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    customers = extract_customers(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, limit=limit)

    customer_df = pd.DataFrame(customers)
    customer_df = transform_customer_data(customer_df)

    file_path = f'{OUTPUT_PATH}/{file_name}.csv'
    load_data_to_csv(customer_df, file_path)

    return file_path


def shopify_out_of_stock_pipeline(file_name: str, limit=250):
    """
    Pipeline to extract only out-of-stock products

    Args:
        file_name: Name for the output file (without extension)
        limit: Maximum number of products to retrieve
    """
    connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN)

    products = extract_products(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, limit)

    product_df = pd.DataFrame(products)
    product_df = transform_product_data(product_df)

    out_of_stock_df = product_df[product_df['inventory_quantity'] <= 0]

    file_path = f'{OUTPUT_PATH}/{file_name}.csv'
    load_data_to_csv(out_of_stock_df, file_path)

    return file_path