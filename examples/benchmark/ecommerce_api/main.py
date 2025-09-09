"""E-Commerce API - Comprehensive online shopping platform."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import random

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from socket_agent import SocketAgentMiddleware, socket

# Create FastAPI app
app = FastAPI(title="E-Commerce API")

# ============= Data Models =============

class Product(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    original_price: Optional[float] = None
    brand: str
    stock: int
    rating: float
    reviews_count: int
    image_url: str
    tags: List[str] = []
    
class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)

class Cart(BaseModel):
    id: str
    user_id: Optional[str] = None
    items: List[Dict[str, Any]]
    subtotal: float
    tax: float
    total: float
    created_at: str
    updated_at: str

class ShippingAddress(BaseModel):
    name: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"

class OrderCreate(BaseModel):
    cart_id: str
    user_id: str
    shipping_address: ShippingAddress
    shipping_method: str = Field(default="standard", pattern="^(standard|express|overnight)$")
    payment_method: str = Field(default="credit_card")

class Order(BaseModel):
    id: str
    user_id: str
    items: List[Dict[str, Any]]
    subtotal: float
    tax: float
    shipping: float
    total: float
    status: str
    shipping_address: Dict[str, str]
    shipping_method: str
    payment_method: str
    created_at: str
    estimated_delivery: str

class Review(BaseModel):
    product_id: str
    user_id: str
    rating: int = Field(ge=1, le=5)
    title: str
    comment: str

class User(BaseModel):
    id: str
    name: str
    email: str
    addresses: List[Dict[str, str]]
    order_history: List[str]
    wishlist: List[str]

# ============= In-Memory Database =============

# Sample product data
products_db = {
    # Electronics
    "prod-001": {
        "id": "prod-001",
        "name": "Wireless Noise-Canceling Headphones",
        "description": "Premium over-ear headphones with active noise cancellation and 30-hour battery life",
        "category": "electronics",
        "price": 299.99,
        "original_price": 349.99,
        "brand": "AudioTech",
        "stock": 45,
        "rating": 4.5,
        "reviews_count": 234,
        "image_url": "/images/headphones.jpg",
        "tags": ["wireless", "noise-canceling", "bluetooth", "premium"]
    },
    "prod-002": {
        "id": "prod-002",
        "name": "Smart Watch Pro",
        "description": "Fitness tracking, heart rate monitor, GPS, and smartphone notifications",
        "category": "electronics",
        "price": 249.99,
        "brand": "TechFit",
        "stock": 67,
        "rating": 4.3,
        "reviews_count": 189,
        "image_url": "/images/smartwatch.jpg",
        "tags": ["fitness", "smart", "wearable", "health"]
    },
    "prod-003": {
        "id": "prod-003",
        "name": "4K Webcam",
        "description": "Ultra HD webcam with auto-focus and built-in microphone",
        "category": "electronics",
        "price": 129.99,
        "brand": "ViewClear",
        "stock": 112,
        "rating": 4.2,
        "reviews_count": 456,
        "image_url": "/images/webcam.jpg",
        "tags": ["webcam", "4k", "streaming", "work-from-home"]
    },
    "prod-004": {
        "id": "prod-004",
        "name": "Portable SSD 1TB",
        "description": "High-speed external storage with USB-C connectivity",
        "category": "electronics",
        "price": 149.99,
        "original_price": 199.99,
        "brand": "DataStore",
        "stock": 89,
        "rating": 4.7,
        "reviews_count": 678,
        "image_url": "/images/ssd.jpg",
        "tags": ["storage", "portable", "fast", "usb-c"]
    },
    "prod-005": {
        "id": "prod-005",
        "name": "Wireless Gaming Mouse",
        "description": "RGB gaming mouse with 16000 DPI and programmable buttons",
        "category": "electronics",
        "price": 79.99,
        "brand": "GameGear",
        "stock": 156,
        "rating": 4.4,
        "reviews_count": 892,
        "image_url": "/images/gaming-mouse.jpg",
        "tags": ["gaming", "wireless", "rgb", "programmable"]
    },
    
    # Clothing
    "prod-006": {
        "id": "prod-006",
        "name": "Premium Cotton T-Shirt",
        "description": "100% organic cotton, comfortable fit, available in multiple colors",
        "category": "clothing",
        "price": 29.99,
        "brand": "EcoWear",
        "stock": 200,
        "rating": 4.6,
        "reviews_count": 1234,
        "image_url": "/images/tshirt.jpg",
        "tags": ["cotton", "organic", "casual", "comfortable"]
    },
    "prod-007": {
        "id": "prod-007",
        "name": "Denim Jeans - Slim Fit",
        "description": "Classic blue denim with modern slim fit design",
        "category": "clothing",
        "price": 69.99,
        "brand": "DenimCo",
        "stock": 145,
        "rating": 4.3,
        "reviews_count": 567,
        "image_url": "/images/jeans.jpg",
        "tags": ["denim", "slim-fit", "casual", "classic"]
    },
    "prod-008": {
        "id": "prod-008",
        "name": "Running Shoes",
        "description": "Lightweight athletic shoes with superior cushioning",
        "category": "clothing",
        "price": 119.99,
        "original_price": 149.99,
        "brand": "RunFast",
        "stock": 78,
        "rating": 4.5,
        "reviews_count": 345,
        "image_url": "/images/running-shoes.jpg",
        "tags": ["athletic", "running", "sports", "comfortable"]
    },
    "prod-009": {
        "id": "prod-009",
        "name": "Winter Jacket",
        "description": "Waterproof insulated jacket for cold weather",
        "category": "clothing",
        "price": 199.99,
        "brand": "WarmGear",
        "stock": 34,
        "rating": 4.7,
        "reviews_count": 234,
        "image_url": "/images/jacket.jpg",
        "tags": ["winter", "waterproof", "insulated", "warm"]
    },
    "prod-010": {
        "id": "prod-010",
        "name": "Yoga Pants",
        "description": "Stretchy, breathable fabric perfect for yoga and fitness",
        "category": "clothing",
        "price": 49.99,
        "brand": "FlexFit",
        "stock": 167,
        "rating": 4.4,
        "reviews_count": 789,
        "image_url": "/images/yoga-pants.jpg",
        "tags": ["yoga", "fitness", "stretchy", "comfortable"]
    },
    
    # Home & Garden
    "prod-011": {
        "id": "prod-011",
        "name": "Smart LED Bulb Set (4-pack)",
        "description": "WiFi-enabled color-changing LED bulbs with app control",
        "category": "home",
        "price": 49.99,
        "brand": "SmartHome",
        "stock": 234,
        "rating": 4.2,
        "reviews_count": 567,
        "image_url": "/images/smart-bulbs.jpg",
        "tags": ["smart-home", "led", "energy-efficient", "wifi"]
    },
    "prod-012": {
        "id": "prod-012",
        "name": "Robot Vacuum Cleaner",
        "description": "Automatic vacuum with mapping technology and app control",
        "category": "home",
        "price": 399.99,
        "original_price": 499.99,
        "brand": "CleanBot",
        "stock": 23,
        "rating": 4.6,
        "reviews_count": 892,
        "image_url": "/images/robot-vacuum.jpg",
        "tags": ["smart-home", "cleaning", "automatic", "robot"]
    },
    "prod-013": {
        "id": "prod-013",
        "name": "Memory Foam Pillow",
        "description": "Ergonomic design for better sleep and neck support",
        "category": "home",
        "price": 59.99,
        "brand": "SleepWell",
        "stock": 189,
        "rating": 4.5,
        "reviews_count": 1456,
        "image_url": "/images/pillow.jpg",
        "tags": ["bedroom", "comfort", "memory-foam", "ergonomic"]
    },
    "prod-014": {
        "id": "prod-014",
        "name": "Stainless Steel Cookware Set",
        "description": "10-piece professional grade cookware set",
        "category": "home",
        "price": 299.99,
        "brand": "ChefPro",
        "stock": 45,
        "rating": 4.7,
        "reviews_count": 234,
        "image_url": "/images/cookware.jpg",
        "tags": ["kitchen", "cooking", "stainless-steel", "professional"]
    },
    "prod-015": {
        "id": "prod-015",
        "name": "Indoor Plant Collection",
        "description": "Set of 3 low-maintenance indoor plants with decorative pots",
        "category": "home",
        "price": 79.99,
        "brand": "GreenLife",
        "stock": 67,
        "rating": 4.3,
        "reviews_count": 345,
        "image_url": "/images/plants.jpg",
        "tags": ["plants", "indoor", "decorative", "low-maintenance"]
    },
    
    # Books
    "prod-016": {
        "id": "prod-016",
        "name": "The Art of Programming",
        "description": "Comprehensive guide to modern software development practices",
        "category": "books",
        "price": 49.99,
        "brand": "TechBooks",
        "stock": 234,
        "rating": 4.8,
        "reviews_count": 567,
        "image_url": "/images/programming-book.jpg",
        "tags": ["programming", "technology", "education", "software"]
    },
    "prod-017": {
        "id": "prod-017",
        "name": "Mindful Living",
        "description": "A guide to meditation and stress-free living",
        "category": "books",
        "price": 24.99,
        "brand": "WellnessPress",
        "stock": 156,
        "rating": 4.5,
        "reviews_count": 892,
        "image_url": "/images/mindful-book.jpg",
        "tags": ["self-help", "meditation", "wellness", "lifestyle"]
    },
    "prod-018": {
        "id": "prod-018",
        "name": "World History Encyclopedia",
        "description": "Comprehensive coverage of world history from ancient to modern times",
        "category": "books",
        "price": 89.99,
        "brand": "Academic Press",
        "stock": 78,
        "rating": 4.6,
        "reviews_count": 234,
        "image_url": "/images/history-book.jpg",
        "tags": ["history", "education", "reference", "encyclopedia"]
    },
    "prod-019": {
        "id": "prod-019",
        "name": "Cookbook: Global Cuisines",
        "description": "500+ recipes from around the world",
        "category": "books",
        "price": 34.99,
        "brand": "CulinaryBooks",
        "stock": 123,
        "rating": 4.4,
        "reviews_count": 456,
        "image_url": "/images/cookbook.jpg",
        "tags": ["cooking", "recipes", "cuisine", "food"]
    },
    "prod-020": {
        "id": "prod-020",
        "name": "Science Fiction Collection",
        "description": "Box set of 5 award-winning sci-fi novels",
        "category": "books",
        "price": 59.99,
        "original_price": 79.99,
        "brand": "SciFi Publishing",
        "stock": 89,
        "rating": 4.7,
        "reviews_count": 678,
        "image_url": "/images/scifi-books.jpg",
        "tags": ["fiction", "sci-fi", "novels", "collection"]
    },
    
    # Sports & Outdoors
    "prod-021": {
        "id": "prod-021",
        "name": "Yoga Mat - Extra Thick",
        "description": "Non-slip exercise mat with carrying strap",
        "category": "sports",
        "price": 39.99,
        "brand": "FitGear",
        "stock": 234,
        "rating": 4.5,
        "reviews_count": 1234,
        "image_url": "/images/yoga-mat.jpg",
        "tags": ["yoga", "exercise", "fitness", "non-slip"]
    },
    "prod-022": {
        "id": "prod-022",
        "name": "Camping Tent - 4 Person",
        "description": "Waterproof family tent with easy setup",
        "category": "sports",
        "price": 199.99,
        "brand": "OutdoorPro",
        "stock": 45,
        "rating": 4.4,
        "reviews_count": 345,
        "image_url": "/images/tent.jpg",
        "tags": ["camping", "outdoor", "waterproof", "family"]
    },
    "prod-023": {
        "id": "prod-023",
        "name": "Adjustable Dumbbells Set",
        "description": "5-50 lbs adjustable weight dumbbells with stand",
        "category": "sports",
        "price": 299.99,
        "brand": "PowerLift",
        "stock": 34,
        "rating": 4.7,
        "reviews_count": 567,
        "image_url": "/images/dumbbells.jpg",
        "tags": ["weights", "fitness", "strength", "adjustable"]
    },
    "prod-024": {
        "id": "prod-024",
        "name": "Mountain Bike",
        "description": "21-speed mountain bike with shock absorption",
        "category": "sports",
        "price": 599.99,
        "original_price": 799.99,
        "brand": "TrailBlazer",
        "stock": 12,
        "rating": 4.6,
        "reviews_count": 234,
        "image_url": "/images/mountain-bike.jpg",
        "tags": ["bike", "mountain", "outdoor", "exercise"]
    },
    "prod-025": {
        "id": "prod-025",
        "name": "Swimming Goggles",
        "description": "Anti-fog, UV protection swimming goggles",
        "category": "sports",
        "price": 24.99,
        "brand": "AquaGear",
        "stock": 189,
        "rating": 4.3,
        "reviews_count": 789,
        "image_url": "/images/goggles.jpg",
        "tags": ["swimming", "water-sports", "uv-protection", "anti-fog"]
    }
}

# Other databases
carts_db: Dict[str, Dict] = {}
orders_db: Dict[str, Dict] = {}
users_db: Dict[str, Dict] = {
    "user-001": {
        "id": "user-001",
        "name": "John Doe",
        "email": "john@example.com",
        "addresses": [
            {
                "name": "John Doe",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94102",
                "country": "USA"
            }
        ],
        "order_history": [],
        "wishlist": ["prod-001", "prod-012"]
    },
    "user-002": {
        "id": "user-002",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "addresses": [
            {
                "name": "Jane Smith",
                "street": "456 Oak Ave",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "country": "USA"
            }
        ],
        "order_history": [],
        "wishlist": ["prod-006", "prod-010"]
    }
}

reviews_db: Dict[str, List[Dict]] = {}

# ============= Helper Functions =============

def calculate_tax(subtotal: float, state: str = "CA") -> float:
    """Calculate tax based on state."""
    tax_rates = {
        "CA": 0.0875,
        "NY": 0.08,
        "TX": 0.0625,
        "FL": 0.06,
        "WA": 0.065
    }
    rate = tax_rates.get(state, 0.07)  # Default 7%
    return round(subtotal * rate, 2)

def calculate_shipping(method: str, subtotal: float) -> float:
    """Calculate shipping cost."""
    if subtotal >= 100:  # Free shipping over $100
        return 0.0
    
    shipping_costs = {
        "standard": 9.99,
        "express": 19.99,
        "overnight": 39.99
    }
    return shipping_costs.get(method, 9.99)

def estimate_delivery(method: str) -> str:
    """Estimate delivery date based on shipping method."""
    from datetime import timedelta
    
    days = {
        "standard": 5,
        "express": 2,
        "overnight": 1
    }
    
    delivery_date = datetime.now() + timedelta(days=days.get(method, 5))
    return delivery_date.strftime("%Y-%m-%d")

# ============= API Routes =============

# Product endpoints
@app.get("/products", response_model=List[Product])
@socket.describe(
    "Browse products with optional filters",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "category": {"type": "string"},
                "price": {"type": "number"},
                "brand": {"type": "string"},
                "stock": {"type": "integer"},
                "rating": {"type": "number"}
            }
        }
    }
)
async def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    in_stock: bool = True,
    sort_by: str = "name"
):
    """List products with optional filters."""
    products = list(products_db.values())
    
    # Apply filters
    if category:
        products = [p for p in products if p["category"] == category]
    if min_price:
        products = [p for p in products if p["price"] >= min_price]
    if max_price:
        products = [p for p in products if p["price"] <= max_price]
    if brand:
        products = [p for p in products if p["brand"].lower() == brand.lower()]
    if in_stock:
        products = [p for p in products if p["stock"] > 0]
    
    # Sort
    if sort_by == "price":
        products.sort(key=lambda x: x["price"])
    elif sort_by == "rating":
        products.sort(key=lambda x: x["rating"], reverse=True)
    else:
        products.sort(key=lambda x: x["name"])
    
    return products

@app.get("/products/search")
@socket.describe(
    "Search products by name or description",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "category": {"type": "string"},
                "price": {"type": "number"},
                "rating": {"type": "number"}
            }
        }
    }
)
async def search_products(q: str):
    """Search products by name, description, or tags."""
    results = []
    query = q.lower()
    
    for product in products_db.values():
        if (query in product["name"].lower() or 
            query in product["description"].lower() or
            any(query in tag for tag in product.get("tags", []))):
            results.append(product)
    
    return results

@app.get("/products/{product_id}", response_model=Product)
@socket.describe(
    "Get detailed information about a specific product",
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "category": {"type": "string"},
            "price": {"type": "number"},
            "original_price": {"type": "number"},
            "brand": {"type": "string"},
            "stock": {"type": "integer"},
            "rating": {"type": "number"},
            "reviews_count": {"type": "integer"}
        }
    }
)
async def get_product(product_id: str):
    """Get product details."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**products_db[product_id])

