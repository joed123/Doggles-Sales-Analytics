"""
Shopify Line Items Extraction
Extracts order line items (individual products within each order)
This connects orders to products so you can see what sells best.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta



def extract_line_items(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, days_back=30, limit=250, status='any'):
    """
    Extract order line items from Shopify.
    Each order can have multiple line items (products purchased).

    Args:
        SHOPIFY_STORE: Shopify store subdomain
        SHOPIFY_ACCESS_TOKEN: API access token
        days_back: Number of days to look back
        limit: Max orders per page (max 250)
        status: Order status filter ('any', 'open', 'closed', 'cancelled')

    Returns:
        list: List of line item dictionaries
    """
    all_line_items = []

    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2024-10/orders.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    created_at_min = (datetime.now() - timedelta(days=days_back)).isoformat()
    params = {
        'limit': limit,
        'status': status,
        'created_at_min': created_at_min
    }

    while url:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to extract orders for line items: {response.status_code}")
            print(f"Response body: {response.text}")
            break

        orders = response.json().get('orders', [])
        print(f"DEBUG: Processing {len(orders)} orders for line items...")

        for order in orders:
            order_id = order['id']
            order_email = order.get('email')
            order_created_at = order.get('created_at')
            order_financial_status = order.get('financial_status')
            order_fulfillment_status = order.get('fulfillment_status')

            for item in order.get('line_items', []):
                all_line_items.append({
                    'order_id': order_id,
                    'order_created_at': order_created_at,
                    'order_email': order_email,
                    'financial_status': order_financial_status,
                    'fulfillment_status': order_fulfillment_status,
                    'line_item_id': item.get('id'),
                    'product_id': item.get('product_id'),
                    'variant_id': item.get('variant_id'),
                    'product_title': item.get('title'),
                    'variant_title': item.get('variant_title'),
                    'sku': item.get('sku'),
                    'quantity': item.get('quantity'),
                    'price': item.get('price'),
                    'total_discount': item.get('total_discount', '0.00'),
                })

        # Reset params for subsequent paginated requests
        params = {}

        # Check for pagination via Link header
        link_header = response.headers.get('Link')
        next_url = None

        if link_header:
            links = link_header.split(', ')
            for link in links:
                if 'rel="next"' in link:
                    next_url = link.split(';')[0].strip('<>')
                    break

        url = next_url

    print(f"Extracted {len(all_line_items)} line items from all orders")
    return all_line_items


def transform_line_item_data(line_items_df: pd.DataFrame):
    """
    Transform line items DataFrame with proper types.

    Args:
        line_items_df: Raw line items DataFrame

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    if line_items_df.empty:
        return line_items_df

    # Convert timestamps
    timestamp_cols = ['order_created_at']
    for col in timestamp_cols:
        if col in line_items_df.columns:
            line_items_df[col] = pd.to_datetime(line_items_df[col], utc=True)

    # Convert numeric columns
    numeric_cols = ['quantity', 'price', 'total_discount']
    for col in numeric_cols:
        if col in line_items_df.columns:
            line_items_df[col] = pd.to_numeric(line_items_df[col], errors='coerce')

    # Calculate line total (quantity * price - discount)
    if all(c in line_items_df.columns for c in ['quantity', 'price', 'total_discount']):
        line_items_df['line_total'] = (
            line_items_df['quantity'] * line_items_df['price']
        ) - line_items_df['total_discount']

    # Convert string columns
    string_cols = ['order_email', 'financial_status', 'fulfillment_status',
                   'product_title', 'variant_title', 'sku']
    for col in string_cols:
        if col in line_items_df.columns:
            line_items_df[col] = line_items_df[col].astype(str)

    return line_items_df
