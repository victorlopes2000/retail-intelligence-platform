# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2, logging
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
load_dotenv()  # load .env file
class RetailIntelligencePipeline:
    def process_item(self, item, spider):
        return item
    
class PostgresPipeline:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.create_connection()
        self.create_table()
        
    def create_connection(self):
        try:
            self.connection = psycopg2.connect(
                host=os.getenv('DB_HOST',"localhost"),
                user=os.getenv('DB_USER',"postgres"),
                password=os.getenv('DB_PASSWORD',"postgres"),
                dbname=os.getenv('DB_NAME',"retail_intelligence"),
                port=os.getenv('DB_PORT',5432),
            )
            self.cur = self.connection.cursor()
            self.logger.info("PostgreSQL connected successfully")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")   
        
    def create_table(self):
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    price FLOAT,
                    bestseller TEXT,
                    currency VARCHAR(10),
                    image_url TEXT,
                    rating FLOAT,
                    review_count INT,
                    product_url TEXT UNIQUE,
                    platform VARCHAR(50)
                )
            """)
            self.connection.commit()
            self.logger.info("Table created (if not exists)")
        except Exception as e:
            self.logger.error(f"Table creation failed: {e}")
    
    def process_item(self, item, spider):
        self.store_db(item)
        return item
    
    def store_db(self, item):
        try:
            if item.get('price') is not None:
                self.cur.execute("""
                    INSERT INTO products (
                        title, price, bestseller, currency, image_url,
                        rating, review_count, product_url, platform
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (product_url) DO UPDATE SET
                        title = EXCLUDED.title,
                        price = EXCLUDED.price,
                        bestseller = EXCLUDED.bestseller,
                        currency = EXCLUDED.currency,
                        image_url = EXCLUDED.image_url,
                        rating = EXCLUDED.rating,
                        review_count = EXCLUDED.review_count,
                        platform = EXCLUDED.platform
                """, (
                    item.get("title"),
                    float(item.get("price")) if item.get("price") else None,
                    item.get("bestseller") if item.get("bestseller") else None,
                    item.get("currency") if item.get("currency") else None,
                    item.get("image_url") if item.get("image_url") else None,
                    float(item.get("rating")) if item.get("rating") else None,
                    int(item.get("review_count")) if item.get("review_count") else None,
                    item.get("product_url"),
                    item.get("platform") if item.get("platform") else None
                ))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Insert/Update failed: {e} | Item: {item}")
    
    def close_spider(self, spider):
        try:
            self.cur.close()
            self.connection.close()
            self.logger.info("PostgreSQL connection closed")
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")