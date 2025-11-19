import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Phoneproduct, Order

app = FastAPI(title="Phone Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Phone Store Backend Running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Helper to convert ObjectId to string

def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id")) if doc.get("_id") else None
    return doc

# Seed some demo phones if collection empty
@app.post("/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["phoneproduct"].count_documents({})
    if count > 0:
        return {"inserted": 0, "message": "Already seeded"}
    demo = [
        {
            "brand": "Apple",
            "model": "iPhone 15 Pro",
            "description": "A17 Pro chip, ProMotion, titanium body",
            "price": 1199,
            "stock": 25,
            "image": "https://images.unsplash.com/photo-1695653422656-ef532eb0d99f?q=80&w=1200&auto=format&fit=crop",
            "colors": ["Black", "White", "Blue"],
            "storage": ["128GB", "256GB", "512GB"],
            "screen": "6.1" " OLED",
            "battery": "3274 mAh",
            "camera": "48MP main"
        },
        {
            "brand": "Samsung",
            "model": "Galaxy S23 Ultra",
            "description": "200MP camera, S Pen, powerhouse",
            "price": 1099,
            "stock": 30,
            "image": "https://images.unsplash.com/photo-1670272500051-3c8aaf645ed9?q=80&w=1200&auto=format&fit=crop",
            "colors": ["Green", "Black", "Cream"],
            "storage": ["256GB", "512GB"],
            "screen": "6.8" " AMOLED",
            "battery": "5000 mAh",
            "camera": "200MP"
        },
        {
            "brand": "Google",
            "model": "Pixel 8 Pro",
            "description": "Tensor G3, best-in-class AI",
            "price": 999,
            "stock": 15,
            "image": "https://images.unsplash.com/photo-1696855876023-4d620f33220e?q=80&w=1200&auto=format&fit=crop",
            "colors": ["Obsidian", "Porcelain"],
            "storage": ["128GB", "256GB"],
            "screen": "6.7" " OLED",
            "battery": "5050 mAh",
            "camera": "50MP"
        }
    ]
    ids = []
    for d in demo:
        ids.append(create_document("phoneproduct", d))
    return {"inserted": len(ids), "ids": ids}

# Products endpoints
@app.get("/api/phones")
def list_phones(q: Optional[str] = None):
    flt = {}
    if q:
        # simple regex OR across brand and model
        flt = {"$or": [{"brand": {"$regex": q, "$options": "i"}}, {"model": {"$regex": q, "$options": "i"}}]}
    docs = get_documents("phoneproduct", flt)
    return [serialize_doc(d) for d in docs]

@app.get("/api/phones/{phone_id}")
def get_phone(phone_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db["phoneproduct"].find_one({"_id": ObjectId(phone_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

# Cart / Order endpoints
class CartItem(BaseModel):
    product_id: str
    qty: int

class CreateOrderRequest(BaseModel):
    customer_name: str
    email: str
    address: str
    city: str
    country: str
    items: List[CartItem]

@app.post("/api/orders")
def create_order(payload: CreateOrderRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Fetch products and compute total
    item_docs = []
    total = 0.0
    for item in payload.items:
        try:
            doc = db["phoneproduct"].find_one({"_id": ObjectId(item.product_id)})
            if not doc:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            if doc.get("stock", 0) < item.qty:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {doc.get('model')}")
            price = float(doc.get("price", 0))
            total += price * item.qty
            item_docs.append({
                "product_id": item.product_id,
                "brand": doc.get("brand"),
                "model": doc.get("model"),
                "price": price,
                "qty": item.qty,
                "image": doc.get("image")
            })
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid product id")

    order = Order(
        customer_name=payload.customer_name,
        email=payload.email,
        address=payload.address,
        city=payload.city,
        country=payload.country,
        items=item_docs,
        total=round(total, 2),
        status="pending",
    )

    order_id = create_document("order", order)

    # Decrement stock
    for it in payload.items:
        db["phoneproduct"].update_one({"_id": ObjectId(it.product_id)}, {"$inc": {"stock": -it.qty}, "$set": {"updated_at": None}})

    return {"order_id": order_id, "total": order.total, "status": "success"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
