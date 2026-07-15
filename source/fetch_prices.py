import requests
import json

def fetch_poe2_prices():
    print("Connecting to the updated Path of Exile 2 poe.ninja API...")
    
    # PoE2 uses a brand new base path structure
    league = "Standard"  # Update this to the current temporary league if needed
    url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league=Runes%20of%20Aldur&type=Currency"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ExileVision/1.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("Successfully retrieved live PoE2 data!\n")
            
            lines = data.get('lines', [])
            
            print(f"--- Tracking {len(lines)} different PoE2 Currencies ---")
            
            # The modern API payload formats currency rates directly inside the lines
            for line in lines[:15]:
                # In PoE2, currency names are found under 'currencyTypeName'
                currency_name = line.get('currencyTypeName')
                
                # The value calculation engine in the new endpoint uses 'chaosEquivalent' 
                # or direct conversion rates depending on active league benchmarks
                value = line.get('chaosEquivalent', 0.0)
                
                if value > 0:
                    print(f"🔹 {currency_name}: {value:.2f} Chaos")
                else:
                    print(f"🔹 {currency_name}: Listed in bulk market")
                    
        else:
            print(f"Failed to connect. HTTP Status Code: {response.status_code}")
            print("Make sure the league name is exact and capitalized correctly.")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    fetch_poe2_prices()