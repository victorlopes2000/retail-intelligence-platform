from collections.abc import Iterable
from typing import Any
import scrapy, os, logging, sys 
from scrapy_playwright.page import PageMethod
from urllib.parse import urlencode 
from urllib.parse import urljoin as py_urljoin
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class SnapshotSpiderSpider(scrapy.Spider):
    name = "snapshot_spider"    
    def __init__(self, query="laptop", product_limit=10, *args, **kwargs):
        """
        Constructor for the SnapshotSpiderSpider class.

        Responsibilities:
        - Calls the parent class constructor.
        - Configures the spider's logger so that only its logs
        (self.logger) are displayed in the terminal,
        while Scrapy framework logs go to the log file.
        - Loads and validates the SCRAPEOPS_API_KEY from environment variables.
        - Initializes the search query and product scraping limit.
        - Creates a dictionary to track product counts per website.
        """
        # Call the parent class constructor
        super(SnapshotSpiderSpider, self).__init__(*args, **kwargs)

        # SpiderLoggerAdapter ke andar ka real logger access karo
        base_logger = self.logger.logger  

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(formatter)

        # Duplicate na ho is liye check karo
        if not any(isinstance(h, logging.StreamHandler) for h in base_logger.handlers):
            base_logger.addHandler(console_handler)
        
        try:
            # Load the API key from environment variables
            self.API_KEY = os.getenv("SCRAPEOPS_API_KEY")
            # Raise error if API key is not found or empty
            if not self.API_KEY:
                raise ValueError("API Key is empty")
        except Exception as e:
            # Log an critical message if API key is missing
            self.logger.critical(f"SCRAPEOPS_API_KEY Not Found. {e}")
            # Stop the spider since API key is required
            raise SystemExit("API Key missing, exiting spider.")  # It will Stop Spider
        
        # Set the search query for the spider
        self.query = str(query) # Ensure String
        
        # set the product_limit of products for the spider
        self.product_limit= int(product_limit)  # Ensure numeric
        
        # Tracks total products per website
        self.product_count={}
        
    def start_requests(self):
        """
        Entry point for the spider.

        Responsibilities:
        - Defines the initial list of URLs to scrape (Amazon & Walmart search pages).
        - For each URL:
            * Logs the request preparation.
            * Builds a ScrapeOps proxy URL with the API key and target URL.
            * Creates a Scrapy Request configured with Playwright for dynamic rendering.
            * Passes metadata such as original URL, page number, and Playwright settings.
            * Yields the request to the Scrapy engine with callback set to `parse`.
        - Logs success or failure for each request.
        """
        # List of URLs to scrape
        urls=[
            f'https://www.amazon.com/s?k={self.query}&page=1&xpid=aXiBqChDm5LpM&crid=15IL5AN68UBTK&qid=1758021249&sprefix=%2Caps%2C889&ref=sr_pg_1',
            f'https://www.walmart.com/search?q={self.query}&page=1&affinityOverride=default'
        ]
        # Loop through each URL
        for url in urls:
            try:
                self.logger.info(f"[START] Preparing request for URL: {url}")
                # Setup the payload for the proxy (ScrapeOps API key + target URL)
                payload = {"api_key": self.API_KEY, "url": url}
                # Construct the full proxy URL
                proxy_url = "http://proxy.scrapeops.io/v1/?" + urlencode(payload)
                # Generate the Scrapy Request
                self.logger.info(f"[INFO] Proxy URL: {proxy_url}")
                yield scrapy.Request(
                                    url=proxy_url, # Target URL via ScrapeOps proxy
                                    meta={
                                        "playwright": True,
                                        "original_url": url,   # <-- store original target URL
                                        "playwright_page_goto_kwargs": {
                                            "timeout": 120000,   # Maximum page load time (120 seconds)
                                            "wait_until": "domcontentloaded"  # Condition to wait for page load
                                        },
                                        "playwright_page_methods": [
                                            PageMethod("wait_for_timeout", 5000)   # Extra 5 seconds wait
                                        ],
                                        "page_num": 1,                                     
                                    },
                                    callback=self.parse, 
                                    dont_filter=True # Ignore duplicate URL filtering
                                    )
                self.logger.info(f"[SUCCESS] Request yielded for URL: {url}")
            except Exception as e:
                self.logger.error(f"[ERROR] Failed to prepare request for URL: {url} | Exception: {e}")
                continue  # Skip this URL but keep spider running
                
    def make_request(self, url,page_num, website_name):
        """
        Helper method to build and return a Scrapy Request for the next page.

        Responsibilities:
        - Based on the website name (Amazon or Walmart), construct the correct
        target URL for the next page.
        - Wrap the target URL with the ScrapeOps proxy (with API key).
        - Configure Playwright settings for rendering (timeout, wait conditions, etc.).
        - Attach metadata including original URL and current page number.
        - Return a Scrapy Request object with callback set to `parse`.
        """
        if website_name == 'amazon':
            website_url= f'https://www.amazon.com/s?k={self.query}&page=1&xpid=aXiBqChDm5LpM&crid=15IL5AN68UBTK&qid=1758021249&sprefix=%2Caps%2C889&ref=sr_pg_1'
            make= f"https://www.amazon.com{url}"
            payload = {"api_key": self.API_KEY, "url": make}
            # Construct the full proxy URL
            proxy_url = "http://proxy.scrapeops.io/v1/?" + urlencode(payload)
            
        elif website_name == 'walmart':
            website_url= f'https://www.walmart.com/search?q={self.query}&page=1&affinityOverride=default'
            proxy_url= f"http://proxy.scrapeops.io{url}"
        else:
            self.logger.error(f"Next page (Make Request Method) Original Url Not Found")
            
        self.logger.info(f"This is Proxy_url: {proxy_url}")
        return scrapy.Request(
            url=proxy_url,
            meta={
                "playwright": True,
                "original_url": website_url, 
                "playwright_page_goto_kwargs": {
                    "timeout": 120000,   # 120 sec
                    "wait_until": "domcontentloaded"   # "networkidle" ki jagah
                },
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 5000)   # 5 sec wait
                ],
                "page_num":page_num,
            },
            callback=self.parse,
            dont_filter=True
        )
        
    def parse(self, response):
        """
        Parse the product listing page for Amazon or Walmart.
        
        - Identify website (amazon/walmart) based on original_url.
        - Extract product HTML snippets.
        - Save extracted products into HTML files (page-wise).
        - Maintain product count per website.
        - Handle pagination until product_limit is reached or no next page found.
        """
    
        # Use original_url instead of response.url
        original_url = response.meta.get("original_url")
        domain_full = original_url.split("//")[-1].split("/")[0].replace("www.", "")
        website_name = domain_full.split(".")[0]
        
        
        # Get Page Number from  response.meta
        page_num= response.meta.get("page_num",1)
        
        # Check wich website is using
        if website_name == 'amazon':
            self.logger.info("Amazon Website Detected for Product Scraping")
            products = response.css('.puis-card-container').getall()
            next_page_href = response.xpath('//a[contains(@aria-label,"next page")]/@href').get()
            self.logger.info(f"NEXT PAGE HREF OF AMAZON IS HERE {next_page_href}")
        elif website_name == 'walmart':
            self.logger.info("Walmart Website Detected for Product Scraping")
            products = response.xpath('//div[contains(@class, "mb0 ph0-xl pt0-xl bb b--near-white w-25")]').getall()
            next_page_href = response.xpath('//a[contains(@aria-label,"Next Page")]/@href').get()
        else:
            self.logger.error(f"Unknown website '{website_name}' found. Skipping this URL.")
            return  # Skip this response gracefully
            
        # Check If Products Exist
        if not products:
            self.logger.warning(f"[PAGE {page_num}] No products found for {website_name}")
            return
        
        # Create path banado (e.g. html_pages/amazon/)
        folder_path = os.path.join("html_pages", website_name)
        os.makedirs(folder_path, exist_ok=True)

        # Create products file name
        filename = os.path.join(folder_path, f"product_list_page_{page_num}.html")
        
        # Count current Website Products
        count=0
        
        # Write products to file
        try:
            with open (filename, "w" , encoding="utf-8") as f:
                for product in products:
                    if count < self.product_limit:
                        f.write(product + "\n\n")
                        count += 1
                    else: 
                        break
            # Update total product count per website (persistent across pages)
            self.product_count[website_name] = self.product_count.get(website_name, 0) + count
            self.logger.info(f"[SUCCESS] Saved {count} products to {filename}")
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to save products to {filename} | Exception: {e}")
            
        # --- Pagination ---
        total_count = self.product_count.get(website_name, 0)

        if next_page_href and total_count < self.product_limit:
            yield self.make_request(next_page_href, page_num + 1, website_name)
        else:
            self.logger.info(f"[PAGE {page_num}] No NEXT_PAGE_HREF found or limit reached for {website_name}")
        
    def close(self, reason):
        """
        Called automatically when the spider finishes.
        Logs total products per website and overall total.
        """
        if not hasattr(self, 'product_count') or not self.product_count:
            self.logger.warning("No products were counted.")
            return

        total_products = 0
        for web, count in self.product_count.items():
            self.logger.info(f"Total Products from {web}: {count}")
            total_products += count

        self.logger.info(f"Total Products from All Websites: {total_products}")
        
            