@app.get("/products/category/{category}")
@socket.describe(
    "Get all products in a specific category",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "price": {"type": "number"},
                "brand": {"type": "string"}
            }
        }
    }
)
async def get_products_by_category(category: str):
    """Get products by category."""
    products = [p for p in products_db.values() if p["category"] == category]
    if not products:
        raise HTTPException(status_code=404, detail=f"No products found in category: {category}")
    return products

# Cart endpoints
@app.post("/cart", response_model=Cart)
@socket.describe(
    "Create a new shopping cart",
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "items": {"type": "array"},
            "subtotal": {"type": "number"},
            "tax": {"type": "number"},
            "total": {"type": "number"}
        }
    }
)
async def create_cart(user_id: Optional[str] = None):
    """Create a new shopping cart."""
    cart_id = str(uuid4())
    cart = {
        "id": cart_id,
        "user_id": user_id,
        "items": [],
        "subtotal": 0.0,
        "tax": 0.0,
        "total": 0.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    carts_db[cart_id] = cart
    return Cart(**cart)

@app.get("/cart/{cart_id}", response_model=Cart)
@socket.describe(
    "Get cart contents",
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "items": {"type": "array"},
            "subtotal": {"type": "number"},
            "tax": {"type": "number"},
            "total": {"type": "number"}
        }
    }
)
async def get_cart(cart_id: str):
    """Get cart contents."""
    if cart_id not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    return Cart(**carts_db[cart_id])

