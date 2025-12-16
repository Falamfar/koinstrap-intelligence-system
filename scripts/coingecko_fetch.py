import requests  #to fetch data from the CoinGecko API
import os #to handle folder paths
import json  #to parse JSON responses
from datetime import datetime  #to stampstamp collected data.
from dotenv import load_dotenv  #to load environment variables from a .env file


load_dotenv()  # Load environment variables from .env file
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")  # Get CoinGecko API key from environment variables

# Define the base URL for CoinGecko API
BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"

# Define parameters for the API request
params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 100,
    "page": 1,
    "sparkline": "false",
    "ids": "bitcoin,ethereum"
}

#OPtional: attach API key if required by CoinGecko
if COINGECKO_API_KEY:
    params["x_cg_demo_api_key"] = COINGECKO_API_KEY

# Make the API request    
response = requests.get(BASE_URL, params=params)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Parse the JSON response
    print("✅coingecko data fetched successfully.")
else:
    print(f"❌Failed to fetch data from CoinGecko. Status code: {response.status_code}")
    data = []

#Ensure raw data directory exists
RAW_DATA_DIR = "data/raw/coingecko/"  
os.makedirs(RAW_DATA_DIR, exist_ok=True)

#Create a filename with current timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
file_path = f"{RAW_DATA_DIR}/coingecko_data_{timestamp}.json"

#Save the fetched data to a JSON file
with open(file_path, "w") as f:
    json.dump(data, f, indent=4)

print(f"✅CoinGecko data saved to {file_path}.")