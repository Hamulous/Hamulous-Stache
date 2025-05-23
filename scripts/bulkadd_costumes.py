import json
import re
import os

def clean_string(input_string):
    return re.sub(r'[^a-zA-Z0-9_-]', '', input_string)

# Ask user for path to Propertysheets.json
propertysheet_path = input("Enter the full path to Propertysheets.json: ").strip().strip('"')

# Validate file existence
if not os.path.exists(propertysheet_path):
    raise FileNotFoundError(f"The file at '{propertysheet_path}' does not exist.")

# Extract directory to save outputs
output_dir = os.path.dirname(propertysheet_path)

with open(propertysheet_path, "r") as f:
    property_data = json.load(f)

def transform_costumes(costume):
    costume_id = costume.get("CostumeID")
    plant_type_name = clean_string(costume.get("PlantTypeName").lower())
    friendly_name = clean_string(costume.get("FriendlyName").lower())

    products = {
        "aliases": [
            f"com.popcap.pvz2.costume.{plant_type_name}.{friendly_name}.nonconsume"
        ],
        "objclass": "StoreProductProps",
        "objdata": {
            "IsAdPlacement": False,
            "IsFree": False,
            "LawnShortDescription": f"PRODUCT_COSTUME_{plant_type_name.upper()}_{friendly_name.upper()}_NONCONSUME_S",
            "Name": f"Costume - {plant_type_name.capitalize()} {friendly_name.capitalize()}",
            "ObjectCount": 1,
            "ObjectItem": str(costume_id),
            "ObjectType": "costume",
            "Price": 0,
            "PriceCoins": "1000",
            "PriceGems": "0",
            "PriceMints": "0",
            "Sku": f"com.popcap.pvz2.costume.{plant_type_name}.{friendly_name}.nonconsume"
        }
    }

    market_schedule = {
        "Comment": str(costume_id),
        "Category": "",
        "Priority": "",
        "ABTest": "",
        "PromotionGroup": "",
        "AdditionalSegment": "",
        "SmartKey": "",
        "SoftCurrency": "",
        "SoftCost": -1,
        "MaxPurchase": -1,
        "SoftCostPerPurchase": -1,
        "Visuals": "RTID(0)",
        "Sku": [
            f"com.popcap.pvz2.costume.{plant_type_name}.{friendly_name}.nonconsume",
            f"com.popcap.pvz2.costume.{plant_type_name}.{friendly_name}.nonconsume"
        ]
    }

    return products, market_schedule

def process_json(data):
    products_list = []
    market_schedule_list = []

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                result = process_json(value)
                products_list.extend(result[0])
                market_schedule_list.extend(result[1])
            elif key == "objclass" and value == "CostumePropertySheet":
                costume_list = data.get("objdata", {}).get("CostumeList", [])
                for costume in costume_list:
                    products, market_schedule = transform_costumes(costume)
                    products_list.append(products)
                    market_schedule_list.append(market_schedule)

    elif isinstance(data, list):
        for item in data:
            result = process_json(item)
            products_list.extend(result[0])
            market_schedule_list.extend(result[1])

    return products_list, market_schedule_list

products_data, market_schedule_data = process_json(property_data)

with open(os.path.join(output_dir, "products_output.json"), "w") as f:
    json.dump(products_data, f, indent=4)

with open(os.path.join(output_dir, "market_schedule_output.json"), "w") as f:
    json.dump(market_schedule_data, f, indent=4)