@app.post("/cart/{cart_id}/items")
@socket.describe(
    "Add item to cart",
    request_schema={
        "type": "object",
        "properties": {
            "product_id": {"type": "string"},
            "quantity": {"type": "integer", "minimum": 1}
        },
        "required": ["product_id", "quantity"]
    },
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "items": {"type": "array"},
            "subtotal": {"type": "number"},
            "total": {"type": "number"}
        }
    },
    examples=['curl -X POST /cart/{cart_id}/items -d \'{"product_id":"prod-001","quantity":1}\'']
)
async def add_to_cart(cart_id: str, item: CartItem):
    """Add an item to the cart."""
    if cart_id not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    if item.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[item.product_id]
    
    # Check stock
    if product["stock"] < item.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Only {product['stock']} available"
        )
    
    cart = carts_db[cart_id]
    
    # Check if item already in cart
    for cart_item in cart["items"]:
        if cart_item["product_id"] == item.product_id:
            # Update quantity
            new_quantity = cart_item["quantity"] + item.quantity
            if product["stock"] < new_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for total quantity"
                )
            cart_item["quantity"] = new_quantity
            cart_item["subtotal"] = cart_item["price"] * new_quantity
            break
    else:
        # Add new item
        cart_item = {
            "product_id": item.product_id,
            "product_name": product["name"],
            "price": product["price"],
            "quantity": item.quantity,
            "subtotal": product["price"] * item.quantity
        }
        cart["items"].append(cart_item)
    
    # Update totals
    cart["subtotal"] = sum(item["subtotal"] for item in cart["items"])
    cart["tax"] = calculate_tax(cart["subtotal"])
    cart["total"] = cart["subtotal"] + cart["tax"]
    cart["updated_at"] = datetime.now().isoformat()
    
    return Cart(**cart)

