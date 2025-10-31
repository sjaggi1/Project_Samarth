"""
Data Collector Module for Project Samarth
Fetches and caches data from data.gov.in
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime
import time

class DataCollector:
    def __init__(self, cache_dir="data_cache"):
        self.cache_dir = cache_dir
        self.base_url = "https://api.data.gov.in/resource"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Key dataset IDs from data.gov.in
        self.datasets = {
            "agriculture": "9ef84268-d588-465a-a308-a864a43d0070",  # Crop production
            "rainfall": "eb1f4e8f-e7b5-4f8f-a7d7-7f3d9c6c4b8a",     # Rainfall data
        }
    
    def fetch_data(self, resource_id, filters=None, limit=10000):
        """Fetch data from data.gov.in API"""
        cache_file = f"{self.cache_dir}/{resource_id}.json"
        
        # Check cache first
        if os.path.exists(cache_file):
            age = time.time() - os.path.getmtime(cache_file)
            if age < 86400:  # 24 hours
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        # Fetch from API
        params = {
            "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b",
            "format": "json",
            "limit": limit
        }
        
        if filters:
            params["filters"] = json.dumps(filters)
        
        try:
            url = f"{self.base_url}/{resource_id}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            
            return data
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def get_crop_production_data(self):
        """Get agricultural production data"""
        cache_file = f"{self.cache_dir}/crop_production.csv"
        
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file)
        
        # Sample agricultural data structure
        # In production, fetch from actual API
        data = {
            'State': ['Punjab', 'Punjab', 'Haryana', 'Haryana', 'UP', 'UP'] * 5,
            'District': ['Ludhiana', 'Amritsar', 'Karnal', 'Ambala', 'Meerut', 'Agra'] * 5,
            'Crop': ['Wheat', 'Rice', 'Wheat', 'Rice', 'Sugarcane', 'Wheat'] * 5,
            'Year': [2020, 2020, 2020, 2020, 2020, 2020] + [2021]*6 + [2022]*6 + [2023]*6 + [2024]*6,
            'Production': [4500, 3200, 4200, 3000, 5500, 4000] * 5,
            'Area': [1000, 900, 950, 850, 1200, 1050] * 5,
            'Season': ['Rabi', 'Kharif', 'Rabi', 'Kharif', 'Kharif', 'Rabi'] * 5
        }
        
        df = pd.DataFrame(data)
        df.to_csv(cache_file, index=False)
        return df
    
    def get_rainfall_data(self):
        """Get rainfall data"""
        cache_file = f"{self.cache_dir}/rainfall.csv"
        
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file)
        
        # Sample rainfall data
        data = {
            'State': ['Punjab', 'Haryana', 'UP'] * 15,
            'District': ['Ludhiana', 'Karnal', 'Meerut'] * 15,
            'Year': [2020]*3 + [2021]*3 + [2022]*3 + [2023]*3 + [2024]*3 + 
                    [2020]*3 + [2021]*3 + [2022]*3 + [2023]*3 + [2024]*3 +
                    [2020]*3 + [2021]*3 + [2022]*3 + [2023]*3 + [2024]*3,
            'Annual_Rainfall_mm': [650, 680, 720, 670, 690, 710, 660, 700, 730, 
                                  680, 710, 740, 690, 720, 750] * 3,
            'Monsoon_Rainfall_mm': [450, 470, 500, 460, 480, 490, 470, 490, 510,
                                   480, 500, 520, 490, 510, 530] * 3
        }
        
        df = pd.DataFrame(data)
        df.to_csv(cache_file, index=False)
        return df
    
    def get_all_data(self):
        """Load all datasets"""
        return {
            'crop_production': self.get_crop_production_data(),
            'rainfall': self.get_rainfall_data()
        }

if __name__ == "__main__":
    collector = DataCollector()
    data = collector.get_all_data()
    print("Data loaded successfully!")
    print(f"Crop production records: {len(data['crop_production'])}")
