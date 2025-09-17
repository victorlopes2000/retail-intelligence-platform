# Retail Intelligence Platform

An **enterprise-grade competitor intelligence solution** for retail and ecommerce.  
This platform scrapes data from major retailers (e.g., Walmart, Amazon, Target), processes it via ETL workflows, stores in PostgreSQL, and provides interactive analytics with Streamlit.

---

## 🚀 Features
- **Multi-site scraping** with Scrapy + Playwright (Walmart, Amazon, Target).
- **ETL Pipeline** → Extract (scraping), Transform (cleaning/normalization), Load (PostgreSQL).
- **Historical Trends** → 30-day price, stock, and rating analysis.
- **Review Analysis** → AI-powered sentiment analysis (positive/negative/neutral).
- **Streamlit Dashboard** → Visualize competitor trends, configure alerts, and export data.

---

## 🛠️ Tech Stack
- **Scraping**: Scrapy + Playwright  
- **Database**: PostgreSQL  
- **ETL**: Python (data cleaning + normalization)  
- **Dashboard**: Streamlit (charts, tables, exports)  


## ⚡ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/retail-intelligence-platform.git
cd retail-intelligence-platform
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
### 3. Install Playwright
```bash
playwright install
```
### 4. Create .env File
```bash
retail_intelligence/
│
├── retail_intelligence/   # Scrapy project files
│   ├── settings.py
│   ├── spiders/
│   └── ...
├── .env                   # 🔑 Environment variables here
├── scrapy.cfg
├── requirements.txt
└── README.md
```
### 5. Inside .env File 
```bash
SCRAPEOPS_API_KEY=your_scrapeops_api_key
```
### 6. Setup PostgreSQL Database
```sql
CREATE DATABASE retail_intelligence;
```

Configure connection in `.env` file:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_intelligence
DB_USER=your_username
DB_PASS=your_password
```

### 7. Run the Scrapy spider with custom arguments to fetch products from the given URLs and save their HTML content locally.
```bash
scrapy crawl snapshot_spider -a query="mobile" -a product_limit=150  
```

### 8. Run Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

## 🔹 License
This project is licensed under the **MIT License** – completely free for both personal and commercial use.  
See the [LICENSE](LICENSE) file for details.  

---

## 🔹 Author
👨‍💻 Created & maintained by [Shahzaib Ali](https://github.com/shahzaib-1-no)  
📬 For collaboration or freelance work: **sa4715228@gmail.com**  