@app.put("/cart/{cart_id}/items/{product_id}")
@socket.describe(
    "Update item quantity in cart",
    request_schema={
        "type": "object",
        "properties": {
            "quantity": {"type": "integer", "minimum": 0}
        },
        "required": ["quantity"]
    },
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "items": {"type": "array"},
            "total": {"type": "number"}
        }
    }
)
async def update_cart_item(cart_id: str, product_id: str, update: Dict[str, int]):
    """Update item quantity in cart (set to 0 to remove)."""
    if cart_id not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart = carts_db[cart_id]
    quantity = update.get("quantity", 0)
    
    if quantity == 0:
        # Remove item
        cart["items"] = [item for item in cart["items"] if item["product_id"] != product_id]
    else:
        # Update quantity
        product = products_db.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product["stock"] < quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        for item in cart["items"]:
            if item["product_id"] == product_id:
                item["quantity"] = quantity
                item["subtotal"] = item["price"] * quantity
                break
        else:
            raise HTTPException(status_code=404, detail="Item not in cart")
    
    # Update totals
    cart["subtotal"] = sum(item["subtotal"] for item in cart["items"])
    cart["tax"] = calculate_tax(cart["subtotal"])
    cart["total"] = cart["subtotal"] + cart["tax"]
    cart["updated_at"] = datetime.now().isoformat()
    
    return Cart(**cart)

