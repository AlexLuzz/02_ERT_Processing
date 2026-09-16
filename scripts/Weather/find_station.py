import requests

def get_stations_dict(province, search_term=""):
    url = "https://collaboration.cmc.ec.gc.ca/cmc/climate/Get_More_Data_Plus_de_donnees/Station%20Inventory%20EN.csv"
    
    print("Fetching station data... (This might take a few seconds)")
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    # 1. Split the raw text string into a list of individual lines
    lines = r.text.strip().split('\n')
    
    # 2. Extract headers from the 4th line (index 3). 
    # Strip the leading/trailing quotes and newlines, then split by the quote-comma-quote separator.
    headers = lines[3].strip(' "\r').split('","')
    
    # Find the column indexes dynamically so we don't rely on hardcoded positions
    name_idx = headers.index("Name")
    id_idx = headers.index("Station ID")
    prov_idx = headers.index("Province")

    target_province = province.strip().upper()
    target_term = search_term.strip().upper()
    
    # 3. Create an empty dictionary to hold the results
    stations_dict = {}
    
    # 4. Iterate through the data lines starting from index 4
    for line in lines[4:]:
        if not line.strip():
            continue
            
        # Parse the data row using the same manual split method
        row = line.strip(' "\r').split('","')
        
        # Guard against malformed lines that are missing columns
        if len(row) <= max(name_idx, id_idx, prov_idx):
            continue
            
        row_prov = row[prov_idx].strip().upper()
        row_name = row[name_idx].strip().upper()
        row_id = row[id_idx].strip()
        
        # 5. Filter and populate the dictionary
        if row_prov == target_province:
            if not target_term or target_term in row_name:
                # Add to dictionary: Key = Station ID, Value = Name
                stations_dict[row_id] = row_name

    # Display the results
    if not stations_dict:
        print(f"\nNo stations found for {province} matching '{search_term}'.")
    else:
        print(f"\n--- Found {len(stations_dict)} stations ---")
        for station_id, station_name in stations_dict.items():
            print(f"ID: {station_id:<8} | Name: {station_name}")
            
    return stations_dict

# ==========================================
# Try it out!
# ==========================================

# Example: Get a dictionary of all stations in Quebec containing "MONTREAL"
my_stations = get_stations_dict(province="QUEBEC", search_term="VAL")

# You can now use the dictionary directly in your code
# print(my_stations["5415"])  # Would print "MONTREAL/PIERRE ELLIOTT TRUDEAU INTL A"