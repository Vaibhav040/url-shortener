import boto3
import string
import random
from datetime import datetime
from app.config import Settings

dynamodb = boto3.resource("dynamodb", region_name=Settings.aws_region)
table = dynamodb.Table(Settings.dynamo_table)

def generate_short_code(length: int = Settings.short_code_length) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))

def save_url(original_url: str, custom_code: str = None) -> dict:
    short_code = custom_code if custom_code else generate_short_code()

    item ={
        "short_code": short_code,
        "original_url": original_url,
        "visit_count": 0,
        "created_at": datetime.utcnow().isoformat,
    }

    table.put_item(
        Item=item,
        conditionExpression="attribute_not_exists(short_code)"
    )
    return item

def get_url(short_code: str) -> dict | None:
    response = table.get_item(key={"short_code": short_code})
    return response.get("Item")

def increment_visit_count(short_code: str):
    table.update_item(
        Key={"short_code": short_code},
        UpdateExpression="ADD_visit_count : inc",
        ExpressionAttributeValues={":inc": 1}
    )