from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any,Optional
from utils.utils import get_property_info,generate_report
import os
import json
from urllib.parse import unquote

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origins in production, e.g., ["https://frontend.com"]
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_URL = "http://127.0.0.1:8000"
REPORTS_DIR = "reports"

# Define the input data model
class ReportRequest(BaseModel):
    report_type: str  # "buyer" or "seller"re
    data: Dict[str, Any]  # Data for generating the report

class DataRequest(BaseModel):
    property_address: str

def check_missing_values(property_info):
    required_keys = [
        'address', 'days_on_market', 'main_img_url', 'url', 'zestimate',
        'Assessed_value', 'square_footage', 'totalBathrooms', 'totalBedrooms',
        'Porperty_size', 'specifications', 'longitude', 'latitude'
    ]
    
    missing_keys = [key for key in required_keys if key not in property_info or property_info[key] in [None, "N/A", "", 0]]

    if missing_keys:
        return {"missing_keys": missing_keys, "status": "Some required values are missing"}
    return True

def fix_space_link(url):
    return url.replace("%20", "+").replace(" ", "+").replace("\"","").replace(",","%2C") 


@app.get("/generate-report-new/")
async def generate_report_endpoint(
    report_type: str,
    address: str,
    days_on_market: int,
    main_img_url: str,
    url: str,
    zestimate: float,
    assessed_value: float,
    square_footage: int,
    totalBathrooms: int,
    totalBedrooms: int,
    property_size: int,
    specifications: str,
    longitude: float,
    latitude: float
):
    if report_type not in ["buyer", "seller"]:
        raise HTTPException(status_code=400, detail="Invalid report type. Use 'buyer' or 'seller'.")

    main_img_url = fix_space_link(main_img_url)
    print(main_img_url)
    # Convert parameters into a dictionary (same structure as before)
    data = {
        "address": address,
        "days_on_market": days_on_market,
        "main_img_url": main_img_url,
        "url": url,
        "zestimate": zestimate,
        "Assessed_value": assessed_value,
        "square_footage": square_footage,
        "totalBathrooms": totalBathrooms,
        "totalBedrooms": totalBedrooms,
        "Porperty_size": property_size,
        "specifications": specifications,
        "longitude": longitude,
        "latitude": latitude,
    }

    # Perform data validation
    check_return = check_missing_values(data)
    if check_return != True:
        return check_return

    # Generate the report
    report_path = generate_report(report_type, data, REPORTS_DIR)

    # Create a download link
    report_name = os.path.basename(report_path)
    download_link = f"{BASE_URL}/download/{report_name}"

    return {"message": "Report generated successfully.", "download_link": download_link}

@app.post("/generate-report/")
async def generate_report_endpoint(request: ReportRequest):
    if request.report_type not in ["buyer", "seller"]:
        raise HTTPException(status_code=400, detail="Invalid report type. Use 'buyer' or 'seller'.")

    # Format the main input data
    check_return = check_missing_values(request.data)
    if check_return != True:
        return check_return
    # Generate the report
    report_path = generate_report(request.report_type, request.data, REPORTS_DIR)

    # Create a download link
    report_name = os.path.basename(report_path)
    download_link = f"{BASE_URL}/download/{report_name}"

    return {"message": "Report generated successfully.", "download_link": download_link}
@app.get("/get_property_info")
async def get_address(property_address:str):
    print(property_address)
    try:
        data = get_property_info(property_address)
        #print main image url 
        if data and 'main_img_url' in data:
            print("Main Image URL:", data['main_img_url'])
        return data
    except:
        pass
    return None


from fastapi.responses import FileResponse
import re
def custom_decode(report_name: str) -> str:
    # Replace '%23' with '#' using regex. You can add more substitutions as needed.
    return re.sub(r'%23', '#', report_name)

@app.get("/download/{report_name:path}")
async def download_report(report_name: str = Path(..., regex=".*", description="Encoded report name")):
    decoded_report_name = custom_decode(report_name)
    report_path = os.path.join(REPORTS_DIR, decoded_report_name)
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found.")
    
    return FileResponse(path=report_path, filename=decoded_report_name, media_type="application/pdf")
