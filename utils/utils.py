import requests
import json
from utils.rep_gen import generate_report_seller, generate_buyer_report
import time
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from openai import OpenAI
import re
import os
import cv2
#ZILLOW API KEYS
API_KEY = os.getenv("ZILLOW_KEY")
API_KEY_OPENAI = os.getenv("OPENAPI_KEY")
client = OpenAI(api_key=API_KEY_OPENAI)

placeholder_url_img = "https://www.zillowstatic.com/static/images/nophoto_p_c.png"

def split_address(address):
    # Split the address into main components
    parts = address.split(", ")
    street_address = parts[0]  # First part is the street address
    city = parts[1]  # Second part is the city
    state_zip = parts[2]  # Third part contains state and ZIP

    # Further split state and ZIP
    state, zip_code = state_zip.split(" ")
    return street_address, city, state, zip_code

def get_property_data(address):

    url = "https://zillow-working-api.p.rapidapi.com/pro/byaddress"

    querystring = {"propertyaddress":address}

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "zillow-working-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if not response.status_code == 200:
        return None
    return response.json()

def get_property_info(address):
    data = get_property_data(address)

    if data is None:
        return {"error": "API_DATA_NOT_FOUND or API_LIMIT_REACHED"}
    
    zillowURL = data.get('zillowURL', "N/A")
    property_details = data.get('propertyDetails', {})

    latitude = property_details.get('latitude', "N/A")
    longitude = property_details.get('longitude', "N/A")
    bedrooms = property_details.get('bedrooms', "N/A")
    if bedrooms == None:
        bedrooms = "N/A"
    bathrooms = property_details.get('bathrooms', "N/A")
    if bathrooms == None:
        bathrooms = "N/A"
    price = property_details.get('price', "N/A")
    if price == None:
        price = "N/A"
    yearBuilt = property_details.get('yearBuilt', "N/A")
    description = property_details.get('description', "N/A")
    
    tax_history = property_details.get('taxHistory', [])
    taxValue = tax_history[0].get('value', 0) if tax_history else 0
    if taxValue == None:
        taxValue = "N/A"
    livingArea = property_details.get('livingArea', "N/A")
    if livingArea == None:
        livingArea = "N/A"
    lotSize = property_details.get('lotSize', "N/A")
    if lotSize == None:
        lotSize = "N/A"
    zestimate = property_details.get('lastSoldPrice', "N/A")
    if zestimate == None:
        zestimate = "N/A"
    assessed_value = (zestimate + price) / 2 if isinstance(zestimate, (int, float)) and isinstance(price, (int, float)) else "N/A"
    
    main_img_url = property_details.get('mediumImageLink', "N/A")
    if main_img_url == None or main_img_url == "N/A":
        main_img_url = property_details['originalPhotos'][0]['mixedSources']['jpeg'][0]['url'] if property_details.get('originalPhotos') else placeholder_url_img
    
    timeOnZillow = property_details.get('timeOnZillow', "N/A")
    daysOnZillow = int(timeOnZillow.split(" ")[0]) if isinstance(timeOnZillow, str) and timeOnZillow.split(" ")[0].isdigit() else "N/A"

    
    return { 'address': address,"days_on_market":daysOnZillow,'main_img_url':main_img_url, 'url': zillowURL,"zestimate":price, 'Assessed_value': taxValue, 'square_footage': livingArea, 'totalBathrooms': bathrooms, 'totalBedrooms': bedrooms, 'totalMarketValue': zestimate, 'Porperty_size': lotSize,"specifications":description,"longitude":longitude,"latitude":latitude}

def get_annual_tax(data):
    url = "https://zillow-working-api.p.rapidapi.com/taxinfo"

    querystring = {"byurl":data['url']}

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "zillow-working-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    tax_resp = response.json()
    for i in range(len(tax_resp['taxHistory'])):
        annual_tax = tax_resp['taxHistory'][i]['taxPaid']
        if not annual_tax is None:
            break
    return annual_tax