@app.delete("/cart/{cart_id}/items/{product_id}")
@socket.describe(
    "Remove item from cart",
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "items": {"type": "array"},
            "total": {"type": "number"}
        }
    }
)
async def remove_from_cart(cart_id: str, product_id: str):
    """Remove an item from the cart."""
    if cart_id not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart = carts_db[cart_id]
    cart["items"] = [item for item in cart["items"] if item["product_id"] != product_id]
    
    # Update totals
    cart["subtotal"] = sum(item["subtotal"] for item in cart["items"])
    cart["tax"] = calculate_tax(cart["subtotal"])
    cart["total"] = cart["subtotal"] + cart["tax"]
    cart["updated_at"] = datetime.now().isoformat()
    
    return Cart(**cart)

# Order endpoints
@app.post("/checkout", response_model=Order)
@socket.describe(
    "Create an order from a shopping cart",
    request_schema={
        "type": "object",
        "properties": {
            "cart_id": {"type": "string"},
            "user_id": {"type": "string"},
            "shipping_address": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "street": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "zip_code": {"type": "string"}
                }
            },
            "shipping_method": {"type": "string"},
            "payment_method": {"type": "string"}
        },
        "required": ["cart_id", "user_id", "shipping_address"]
    },
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "user_id": {"type": "string"},
            "total": {"type": "number"},
            "status": {"type": "string"},
            "estimated_delivery": {"type": "string"}
        }
    },
    examples=['curl -X POST /checkout -d \'{"cart_id":"...", "user_id":"user-001", "shipping_address":{...}}\'']
)
async def checkout(order_data: OrderCreate):
    """Create an order from a cart."""
    # Validate cart
    if order_data.cart_id not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart = carts_db[order_data.cart_id]
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Validate user
    if order_data.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate shipping
    shipping_cost = calculate_shipping(order_data.shipping_method, cart["subtotal"])
    
    # Create order
    order_id = str(uuid4())
    order = {
        "id": order_id,
        "user_id": order_data.user_id,
        "items": cart["items"].copy(),
        "subtotal": cart["subtotal"],
        "tax": cart["tax"],
        "shipping": shipping_cost,
        "total": cart["subtotal"] + cart["tax"] + shipping_cost,
        "status": "pending_payment",
        "shipping_address": order_data.shipping_address.dict(),
        "shipping_method": order_data.shipping_method,
        "payment_method": order_data.payment_method,
        "created_at": datetime.now().isoformat(),
        "estimated_delivery": estimate_delivery(order_data.shipping_method)
    }
    
    # Update inventory
    for item in cart["items"]:
        product = products_db[item["product_id"]]
        product["stock"] -= item["quantity"]
    
    # Save order
    orders_db[order_id] = order
    
    # Add to user's order history
    users_db[order_data.user_id]["order_history"].append(order_id)
    
    # Clear cart
    cart["items"] = []
    cart["subtotal"] = 0.0
    cart["tax"] = 0.0
    cart["total"] = 0.0
    cart["updated_at"] = datetime.now().isoformat()
    
    return Order(**order)

