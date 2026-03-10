
import pandas as pd


def load_data_to_csv(data: pd.DataFrame, path: str):
    """Save data to CSV"""
    data.to_csv(path, index=False)
    print(f"Data saved to {path}")