def get_comps(data,sold=False):
    url = "https://zillow-working-api.p.rapidapi.com/search/bycoordinates"
    listing_statue = "For_Sale"
    if sold == True:
        listing_statue = 'Sold'
        
    if data['totalBedrooms'] == None:
        totalBedrooms = 5
    else:
        totalBedrooms = data['totalBedrooms']
    if data['totalBathrooms'] == None:
        totalBathrooms = 'Any'
    else:
        if data['totalBathrooms'] == 1 or data['totalBathrooms']== 'OnePlus':
            totalBathrooms = 'OnePlus'
        elif data['totalBathrooms'] == 2 or data['totalBathrooms'] == 'TwoPlus':
            totalBathrooms = 'TwoPlus'
        elif data['totalBathrooms'] == 3 or data['totalBathrooms'] == 'ThreePlus':
            totalBathrooms = 'ThreePlus'
        elif data['totalBathrooms'] == 4 or data['totalBathrooms'] == 'FourPlus':
            totalBathrooms = 'FourPlus'
        else:
            totalBathrooms = 'Any'
    if sold == True:
        querystring = {"latitude":str(data['latitude']),"longitude":str(data['longitude']),"radius":"1","page":"1","listingStatus":listing_statue,"bed_max":str(totalBedrooms),"bathrooms":totalBathrooms,"homeType":"Houses, Townhomes, Multi-family, Condos/Co-ops, Lots-Land, Apartments, Manufactured","maxHOA":"Any","listingType":"By_Agent","listingTypeOptions":"Agent listed,New Construction,Fore-closures,Auctions","parkingSpots":"Any","mustHaveBasement":"No","daysOnZillow":"Any","soldInLast":"Any"}
    else:
        querystring = {"latitude":str(data['latitude']),"longitude":str(data['longitude']),"radius":"1","page":"1","listingStatus":listing_statue,"homeType":"Houses, Townhomes, Multi-family, Condos/Co-ops, Lots-Land, Apartments, Manufactured","maxHOA":"Any","listingType":"By_Agent","listingTypeOptions":"Agent listed,New Construction,Fore-closures,Auctions","parkingSpots":"Any","mustHaveBasement":"No","daysOnZillow":"Any","soldInLast":"Any"}
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "zillow-working-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    if not response.status_code == 200:
        return None
    return response.json()

def generate_zillow_url(address: str, zpid: str) -> str:
    """
    Generate a Zillow property URL based on the address and Zillow Property ID (zpid).
    Removes any '#' characters from the address.

    Args:
    - address (str): The property address (e.g., "110 Vandelinda Avenue, Teaneck, NJ 07666").
    - zpid (str): The Zillow Property ID.

    Returns:
    - str: The generated Zillow URL.
    """
    # Format the address to match Zillow's URL structure
    formatted_address = address.lower().replace(",", "").replace(" ", "-").replace("#", "")

    # Construct the Zillow property URL
    zillow_url = f"https://www.zillow.com/homedetails/{formatted_address}/{zpid}_zpid/"
    
    return zillow_url