@app.get("/orders/{order_id}", response_model=Order)
@socket.describe(
    "Get order details",
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "user_id": {"type": "string"},
            "items": {"type": "array"},
            "total": {"type": "number"},
            "status": {"type": "string"},
            "estimated_delivery": {"type": "string"}
        }
    }
)
async def get_order(order_id: str):
    """Get order details."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**orders_db[order_id])

@app.get("/orders/user/{user_id}")
@socket.describe(
    "Get all orders for a user",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "total": {"type": "number"},
                "status": {"type": "string"},
                "created_at": {"type": "string"}
            }
        }
    }
)
async def get_user_orders(user_id: str):
    """Get all orders for a user."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_orders = []
    for order_id in users_db[user_id]["order_history"]:
        if order_id in orders_db:
            order = orders_db[order_id]
            user_orders.append({
                "id": order["id"],
                "total": order["total"],
                "status": order["status"],
                "created_at": order["created_at"]
            })
    
    return user_orders

@app.put("/orders/{order_id}/status")
@socket.describe(
    "Update order status (for payment confirmation, shipping, etc.)",
    request_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string"}
        },
        "required": ["status"]
    },
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "status": {"type": "string"}
        }
    }
)
async def update_order_status(order_id: str, status_update: Dict[str, str]):
    """Update order status."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ["pending_payment", "paid", "processing", "shipped", "delivered", "cancelled"]
    new_status = status_update.get("status")
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    orders_db[order_id]["status"] = new_status
    
    # If cancelled, restore inventory
    if new_status == "cancelled":
        order = orders_db[order_id]
        for item in order["items"]:
            if item["product_id"] in products_db:
                products_db[item["product_id"]]["stock"] += item["quantity"]
    
    return {"id": order_id, "status": new_status}

# User endpoints
@app.get("/users/{user_id}", response_model=User)
@socket.describe(
    "Get user profile",
    response_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string"},
            "addresses": {"type": "array"},
            "wishlist": {"type": "array"}
        }
    }
)
async def get_user(user_id: str):
    """Get user profile."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**users_db[user_id])

