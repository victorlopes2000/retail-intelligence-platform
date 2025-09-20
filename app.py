import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine
import os, math
from dotenv import load_dotenv
from io import BytesIO

# -------------------------------
# ENV + DB CONNECTION
# -------------------------------
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "retail_intelligence")
DB_PORT = os.getenv("DB_PORT", 5432)

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# -------------------------------
# DATA FETCH + CLEAN
# -------------------------------
@st.cache_data
def fetch_products():
    query = """
    SELECT 
        id,
        title,
        COALESCE(price, 0) as price,
        COALESCE(bestseller, 'No') as bestseller,
        COALESCE(currency, 'USD') as currency,
        COALESCE(image_url, '') as image_url,
        COALESCE(rating, 0) as rating,
        COALESCE(review_count, 0) as review_count,
        product_url,
        platform
    FROM products
    ORDER BY title;
    """
    df = pd.read_sql(query, engine)
    df["price"] = df["price"].astype(float)
    df["rating"] = df["rating"].astype(float)
    df["review_count"] = df["review_count"].astype(int)
    df["bestseller"] = df["bestseller"].fillna("No")
    return df

df = fetch_products()

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Retail Products Dashboard", layout="wide")
st.title("🛍️ Retail Products Dashboard")

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.header("Filters")

search_query = st.sidebar.text_input("🔍 Search Product by Title")

platforms = st.sidebar.multiselect(
    "Select Platform",
    options=df["platform"].dropna().unique(),
    default=list(df["platform"].dropna().unique())
)

price_min, price_max = int(df["price"].min()), int(df["price"].max())
price_range = st.sidebar.slider("Price Range", price_min, price_max, (price_min, price_max))

bestseller_filter = st.sidebar.selectbox("Bestseller", ["All", "Yes", "No"])

sort_option = st.sidebar.selectbox(
    "Sort By",
    ["Default", "Price (Low to High)", "Price (High to Low)", "Rating (High to Low)"]
)

# Advanced filters
rating_min, rating_max = st.sidebar.slider("Rating Range", 0.0, 5.0, (0.0, 5.0), 0.1)
min_reviews = st.sidebar.number_input("Minimum Reviews", 0, int(df["review_count"].max()), 0)

# -------------------------------
# FILTERING LOGIC
# -------------------------------
filtered_df = df[
    (df["platform"].isin(platforms)) &
    (df["price"].between(price_range[0], price_range[1])) &
    (df["rating"].between(rating_min, rating_max)) &
    (df["review_count"] >= min_reviews)
]

if bestseller_filter != "All":
    filtered_df = filtered_df[filtered_df["bestseller"] == bestseller_filter]

if search_query:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False)
    ]

# Sorting
if sort_option == "Price (Low to High)":
    filtered_df = filtered_df.sort_values("price")
elif sort_option == "Price (High to Low)":
    filtered_df = filtered_df.sort_values("price", ascending=False)
elif sort_option == "Rating (High to Low)":
    filtered_df = filtered_df.sort_values("rating", ascending=False)

# -------------------------------
# KPIs SECTION
# -------------------------------
if not filtered_df.empty:
    st.subheader("📌 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Products", len(filtered_df))
    col2.metric("Avg Price", f"💲{filtered_df['price'].mean():.2f}")
    col3.metric("Avg Rating", f"{filtered_df['rating'].mean():.1f} ⭐")
    col4.metric("Bestseller %", f"{(filtered_df['bestseller'].eq('Yes').mean()*100):.1f}%")
    col5.metric("Total Reviews", f"{filtered_df['review_count'].sum():,}")

# -------------------------------
# PRODUCT CARDS + PAGINATION
# -------------------------------
st.subheader("🛒 Products")

if filtered_df.empty:
    st.warning("⚠️ No products found for selected filters.")