def calculate_distance_miles(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points (A and B) on Earth using the Haversine formula.

    Args:
    - lat1, lon1: Latitude and Longitude of point A (in decimal degrees).
    - lat2, lon2: Latitude and Longitude of point B (in decimal degrees).

    Returns:
    - Distance in miles (float).
    """
    # Radius of the Earth in miles
    R = 3958.8

    # Convert latitude and longitude from degrees to radians
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Distance in miles
    distance = R * c
    return distance

def get_past_date(days_back):
    """
    Get the date 'n' days before the current date.

    Args:
    - days_back (int): The number of days to subtract from today.

    Returns:
    - Past date as a string in 'YYYY-MM-DD' format.
    """
    try:
        days_back = int(days_back)
    except:
        return days_back
    current_date = datetime.now()
    past_date = current_date - timedelta(days=days_back)
    return past_date.strftime("%m-%d-%Y")

def convert_timestamp_to_date(timestamp_ms):
    # Convert milliseconds to seconds
    timestamp_sec = timestamp_ms / 1000
    # Convert to datetime object
    date_obj = datetime.utcfromtimestamp(timestamp_sec)
    # Format the date as DD-MM-YYYY
    formatted_date = date_obj.strftime('%m-%d-%Y')
    return formatted_date

def safe_convert(value):
    """
    Convert a value to float.
    Handles strings by removing '$' and commas, and returns None for invalid data.
    """
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').replace(' sq ft','').strip()
        return float(value)
    except (ValueError, TypeError):
        return None

def convert_lot_size(value):
    """
    Convert lot size value to square feet.
    If the numeric value is less than 10, assume it's in acres and convert to sqft.
    Otherwise, assume it's already in sqft.
    """
    num = safe_convert(value)
    if num is None:
        return None
    return num * 43560 if num < 10 else num

def estimate_property_price(base_property, sold_properties, on_market_properties):
    """
    Estimates the price range for a base property based on sold and on-market comparables.
    
    :param base_property: Dict with keys 'asking_price', 'beds', 'baths', 'lot_size', 'sqft'
                           (lot_size is assumed to be in sqft)
    :param sold_properties: List of dicts with keys 'sold_price', 'beds', 'baths', 'lot_size', 'sqft'
                           (lot_size may be in acres if <10)
    :param on_market_properties: List of dicts with keys 'asking_price', 'beds', 'baths', 'lot_size', 'sqft'
    :return: Dict with formatted 'min_price', 'max_price', and 'mid_price'
    """
    def calculate_price_per_unit(properties, price_key):
        """
        Calculate price-per-unit metrics:
         - Price per lot sqft,
         - Price per living sqft,
         - Price per (beds + 0.5 * baths)
        """
        lot_prices = []
        sqft_prices = []
        bedbath_prices = []
        
        for prop in properties:
            price = safe_convert(prop.get(price_key, 'N/A'))
            lot_size = convert_lot_size(prop.get('lot_size', 'N/A'))
            sqft = safe_convert(prop.get('sqft', 'N/A'))
            beds = safe_convert(prop.get('beds', 'N/A'))
            baths = safe_convert(prop.get('baths', 'N/A'))
            
            if price is None:
                continue
            
            if lot_size and lot_size > 0:
                ratio = price / lot_size
                if ratio > 0:
                    lot_prices.append(ratio)
            if sqft and sqft > 0:
                ratio = price / sqft
                if ratio > 0:
                    sqft_prices.append(ratio)
            if (beds is not None and baths is not None) and (beds + 0.5 * baths > 0):
                ratio = price / (beds + 0.5 * baths)
                if ratio > 0:
                    bedbath_prices.append(ratio)
                    
        return lot_prices, sqft_prices, bedbath_prices

    # Convert base property values (using convert_lot_size for lot_size)
    base = {}
    for k, v in base_property.items():
        if k == 'lot_size':
            base[k] = convert_lot_size(v)
        else:
            base[k] = safe_convert(v)
    # Calculate per-unit metrics for sold and on-market properties
    sold_lot, sold_sqft, sold_bedbath = calculate_price_per_unit(sold_properties, 'sold_price')
    market_lot, market_sqft, market_bedbath = calculate_price_per_unit(on_market_properties, 'asking_price')
    # Combine both datasets
    lot_prices = sold_lot + market_lot
    sqft_prices = sold_sqft + market_sqft
    bedbath_prices = sold_bedbath + market_bedbath
    
    # Use median as a robust estimator
    med_lot = np.median(lot_prices) if lot_prices else None
    med_sqft = np.median(sqft_prices) if sqft_prices else None
    med_bedbath = np.median(bedbath_prices) if bedbath_prices else None
    
    estimated_prices = []
    if med_lot is not None and base.get('lot_size'):
        estimated_prices.append(med_lot * base['lot_size'])
    if med_sqft is not None and base.get('sqft'):
        estimated_prices.append(med_sqft * base['sqft'])
    if med_bedbath is not None and base.get('beds') is not None and base.get('baths') is not None:
        estimated_prices.append(med_bedbath * (base['beds'] + 0.5 * base['baths']))
    
    # Fallback: if no estimated prices are computed, use the base property's asking price if available.
    if not estimated_prices:
        fallback = safe_convert(base_property.get('asking_price'))
        fallback = fallback if fallback is not None else 0
        return [round(fallback, 2),round(fallback, 2), round(fallback, 2)]   
    def round_to_nearest_ten(value):
        """Round an integer to the nearest ten (replace unit and ten place with 0)."""
        return (value // 100) * 100
    # Compute final results using the available estimates
    min_price = round_to_nearest_ten(int(min(estimated_prices)))
    max_price = round_to_nearest_ten(int(max(estimated_prices)))
    mid_price = round_to_nearest_ten(int(np.median(estimated_prices))) if estimated_prices else 0
    
    if min_price < mid_price - 60000:
        min_price = mid_price - 60000
    if max_price > mid_price +60000:
        max_price = mid_price + 60000

    return [round(min_price, 2),round(mid_price, 2), round(max_price, 2)]

def get_pricing_components(data,sold=False):
    info_all = []
    properties = data['searchResults']
    for prop in properties:
        try:
            sale_amount= prop['property']['price'].get('value',"N/A")
            bedrooms = prop['property'].get('bedrooms',"N/A")
            bathrooms = prop['property'].get('bathrooms',"N/A")
            square_feet = prop['property'].get('livingArea',"N/A")
            year_built = prop['property'].get('yearBuilt',"N/A")
            try:
                lot_size = prop['property']['lotSizeWithUnit'].get('lotSize',"N/A")
                lot_size = str("{:.2f}".format(float(lot_size)))
            except:
                lot_size = "N/A"
            if sold == True:
                
                info = {'sold_price': sale_amount, 'beds': bedrooms, 'baths': bathrooms, 'lot_size': lot_size, 'sqft': square_feet}
            else:
                info = {'asking_price': sale_amount, 'beds': bedrooms, 'baths': bathrooms, 'lot_size': lot_size, 'sqft': square_feet}
            info_all.append(info)
        except Exception as e:
            print("ERROR_DURING_FORMATING",e)
            pass
    return info_all

def format_currency(value):
    """Formats an integer or float as a currency string with '$' and ','."""
    return f"${value:,.2f}" if isinstance(value, float) else f"${value:,}"


def crop_table(image_path, output_path):
    """
    Crops whitespace above and below the table in the given image.

    Parameters:
    - image_path: Path to the input image.
    - output_path: Path to save the cropped image.
    """
    # Load the image
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to create a binary image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Get bounding box of the largest contour (assumed to be the table)
    x, y, w, h = cv2.boundingRect(contours[0])

    # Crop the table
    cropped = image[y:y+h, x:x+w]

    # Save the cropped image
    cv2.imwrite(output_path, cropped)

    return output_path

def save_table_as_image(df, title, filename):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("tight")
    ax.axis("off")

    # Create the table with alternating row colors
    colors = [['#f0f0f0' if i % 2 == 0 else '#ffffff' for _ in range(len(df.columns))] for i in range(len(df))]

    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center',
                     cellColours=colors)

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width([i for i in range(len(df.columns))])

    # Format column headers
    for (i, key) in enumerate(df.columns):
        cell = table[0, i]
        cell.set_text_props(weight='bold', fontsize=12)
        cell.set_facecolor("#cce5ff")  # Light blue background for headers

    # Set border styles
    for key, cell in table.get_celld().items():
        cell.set_edgecolor("black")
        cell.set_linewidth(1.5)  # Thicker borders

    # Add a title
    plt.title(title, fontsize=14, fontweight='bold', pad=15)

    # Save the table
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    crop_table(filename, filename)
    plt.close()

def extract_prices(response, estimate_property_price, base_property, sold_market_info, on_market_info, format_currency):
    pricing = []
    try:
        match = re.search(r"\*\*(.*?)\*\*", response) or re.search(r"\((.*?)\)", response)
        response_clean = match.group(1) if match else response
        response_clean = response_clean.replace(",", "")
        values = re.findall(r"\d+", response_clean)
        pricing = [int(value.strip()) for value in values]
    except Exception:
        pricing = estimate_property_price(base_property, sold_market_info, on_market_info)

    pricing = [format_currency(price) for price in pricing]
    return pricing

def openai_responce(input_text,reason =False):
    if reason == True:
        response = client.chat.completions.create(
                model="o3-mini",
                reasoning_effort="medium",
                messages=[{"role": "developer", "content": "You are a real estate appraisal expert."},
                        {"role": "user", "content": input_text}],
            )
    else:
        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "developer", "content": "You are a real estate appraisal expert."},
                        {"role": "user", "content": input_text}],
            )
    return response.choices[0].message.content

def format_property_info_comp_past(data, lat_i, lon_i,main_add):

    formatted_properties = []
    pricing = []
    pic_links = []
    source_links = []

    addresses = [main_add['address']]
    sale_prices = [main_add['zestimate']]
    square_footages = [main_add['square_footage']]
    beds = [main_add['totalBedrooms']]
    baths = [main_add['totalBathrooms']]
    distance_miles = ['--']
    sold_date = ['--']

    if data==None:
        return formatted_properties,pricing,pic_links
    properties = data['searchResults']

    for prop in properties:
        try:
            # score checking for max missing values
            score = 0
            # beds and bath 0.5 each
            if prop['property'].get('bedrooms',"--") == "--":
                score += 0.5
            if prop['property'].get('bathrooms',"--") == "--":
                score += 0.5
            # square footage 2
            if prop['property'].get('livingArea',"--") == "--":
                score += 2
            # lot size 1
            if prop['property'].get('lotSizeWithUnit',"--") == "--":
                score += 1
            # if score is or exceeds 2.5 then skip
            if score >= 2.5:
                continue 
            # Extract basic details
            address = f"{prop['property']['address']['streetAddress']}, {prop['property']['address']['city']}, {prop['property']['address']['state']} {prop['property']['address']['zipcode']}"
            if address == main_add['address']:
                continue
            photo_link = prop['property']['media']['propertyPhotoLinks']['mediumSizeLink']
            supported_formats = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
            print(photo_link)
            if not photo_link.lower().endswith(supported_formats):
                print("Unsupported image format")
                continue
            market_value = prop['property']['estimates'].get('zestimate',"--")
            if market_value != "--":
                market_value = format_currency(market_value)
            sale_amount= prop['property']['price'].get('value',"--")
            if sale_amount != "--":
                sale_amount = format_currency(sale_amount)
            bedrooms = prop['property'].get('bedrooms',"--")
            bathrooms = prop['property'].get('bathrooms',"--")
            square_feet = prop['property'].get('livingArea',"--")
            try:
                square_feet = convert_lot_size(square_feet)
                square_feet = str("{:.2f} sq ft".format(float(square_feet)))
            except:
                square_feet = "--"
            square_footages.append(square_feet)
            year_built = prop['property'].get('yearBuilt',"--")
            try:
                lot_size = prop['property']['lotSizeWithUnit'].get('lotSize',"--")
                lot_size = convert_lot_size(lot_size)
                lot_size = str("{:.2f} sq ft".format(float(lot_size)))
            except:
                lot_size = "--"
            try:
                tax = prop['property']['taxAssessment'].get('taxAssessedValue',"--")
            except:
                tax = "--"
                print("Tax not found")
            if tax != "--":
                tax = format_currency(tax)
            zpid = prop['property'].get('zpid',"--")
            listing = prop['property']['listing'].get('listingStatus',"--")
            if not listing == "forSale":
                sale_date = prop['property']['lastSoldDate']
            else:
                sale_date = prop['property']['daysOnZillow']
                if int(sale_date) > 365:
                    sale_date = "Not Available"
            source = generate_zillow_url(address,zpid)
            try:
                distance_from_main = f"{calculate_distance_miles(lat_i,lon_i,prop['property']['location']['latitude'],prop['property']['location']['longitude']):.2f}"
                distance_from_main = str("{:.2f}".format(float(distance_from_main)))
            except:
                distance_from_main = "--"
            sale_date_cal = convert_timestamp_to_date(sale_date)
            sold_date.append(sale_date_cal)
            addresses.append(address)
            sale_prices.append(sale_amount)
            beds.append(bedrooms)
            baths.append(bathrooms)
            distance_miles.append(distance_from_main)

            # Format the details
            formatted_info = f"""- Address: {address}
                - Initial Asking Price: {market_value}
                - Sale Price: {sale_amount}
                - Distance from Main Property: {distance_from_main} miles
                - Specifications: {bedrooms} bedrooms, {bathrooms} bathrooms
                - Square Footage: {square_feet}
                - Lot Size: {lot_size}
                - Year Built: {year_built}
                - Sale Date: {sale_date_cal}
                - Assessed Value: {tax}"""
            formatted_properties.append(formatted_info)
            source_links.append(source)
            pic_links.append(photo_link)
            try:
                pricing.append(int(sale_amount))
            except:
                pass
            
        except Exception as e:
            print("ERROR_DURING_FORMATING",e)
            pass
        if len(formatted_properties) >= 6:
            break
    past_market_grid = {"Address":addresses,"Sale Price":sale_prices,"Square Footage":square_footages,"Bedrooms":beds,"Bathrooms":baths,"Distance (miles)":distance_miles,"Sold Date":sold_date}
    # Combine all formatted properties into one string
    return formatted_properties,pricing,pic_links,source_links,past_market_grid

def format_property_info_comp_current(data, lat_i, lon_i,main_add):

    formatted_properties = []
    pricing = []
    pic_links = []
    source_links = []

    addresses = [main_add['address']]
    sale_prices = [main_add['zestimate']]
    square_footages = [main_add['square_footage']]
    beds = [main_add['totalBedrooms']]
    baths = [main_add['totalBathrooms']]
    distance_miles = ['--']
    days_on_market = ['--']
    if data==None:
        return formatted_properties,pricing,pic_links,source_links
    
    properties = data['searchResults']
    total_prop_onmarket = len(properties)
    skipped_props = 0
    for prop in properties:
        try:
            # score checking for max missing values
            
            score = 0
            # beds and bath 0.5 each
            if prop['property'].get('bedrooms',"--") == "--":
                score += 0.5
            if prop['property'].get('bathrooms',"--") == "--":
                score += 0.5
            # square footage 2
            if prop['property'].get('livingArea',"--") == "--":
                score += 2
            # lot size 1
            if prop['property'].get('lotSizeWithUnit',"--") == "--":
                score += 1
            # if score is or exceeds 2.5 then skip
            if score > 2.4:
                # make sure at least 3 properties are returned
                skipped_props += 1
                if skipped_props >= total_prop_onmarket - 3:
                    pass
                else:
                    continue 
            
            # Extract basic details
            address = f"{prop['property']['address']['streetAddress']}, {prop['property']['address']['city']}, {prop['property']['address']['state']} {prop['property']['address']['zipcode']}"
            if address == main_add:
                continue
            photo_link = prop['property']['media']['propertyPhotoLinks']['mediumSizeLink']
            supported_formats = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
            print(photo_link)
            if not photo_link.lower().endswith(supported_formats):
                print("Unsupported image format")
                continue
            market_value = prop['property']['estimates'].get('zestimate',"--")
            if market_value != "--":
                market_value = format_currency(market_value)
            sale_amount= prop['property']['price'].get('value',"--")
            if sale_amount != "--":
                sale_amount = format_currency(sale_amount)
            bedrooms = prop['property'].get('bedrooms',"--")
            bathrooms = prop['property'].get('bathrooms',"--")
            square_feet = prop['property'].get('livingArea',"--")
            try:
                square_feet = convert_lot_size(square_feet)
                square_feet = str("{:.2f} sq ft".format(float(square_feet)))
            except:
                square_feet = "--"
            square_footages.append(square_feet)
            year_built = prop['property'].get('yearBuilt',"--")
            try:
                lot_size = prop['property']['lotSizeWithUnit'].get('lotSize',"--")
                lot_size = convert_lot_size(lot_size)
                lot_size = str("{:.2f} sq ft".format(float(lot_size)))
            except:
                lot_size = "--"
            try:
                tax = prop['property']['taxAssessment'].get('taxAssessedValue',"--")
            except:
                tax = "--"
                print("Tax not found")
            if tax != "--":
                tax = format_currency(tax)
            zpid = prop['property'].get('zpid',"--")
            listing = prop['property']['listing'].get('listingStatus',"--")
            if not listing == "forSale":
                sale_date = "Already Sold"
            else:
                sale_date = prop['property']['daysOnZillow']
                if int(sale_date) > 365:
                    sale_date = "Not Available"
            if zpid == "--":
                source = "--"
            else:
                source = generate_zillow_url(address,zpid)
            try:
                distance_from_main = f"{calculate_distance_miles(lat_i,lon_i,prop['property']['location']['latitude'],prop['property']['location']['longitude']):.2f}"
                distance_from_main = str("{:.2f}".format(float(distance_from_main)))
            except:
                distance_from_main = "--"
            sale_date_cal = get_past_date(sale_date)
            if market_value == "--":
                market_value = sale_amount
            days_on_market.append(sale_date)
            addresses.append(address)
            sale_prices.append(sale_amount)
            beds.append(bedrooms)
            baths.append(bathrooms)
            distance_miles.append(distance_from_main)
            # Format the details
            formatted_info = f"""- Address: {address}
                - Initial List Date: {sale_date_cal}
                - Days on Market: {sale_date}
                - Initial List Price: {market_value}
                - Current Price: {sale_amount}
                - Distance from Main Property: {distance_from_main} miles
                - Specifications: {bedrooms} bedrooms, {bathrooms} bathrooms
                - Square Footage: {square_feet}
                - Lot Size: {lot_size}
                - Year Built: {year_built}
                - Assessed Value: {tax}"""
            formatted_properties.append(formatted_info)
            source_links.append(source)
            pic_links.append(photo_link)
            try:
                pricing.append(int(sale_amount))
            except:
                pass
            
        except Exception as e:
            print("ERROR_DURING_FORMATING",e)
            pass
        if len(formatted_properties) >= 6:
            break
    # Combine all formatted properties into one string
    on_market_grid = {"Address":addresses,"Current price":sale_prices,"Square Footage":square_footages,"Bedrooms":beds,"Bathrooms":baths,"Distance (miles)":distance_miles,"Days on Market":days_on_market}
    return formatted_properties,pricing,pic_links,source_links,on_market_grid


def generate_report(type_report, data, REPORT_DIR):

    if type_report == "buyer":

        print(data['address'])
        street_address, city, state,zip_code = split_address(data['address'])
        try:
            data['square_footage'] = convert_lot_size(data['square_footage'])
            data['square_footage'] = str("{:.2f} sq ft".format(float(data['square_footage'])))
        except:
            data['square_footage'] = "(square footage Not Available)"
        data['zestimate'] = format_currency(data['zestimate'])
        coparable_sales = []
        postal_code_list = []
        soure_link_past = []
        photo_links = []
        pricing = []
        orignal_bed = data['totalBedrooms']
        orignal_bath = data['totalBathrooms']
        for i in range(min(data['totalBathrooms'],data['totalBedrooms'])):
            data['totalBedrooms'] = orignal_bed - i
            data['totalBathrooms'] = orignal_bath - i
            comparable_sales_json = get_comps(data,sold=True)
            sold_market_info = get_pricing_components(comparable_sales_json,sold=True)
            coparable_sale,sale_amounts,photo_link,soure_link,past_market_grid = format_property_info_comp_past(comparable_sales_json, data['latitude'], data['longitude'],data)

            coparable_sales.extend(coparable_sale)
            pricing.extend(sale_amounts)
            soure_link_past.extend(soure_link)
            photo_links.extend(photo_link)
            if len(coparable_sales) >= 3:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
                if len(coparable_sales) >= 6:
                    coparable_sale = coparable_sale[:6]
                
                break
            else:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
        tag = False
        for i in range(min(data['totalBathrooms'],data['totalBedrooms'])):
            data['totalBedrooms'] = orignal_bed - i
            data['totalBathrooms'] = orignal_bath - i
            current_market_data = get_comps(data,sold=False)
            on_market_info = get_pricing_components(current_market_data,sold=False)
            current_market_data,sale_amounts,photo_links_current,soure_link_current,on_market_grid = format_property_info_comp_current(current_market_data, data['latitude'], data['longitude'],data)
            if len(current_market_data) >= 3:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
                if len(current_market_data) >= 6:
                    current_market_data = current_market_data[:6]
                break
            else:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
        pricing.extend(sale_amounts)
        if int(data["days_on_market"]) > 365:
            data["days_on_market"] = "Not Available"
        #print(current_market_data)
        data['Assessed_value'] = format_currency(data['Assessed_value'])
        try:
            data['Porperty_size'] = convert_lot_size(data['Porperty_size'])
            data['Porperty_size'] = str("{:.2f} sq ft".format(float(data['Porperty_size'])))
        except:
            data['Porperty_size'] = "N/A"
        df_past_sales = pd.DataFrame(past_market_grid)
        df_on_market = pd.DataFrame(on_market_grid)
        annual_propert_tax = get_annual_tax(data)
        annual_propert_tax = format_currency(annual_propert_tax)
        main_input_data = f"""-	Address: {data['address']}
        -   Days on Market: {data["days_on_market"]} 
        -   Pricing: {data['zestimate']}
        -   Specifications: {data['totalBedrooms']} bedrooms, {data['totalBathrooms']} bathrooms, approximately {data['square_footage']}
        -   Lot Size: {data['Porperty_size']}
        -   Current Annual Tax: {annual_propert_tax}
        -   Assessed Value: {data['Assessed_value']}
        """
        save_table_as_image(df_past_sales, "Past Sales Data", "utils/past_sales.jpg")
        save_table_as_image(df_on_market, "On Market Data", "utils/on_market.jpg")
        base_property = {
                'asking_price': data['zestimate'],
                'beds': data['totalBedrooms'],
                'baths': data['totalBathrooms'],
                'lot_size': convert_lot_size(data['Porperty_size']),
                'sqft': convert_lot_size(data['square_footage'])
            }
        input_propert = f"Base Property:\n{base_property}\n\nPast Sales:\n" + "\n".join(str(p) for p in past_market_grid.items()) + "\n\nOn Market:\n" + "\n".join(str(o) for o in on_market_grid.items())
        input_text = f"Above is the data provided by property API based on the inserted address of the user. Along side we have other comparable listings in the area. Assess the home value based on the comparables above and also include the beds, baths etc. First find out per square feet price and then compare it to assess the estimated home value.  Analyze the following property data and return low mid and high int sale pricing for the base property only these 3 seperated by , like this (lowprice, midprice, highprice) so that i can seperate them and extract all 3 of them nothing else in responce.\n   Note please only send me the values nothing else in this format (lowprice, midprice, highprice)\n{input_propert}"
        response = openai_responce(input_text)
        pricing = []
        pricing =  extract_prices(response, estimate_property_price, base_property, sold_market_info, on_market_info, format_currency)
        input_text = f"{input_propert}\ni am thinking of buying this property.All the values are from Zillow and this will be used to provide a basis for the price they are going to charge and ideally a few suggestions, low or high depending on the circumstances. based on this information check for the price trend for sold market property and check for supply and demand on current market and tell me in 2 lines should for this property what should be the asking price for it.\n Note that i havent set a price yet so use word recommendation instead of \"your asking price\""
        recommendation = openai_responce(input_text,reason=True)
        additional_consideration_text = f"Base Property:\n{base_property}\nI am thinking of buying this property. in 2 line tell me what are the additional considerations for this property"
        additional_consideration = openai_responce(additional_consideration_text)
        print(pricing)
        path_report = generate_buyer_report(main_input_data,data['main_img_url'],pricing,coparable_sales,photo_links,soure_link_past,current_market_data,photo_links_current,soure_link_current,tag,recommendation,additional_consideration,REPORT_DIR+"/")
        return path_report
    
    elif type_report == "seller":
        print(data['address'])
        aa, city, state,zip_code = split_address(data['address'])
        coparable_sales = []
        postal_code_list = []
        pricing = []
        orignal_bed = data['totalBedrooms']
        orignal_bath = data['totalBathrooms']
        for i in range(min(data['totalBathrooms'],data['totalBedrooms'])):
            data['totalBedrooms'] = orignal_bed - i
            data['totalBathrooms'] = orignal_bath - i
            comparable_sales_json = get_comps(data,sold=True)
            sold_market_info = get_pricing_components(comparable_sales_json,sold=True)
            coparable_sale,sale_amounts,photo_links,soure_link_past,past_market_grid = format_property_info_comp_past(comparable_sales_json, data['latitude'], data['longitude'],data)
            if len(coparable_sale) >= 3:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
                if len(coparable_sale) >= 6:
                    coparable_sale = coparable_sale[:6]
                break
            else:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
        
        coparable_sales.extend(coparable_sale)
        pricing.extend(sale_amounts)
        if len(coparable_sales) >= 6:
            coparable_sale = coparable_sale[:6]
                
        tag = False
        for i in range(min(data['totalBathrooms'],data['totalBedrooms'])):
            data['totalBedrooms'] = orignal_bed - i
            data['totalBathrooms'] = orignal_bath - i
            current_market_data = get_comps(data,sold=False)
            on_market_info = get_pricing_components(current_market_data,sold=False)
            current_market_data,sale_amounts,photo_links_current,soure_link_current,on_market_grid = format_property_info_comp_current(current_market_data, data['latitude'], data['longitude'],data)
            if len(current_market_data) >= 3:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
                if len(current_market_data) >= 6:
                    current_market_data = current_market_data[:6]
                break
            else:
                data['totalBedrooms'] = orignal_bed
                data['totalBathrooms'] = orignal_bath
        pricing.extend(sale_amounts)
        data['zestimate'] = format_currency(data['zestimate'])
        #data['totalMarketValue'] = format_currency(data['totalMarketValue'])
        pricing = []
        base_property = {
                'asking_price': data['zestimate'],
                'beds': data['totalBedrooms'],
                'baths': data['totalBathrooms'],
                'lot_size': data['Porperty_size'],
                'sqft': data['square_footage']
            }
        df_past_sales = pd.DataFrame(past_market_grid)
        df_on_market = pd.DataFrame(on_market_grid)
        save_table_as_image(df_past_sales, "Past Sales Data", "utils/past_sales.jpg")
        save_table_as_image(df_on_market, "On Market Data", "utils/on_market.jpg")
        input_propert = f"Base Property:\n{base_property}\n\nPast Sales:\n" + "\n".join(str(p) for p in past_market_grid.values()) + "\n\nOn Market:\n" + "\n".join(str(o) for o in on_market_grid.values())
        input_text = f"Suppose you are a appraisal expert. Above is the data provided by property API based on the inserted address of the user. Along side we have other comparable listings in the area. Assess the home value based on the comparables above and also include the beds, baths etc. First find out per square feet price and then compare it to assess the estimated home value.  Analyze the following property data and return low mid and high int sale pricing for the base property only these 3 seperated by , like this (lowprice, midprice, highprice) so that i can seperate them and extract all 3 of them nothing else in responce.\n   Note please only send me the values nothing else in this format (lowprice, midprice, highprice)\n{input_propert}"
        # OpenAI API request
        response = openai_responce(input_text)
        pricing = []
        pricing = extract_prices(response, estimate_property_price, base_property, sold_market_info, on_market_info, format_currency)
        input_text = f"{input_propert}\nI am selling this property,all the values are from Zillow and nothing has been setup yet , the purpose of this is to provide a basis for the price i am going to charge and ideally a few suggestions, low or high depending on the circumstances. based on past trends and current market what you should recommend about pricing based on supply and demand and based on pricing trends in 2 3 lines"
        recommendation = openai_responce(input_text,True)
        additional_consideration_text = f"Base Property:\n{base_property}\nI am thinking of selling this property. in 2 line tell me what are the additional considerations for this property"
        additional_consideration = openai_responce(additional_consideration_text)
        data['Assessed_value'] = format_currency(data['Assessed_value'])
        annual_propert_tax = get_annual_tax(data)
        annual_propert_tax = format_currency(annual_propert_tax)
        main_input_data = f"""-	Address: {data['address']}
        -   Specifications: {data['totalBedrooms']} bedrooms, {data['totalBathrooms']} bathrooms, approximately {data['square_footage']} sq ft
        -   Lot Size: {data['Porperty_size']} sq ft
        -   Current Annual Tax: {annual_propert_tax}
        -   Assessed Value: {data['Assessed_value']}
        -   Estimated Property Pricing: {pricing[0]} - {pricing[1]}    (based on comparables)
        """

        path_report = generate_report_seller(main_input_data,data['main_img_url'],pricing,coparable_sales,photo_links,soure_link_past,current_market_data,photo_links_current,soure_link_current,tag,recommendation,additional_consideration,REPORT_DIR+"/")
        return path_report
    
    else:
        return "Invalid report type. Use 'buyer' or 'seller'."
