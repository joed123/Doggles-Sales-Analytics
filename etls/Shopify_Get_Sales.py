# Shopify API Configuration
import sys
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.constants import SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN


def extract_orders(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, days_back=7, limit=250, status='any'):
    """
       Extract orders from Shopify using REST API
       days_back: number of days to look back for orders
       limit: max number of orders to retrieve (max 250 per request)
       status: 'open', 'closed', 'cancelled', or 'any'
       """
    try:
        url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2023-10/orders.json"
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }

        created_at_min = (datetime.now() - timedelta(days=days_back)).isoformat()

        params = {
            'status': status,
            'created_at_min': created_at_min,
            'limit': limit
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to fetch orders. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []

        orders = response.json().get('orders', [])
        print(f"Extracted {len(orders)} orders")
        return orders

    except Exception as e:
        print(f"Could not extract orders. Error: {e}")
        return []

def transform_order_data(order_df: pd.DataFrame):
    if order_df.empty:
        return order_df

    # FILTER TO ONLY THE COLUMNS WE NEED
    keep_columns = [
        'id', 'email', 'created_at', 'updated_at',
        'total_price', 'subtotal_price', 'total_tax',
        'financial_status', 'fulfillment_status'
    ]
    # Only keep columns that exist in the DataFrame
    keep_columns = [col for col in keep_columns if col in order_df.columns]
    order_df = order_df[keep_columns]

    timestamp_cols = ['created_at', 'updated_at']
    for col in timestamp_cols:
        if col in order_df.columns:
            order_df[col] = pd.to_datetime(order_df[col], utc=True)

    numeric_cols = ['total_price', 'subtotal_price', 'total_tax']
    for col in numeric_cols:
        if col in order_df.columns:
            order_df[col] = pd.to_numeric(order_df[col], errors='coerce')

    string_cols = ['email', 'financial_status', 'fulfillment_status']
    for col in string_cols:
        if col in order_df.columns:
            order_df[col] = order_df[col].astype(str)

    return order_df


