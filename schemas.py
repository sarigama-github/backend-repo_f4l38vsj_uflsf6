"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# E-commerce phone store schemas

class Phoneproduct(BaseModel):
    """
    Phone products schema
    Collection name: "phoneproduct"
    """
    brand: str = Field(..., description="Brand name")
    model: str = Field(..., description="Model name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in USD")
    stock: int = Field(0, ge=0, description="Units in stock")
    image: Optional[str] = Field(None, description="Primary image URL")
    colors: Optional[List[str]] = Field(default=None, description="Available colors")
    storage: Optional[List[str]] = Field(default=None, description="Storage options (e.g., 128GB)")
    screen: Optional[str] = Field(None, description="Screen size/resolution")
    battery: Optional[str] = Field(None, description="Battery capacity")
    camera: Optional[str] = Field(None, description="Camera specs")

class Order(BaseModel):
    """
    Orders schema
    Collection name: "order"
    """
    customer_name: str = Field(..., description="Customer full name")
    email: str = Field(..., description="Customer email")
    address: str = Field(..., description="Shipping address")
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country")
    items: list = Field(..., description="List of items with productId, qty, price")
    total: float = Field(..., ge=0, description="Order total")
    status: str = Field("pending", description="Order status")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
