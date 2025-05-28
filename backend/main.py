from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

click_log = []

urls = [
    {"url": "https://www.iherb.com/c/Reishi", "retailer": "iHerb", "logo": "https://s3.iherb.com/assets/img/iherb-logo.png"},
    {"url": "https://www.vitacost.com/productResults.aspx?Ntt=reishi", "retailer": "Vitacost", "logo": "https://www.vitacost.com/Content/images/vitacost_logo.png"}
]

mushroom_types = ["reishi", "cordyceps", "lion's mane", "chaga", "shiitake", "maitake", "blend"]

def fetch_products():
    headers = {"User-Agent": "Mozilla/5.0"}
    products = []

    for entry in urls:
        try:
            response = requests.get(entry["url"], headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")

            for p in soup.select("div.product"):
                name = p.select_one(".product-title").get_text(strip=True) if p.select_one(".product-title") else ""
                price = p.select_one(".price").get_text(strip=True) if p.select_one(".price") else ""
                link = p.select_one("a")["href"] if p.select_one("a") else ""
                brand = p.select_one(".brand").get_text(strip=True) if p.select_one(".brand") else ""
                rating = p.select_one(".rating-stars").get("title", "") if p.select_one(".rating-stars") else "No rating"
                review_count = p.select_one(".review-count").get_text(strip=True) if p.select_one(".review-count") else "0 reviews"
                organic = "organic" in name.lower()
                mtype = next((t for t in mushroom_types if t in name.lower()), "Other")

                products.append({
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "affiliate_link": link,
                    "rating": rating,
                    "reviews_count": review_count,
                    "organic": organic,
                    "type": mtype.capitalize(),
                    "retailer": entry["retailer"],
                    "retailer_logo": entry["logo"]
                })

        except Exception as e:
            print(f"Error with {entry['url']}: {e}")

    return products

@app.get("/products")
def get_products():
    return fetch_products()

@app.post("/clickout")
def log_click(request: Request):
    click_log.append({
        "timestamp": time.time(),
        "ip": request.client.host,
        "headers": dict(request.headers),
        "link": request.query_params.get("link"),
        "product": request.query_params.get("product")
    })
    return {"status": "logged"}

@app.get("/click-logs")
def get_logs():
    return click_log
