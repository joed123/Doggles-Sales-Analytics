# Shopify API Configuration
import sys
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.constants import SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN


# In Shopify_Get_Inventory.py

def extract_products(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, limit=250):
    """
    Extract ALL products from Shopify by paginating through the 'Link'
    header to retrieve data beyond the 250 limit.
    """
    all_products_variants = []

    # 1. Start with the initial URL and parameters
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2023-10/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    params = {'limit': limit}  # Max 250 per request

    # 2. Loop until no 'next' page is found
    while url:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to extract products {response.status_code}")
            print(f"Response body: {response.text}")
            print(f"Request URL: {url}")
            break  # Exit loop on error

        products = response.json().get('products', [])
        data = []

        for product in products:
            for variant in product["variants"]:
                data.append({
                    'product_id': product['id'],
                    'product_title': product['title'],
                    'variant_id': variant['id'],
                    'variant_title': variant['title'],
                    'sku': variant['sku'],
                    'price': variant['price'],
                    'inventory_quantity': variant['inventory_quantity'],
                    'created_at': product.get('created_at'),
                    'updated_at': product.get('updated_at')
                })

        all_products_variants.extend(data)

        # Reset params for subsequent requests, as they're now part of the URL
        params = {}

        # 3. Check for the 'Link' header to find the next page
        link_header = response.headers.get('Link')
        next_url = None

        if link_header:
            # Simple parsing for the rel="next" link
            links = link_header.split(', ')
            for link in links:
                if 'rel="next"' in link:
                    # Extract URL from <...>
                    next_url = link.split(';')[0].strip('<>')
                    break

        url = next_url  # Update URL for the next iteration (or becomes None to stop)

    print(f"Extracted a total of {len(all_products_variants)} product variants (including all pages)")
    return all_products_variants



def transform_product_data(product_df: pd.DataFrame):
    if product_df.empty:
        return product_df

    timestamp_cols = ['created_at', 'updated_at']
    for col in timestamp_cols:
        if col in product_df.columns:
            product_df[col] = pd.to_datetime(product_df[col], utc=True)

    numeric_cols = ['price', 'inventory_quantity']
    for col in numeric_cols:
        if col in product_df.columns:
            product_df[col] = pd.to_numeric(product_df[col], errors = 'coerce')

    string_cols = ['product_title', 'variant_title', 'sku']
    for col in string_cols:
        if col in product_df.columns:
            product_df[col] = product_df[col].astype(str)

    return product_df















