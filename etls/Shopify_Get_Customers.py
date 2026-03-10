# Shopify API Configuration
import sys
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.constants import SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN


def extract_customers(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, days_back=None, limit=250):
    """
    Extract ALL customers from Shopify by paginating through the 'Link'
    header to retrieve data beyond the 250 limit.

    Args:
        SHOPIFY_STORE: Shopify store subdomain
        SHOPIFY_ACCESS_TOKEN: API access token
        days_back: Optional - only fetch customers created in the last N days. None fetches all.
        limit: Max per page (max 250)

    Returns:
        list: List of customer dictionaries
    """
    all_customers = []

    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2023-10/customers.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }


    params = {'limit': limit}

    if days_back:
        created_at_min = (datetime.now() - timedelta(days=days_back)).isoformat()
        params['created_at_min'] = created_at_min

    while url:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to extract customers {response.status_code}")
            print(f"Response body: {response.text}")
            print(f"Request URL: {url}")
            break

        customers = response.json().get('customers', [])
        data = []

        for customer in customers:
            default_address = customer.get('default_address') or {}

            data.append({
                'customer_id': customer['id'],
                'email': customer.get('email'),
                'first_name': customer.get('first_name'),
                'last_name': customer.get('last_name'),
                'orders_count': customer.get('orders_count'),
                'total_spent': customer.get('total_spent'),
                'state': customer.get('state'),
                'tags': customer.get('tags'),
                'city': default_address.get('city'),
                'province': default_address.get('province'),
                'country': default_address.get('country'),
                'created_at': customer.get('created_at'),
                'updated_at': customer.get('updated_at')
            })

        all_customers.extend(data)

        # Reset params for subsequent requests, as they're now part of the URL
        params = {}

        # Check for the 'Link' header to find the next page
        link_header = response.headers.get('Link')
        next_url = None

        if link_header:
            links = link_header.split(', ')
            for link in links:
                if 'rel="next"' in link:
                    next_url = link.split(';')[0].strip('<>')
                    break

        url = next_url

    print(f"Extracted a total of {len(all_customers)} customers (including all pages)")
    return all_customers


def transform_customer_data(customer_df: pd.DataFrame):
    if customer_df.empty:
        return customer_df

    timestamp_cols = ['created_at', 'updated_at']
    for col in timestamp_cols:
        if col in customer_df.columns:
            customer_df[col] = pd.to_datetime(customer_df[col], utc=True)

    numeric_cols = ['orders_count', 'total_spent']
    for col in numeric_cols:
        if col in customer_df.columns:
            customer_df[col] = pd.to_numeric(customer_df[col], errors='coerce')

    string_cols = ['email', 'first_name', 'last_name', 'state', 'tags', 'city', 'province', 'country']
    for col in string_cols:
        if col in customer_df.columns:
            customer_df[col] = customer_df[col].astype(str)

    return customer_df