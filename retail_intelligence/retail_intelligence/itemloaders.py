from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst
import re
def clean_text(value):
    cleaned = re.sub(r'\s+', ' ', value).strip()  # multiple spaces + newlines remove
    return cleaned

def clean_currency(value):
    if not value or value.strip() == "":
        return "$"   # default fallback
    return value.strip()

def clean_rating(value):
    try:
        return float(value.split()[0])
    except (ValueError, AttributeError, IndexError):
        return None
def clean_price(value):
    if not value:
        return None
    match = re.search(r"[\d,.]+", value)
    if match:
        cleaned = match.group(0).replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None

def clean_review_count(value):
    if not value or value.lower() in ["n/a", "null"]:
        return None
    try:
        cleaned = re.sub(r"[^\d]", "", value)  # comma aur non-digit remove
        return int(cleaned)
    except ValueError:
        return None
    
def default_value(value, default=None):
    return value if value else default

class ProductLoader(ItemLoader):
    default_input_processor = MapCompose(clean_text,default_value)  # <- Apply on every Field
    default_output_processor = TakeFirst()
       # define the fields for your item here like:
    title_in = MapCompose()
    price_in = MapCompose(clean_price)
    currency_in = MapCompose(clean_currency)
    image_url_in = MapCompose()
    product_url_in = MapCompose()
    rating_in = MapCompose( clean_rating)
    review_count_in = MapCompose(clean_review_count)
    brand_in = MapCompose()
    bestseller_in = MapCompose()
    platform_in = MapCompose() 
