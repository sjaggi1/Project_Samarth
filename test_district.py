<<<<<<< HEAD
"""
Test script for district-level crop queries
Tests the specific query: "Which district has highest wheat production in Punjab in Rabi season in 2020?"
"""

import pandas as pd
import os
from dotenv import load_dotenv
from query_engine_1_rn import QueryEngine

# Load environment
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Please set GEMINI_API_KEY in .env file")
    exit(1)

# Create sample dataset matching your structure
crop_df = pd.DataFrame({
    'State': ['Punjab', 'Punjab', 'Punjab', 'Haryana', 'Haryana', 'Punjab', 'Punjab'],
    'District': ['Ludhiana', 'Amritsar', 'Patiala', 'Hisar', 'Rohtak', 'Ludhiana', 'Amritsar'],
    'Crop': ['Wheat', 'Wheat', 'Wheat', 'Wheat', 'Wheat', 'Rice', 'Rice'],
    'Year': [2020, 2020, 2020, 2020, 2020, 2021, 2021],
    'Production': [4500, 4200, 3800, 3000, 2800, 3200, 3100],
    'Area': [1000, 950, 850, 700, 650, 900, 880],
    'Season': ['Rabi', 'Rabi', 'Rabi', 'Rabi', 'Rabi', 'Kharif', 'Kharif']
})

rainfall_df = pd.DataFrame({
    'State': ['Punjab', 'Haryana', 'Punjab', 'Haryana'],
    'Year': [2020, 2020, 2021, 2021],
    'Annual_Rainfall_mm': [780, 620, 800, 640]
})

data = {
    'crop_production': crop_df,
    'rainfall': rainfall_df
}

print("="*70)
print("TESTING DISTRICT-LEVEL CROP QUERIES")
print("="*70)

# Initialize engine
try:
    engine = QueryEngine(api_key=api_key, data=data)
    print("\n✅ Query engine initialized successfully\n")
except Exception as e:
    print(f"\n❌ Failed to initialize: {e}")
    exit(1)

# Test queries
test_queries = [
    "Which district has highest wheat production in Punjab in Rabi season in 2020?",
    "Which district has highest wheat production in Punjab?",
    "Show me top wheat producing districts in Punjab in 2020",
    "Compare wheat production in Punjab and Haryana"
]

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}: {query}")
    print(f"{'='*70}")
    
    try:
        result = engine.answer_question(query)
        
        print("\n📊 ANSWER:")
        print(result['answer'])
        
        if result.get('data'):
            print("\n📈 DATA RETURNED:")
            for key, value in result['data'].items():
                print(f"  {key}: {value}")
        
        if result.get('sources'):
            print("\n📚 SOURCES:")
            for source in result['sources']:
                print(f"  - {source}")
        
        print("\n✅ Query executed successfully!")
        
    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*70}")
print("TEST COMPLETE")
print(f"{'='*70}")

# Show the data for verification
print("\n📊 DATASET PREVIEW:")
print("\nCrop Production Data:")
print(crop_df.to_string())
print("\nRainfall Data:")
=======
"""
Test script for district-level crop queries
Tests the specific query: "Which district has highest wheat production in Punjab in Rabi season in 2020?"
"""

import pandas as pd
import os
from dotenv import load_dotenv
from query_engine_1_rn import QueryEngine

# Load environment
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Please set GEMINI_API_KEY in .env file")
    exit(1)

# Create sample dataset matching your structure
crop_df = pd.DataFrame({
    'State': ['Punjab', 'Punjab', 'Punjab', 'Haryana', 'Haryana', 'Punjab', 'Punjab'],
    'District': ['Ludhiana', 'Amritsar', 'Patiala', 'Hisar', 'Rohtak', 'Ludhiana', 'Amritsar'],
    'Crop': ['Wheat', 'Wheat', 'Wheat', 'Wheat', 'Wheat', 'Rice', 'Rice'],
    'Year': [2020, 2020, 2020, 2020, 2020, 2021, 2021],
    'Production': [4500, 4200, 3800, 3000, 2800, 3200, 3100],
    'Area': [1000, 950, 850, 700, 650, 900, 880],
    'Season': ['Rabi', 'Rabi', 'Rabi', 'Rabi', 'Rabi', 'Kharif', 'Kharif']
})

rainfall_df = pd.DataFrame({
    'State': ['Punjab', 'Haryana', 'Punjab', 'Haryana'],
    'Year': [2020, 2020, 2021, 2021],
    'Annual_Rainfall_mm': [780, 620, 800, 640]
})

data = {
    'crop_production': crop_df,
    'rainfall': rainfall_df
}

print("="*70)
print("TESTING DISTRICT-LEVEL CROP QUERIES")
print("="*70)

# Initialize engine
try:
    engine = QueryEngine(api_key=api_key, data=data)
    print("\n✅ Query engine initialized successfully\n")
except Exception as e:
    print(f"\n❌ Failed to initialize: {e}")
    exit(1)

# Test queries
test_queries = [
    "Which district has highest wheat production in Punjab in Rabi season in 2020?",
    "Which district has highest wheat production in Punjab?",
    "Show me top wheat producing districts in Punjab in 2020",
    "Compare wheat production in Punjab and Haryana"
]

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}: {query}")
    print(f"{'='*70}")
    
    try:
        result = engine.answer_question(query)
        
        print("\n📊 ANSWER:")
        print(result['answer'])
        
        if result.get('data'):
            print("\n📈 DATA RETURNED:")
            for key, value in result['data'].items():
                print(f"  {key}: {value}")
        
        if result.get('sources'):
            print("\n📚 SOURCES:")
            for source in result['sources']:
                print(f"  - {source}")
        
        print("\n✅ Query executed successfully!")
        
    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*70}")
print("TEST COMPLETE")
print(f"{'='*70}")

# Show the data for verification
print("\n📊 DATASET PREVIEW:")
print("\nCrop Production Data:")
print(crop_df.to_string())
print("\nRainfall Data:")
>>>>>>> 682e4b9c (Initial commit of Project Samarth)
print(rainfall_df.to_string())