else:
    items_per_page = 8   # 2 rows × 4 columns
    total_items = len(filtered_df)
    total_pages = (total_items - 1) // items_per_page + 1

    page = st.sidebar.number_input("Page", 1, total_pages, 1, step=1)

    start, end = (page - 1) * items_per_page, page * items_per_page
    page_data = filtered_df.iloc[start:end]

    def star_rating(rating):
        try:
            if rating is None or (isinstance(rating, float) and math.isnan(rating)):
                return "No Rating"
            rating = float(rating)
            full = int(rating)
            return "⭐" * full + "☆" * (5 - full)
        except:
            return "No Rating"

    for row_start in range(0, len(page_data), 4):
        cols = st.columns(4)
        for idx, row in enumerate(page_data.iloc[row_start:row_start+4].itertuples()):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="
                        border:1px solid #ddd;
                        border-radius:14px;
                        padding:12px;
                        margin-bottom:18px;
                        box-shadow:0 3px 6px rgba(0,0,0,0.08);
                        text-align:center;
                        background:#fff;
                        transition:transform 0.2s ease, box-shadow 0.2s ease;
                    " onmouseover="this.style.transform='scale(1.04)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)';"
                      onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 3px 6px rgba(0,0,0,0.08)';">
                        <img src="{row.image_url}" style="width:120px; height:120px; object-fit:contain; margin-bottom:8px;"/>
                        <h4 style="font-size:14px; font-weight:600; color:#222; height:40px; overflow:hidden;">{row.title}</h4>
                        <p style="color:#28a745; font-weight:bold; margin:4px 0;">💲 {row.price} {row.currency}</p>
                        <p style="color:#ff9900; font-size:13px; margin:2px 0;">{star_rating(row.rating)} ({row.review_count})</p>
                        <div style="margin-top:6px;">
                            <span style="background:#007BFF; color:white; padding:3px 8px; border-radius:8px; font-size:11px;">{row.platform}</span>
                            <span style="background:{'#FFD700' if row.bestseller=='Yes' else '#6c757d'}; color:white; padding:3px 8px; border-radius:8px; font-size:11px;">{row.bestseller}</span>
                        </div>
                        <br>
                        <a href="{row.product_url}" target="_blank" style="
                            display:inline-block;
                            padding:6px 12px;
                            border-radius:6px;
                            background:#007BFF;
                            color:white;
                            text-decoration:none;
                            font-size:12px;
                            font-weight:500;
                        ">🔗 Buy Now</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(f"<p style='text-align:center; color:gray;'>Page {page} of {total_pages}</p>", unsafe_allow_html=True)

# -------------------------------
# DOWNLOAD OPTIONS
# -------------------------------
st.subheader("⬇️ Download Filtered Data")

# CSV
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download CSV", csv, "products.csv", "text/csv")

# Excel
excel_buffer = BytesIO()
filtered_df.to_excel(excel_buffer, index=False)
st.download_button("📊 Download Excel", excel_buffer.getvalue(), "products.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# JSON
json_data = filtered_df.to_json(orient="records").encode("utf-8")
st.download_button("🗂️ Download JSON", json_data, "products.json", "application/json")

# -------------------------------
# TOP PRODUCTS
# -------------------------------
if not filtered_df.empty:
    st.subheader("🏆 Top Products")

    top_rated = filtered_df.sort_values("rating", ascending=False).head(5).reset_index(drop=True)
    top_rated.index = top_rated.index + 1
    st.markdown("### ⭐ Top 5 Rated Products")
    st.dataframe(top_rated[["title", "rating", "review_count", "price"]].style.format({"price": "💲{:.2f}", "rating": "{:.1f}"}), use_container_width=True, height=240)

    top_reviewed = filtered_df.sort_values("review_count", ascending=False).head(5).reset_index(drop=True)
    top_reviewed.index = top_reviewed.index + 1
    st.markdown("### 💬 Top 5 Most Reviewed Products")
    st.dataframe(top_reviewed[["title", "rating", "review_count", "price"]].style.format({"price": "💲{:.2f}", "rating": "{:.1f}"}), use_container_width=True, height=240)

# -------------------------------
# INSIGHTS
# -------------------------------
if not filtered_df.empty:
    st.subheader("📊 Insights")

    col1, col2 = st.columns(2)

    with col1:
        platform_chart = alt.Chart(filtered_df).mark_bar().encode(
            x="platform", y="count()", color="platform"
        ).properties(title="Platform Share")
        st.altair_chart(platform_chart, use_container_width=True)

        bestseller_chart = alt.Chart(filtered_df).mark_arc().encode(
            theta="count()", color="bestseller"
        ).properties(title="Bestseller Breakdown")
        st.altair_chart(bestseller_chart, use_container_width=True)

    with col2:
        avg_price_chart = alt.Chart(filtered_df).mark_bar().encode(
            x="platform", y="average(price)", color="platform"
        ).properties(title="Average Price per Platform")
        st.altair_chart(avg_price_chart, use_container_width=True)

        scatter_chart = alt.Chart(filtered_df).mark_circle(size=60).encode(
            x="price", y="rating", color="platform",
            tooltip=["title", "price", "rating", "platform"]
        ).properties(title="Rating vs Price")
        st.altair_chart(scatter_chart, use_container_width=True)
