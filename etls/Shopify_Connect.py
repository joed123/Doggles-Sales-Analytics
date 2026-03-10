# Shopify API Configuration
import sys
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.constants import SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN

def connect_shopify(SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN):
    "Test connection to Shopify store"

    try:
        # Correct:
        url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2023-10/shop.json"

        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            shop_data = response.json().get('shop', {})
            print(f"Connected to Shopify store: {shop_data.get('name', 'Unknown')}")
            return True
        else:
            print(f"Failed to connect. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to Shopify: {e}")
        sys.exit(1)