@app.post("/users/{user_id}/wishlist/{product_id}")
@socket.describe(
    "Add product to user's wishlist",
    response_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "wishlist": {"type": "array"}
        }
    }
)
async def add_to_wishlist(user_id: str, product_id: str):
    """Add product to wishlist."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    wishlist = users_db[user_id]["wishlist"]
    if product_id not in wishlist:
        wishlist.append(product_id)
    
    return {"message": "Added to wishlist", "wishlist": wishlist}

@app.delete("/users/{user_id}/wishlist/{product_id}")
@socket.describe(
    "Remove product from user's wishlist",
    response_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "wishlist": {"type": "array"}
        }
    }
)
async def remove_from_wishlist(user_id: str, product_id: str):
    """Remove product from wishlist."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    wishlist = users_db[user_id]["wishlist"]
    if product_id in wishlist:
        wishlist.remove(product_id)
    
    return {"message": "Removed from wishlist", "wishlist": wishlist}

@app.get("/users/{user_id}/wishlist")
@socket.describe(
    "Get user's wishlist with product details",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "price": {"type": "number"},
                "stock": {"type": "integer"}
            }
        }
    }
)
async def get_wishlist(user_id: str):
    """Get user's wishlist with product details."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    wishlist_products = []
    for product_id in users_db[user_id]["wishlist"]:
        if product_id in products_db:
            product = products_db[product_id]
            wishlist_products.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "stock": product["stock"]
            })
    
    return wishlist_products

# Review endpoints
@app.post("/reviews")
@socket.describe(
    "Add a product review",
    request_schema={
        "type": "object",
        "properties": {
            "product_id": {"type": "string"},
            "user_id": {"type": "string"},
            "rating": {"type": "integer", "minimum": 1, "maximum": 5},
            "title": {"type": "string"},
            "comment": {"type": "string"}
        },
        "required": ["product_id", "user_id", "rating", "title", "comment"]
    },
    response_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "review_id": {"type": "string"}
        }
    }
)
async def add_review(review: Review):
    """Add a product review."""
    if review.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    if review.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    review_id = str(uuid4())
    review_data = {
        "id": review_id,
        "user_id": review.user_id,
        "user_name": users_db[review.user_id]["name"],
        "rating": review.rating,
        "title": review.title,
        "comment": review.comment,
        "created_at": datetime.now().isoformat()
    }
    
    if review.product_id not in reviews_db:
        reviews_db[review.product_id] = []
    
    reviews_db[review.product_id].append(review_data)
    
    # Update product rating
    product = products_db[review.product_id]
    all_reviews = reviews_db[review.product_id]
    avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews)
    product["rating"] = round(avg_rating, 1)
    product["reviews_count"] = len(all_reviews)
    
    return {"message": "Review added successfully", "review_id": review_id}

@app.get("/reviews/{product_id}")
@socket.describe(
    "Get all reviews for a product",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "user_name": {"type": "string"},
                "rating": {"type": "integer"},
                "title": {"type": "string"},
                "comment": {"type": "string"},
                "created_at": {"type": "string"}
            }
        }
    }
)
async def get_product_reviews(product_id: str):
    """Get all reviews for a product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return reviews_db.get(product_id, [])

# Categories endpoint
@app.get("/categories")
@socket.describe(
    "Get all available product categories",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "product_count": {"type": "integer"}
            }
        }
    }
)
async def get_categories():
    """Get all product categories with counts."""
    categories = {}
    for product in products_db.values():
        cat = product["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    return [{"name": cat, "product_count": count} for cat, count in categories.items()]

# Deals endpoint
@app.get("/deals")
@socket.describe(
    "Get current deals and discounted products",
    response_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "price": {"type": "number"},
                "original_price": {"type": "number"},
                "discount_percent": {"type": "number"}
            }
        }
    }
)
async def get_deals():
    """Get products on sale."""
    deals = []
    for product in products_db.values():
        if product.get("original_price"):
            discount = ((product["original_price"] - product["price"]) / product["original_price"]) * 100
            deals.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "original_price": product["original_price"],
                "discount_percent": round(discount, 0)
            })
    
    # Sort by discount percentage
    deals.sort(key=lambda x: x["discount_percent"], reverse=True)
    return deals

# Initialize socket-agent middleware
SocketAgentMiddleware(
    app,
    name="E-Commerce API",
    description="Full-featured online shopping platform with products, cart, checkout, and user management",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
