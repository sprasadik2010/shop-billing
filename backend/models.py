from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Product models
class ProductBase(BaseModel):
    name: str
    price: float
    stock: int
    barcode: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Invoice item models
class InvoiceItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItem(InvoiceItemBase):
    id: int
    product: Product
    
    class Config:
        from_attributes = True

# Invoice models
class InvoiceBase(BaseModel):
    customer_name: str = "Walk-in Customer"
    payment_method: str = "cash"

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]

class Invoice(InvoiceBase):
    id: int
    total_amount: float
    tax_amount: float
    created_at: datetime
    items: List[InvoiceItem]
    
    class Config:
        from_attributes = True

# Cart models
class CartItem(BaseModel):
    product_id: int
    quantity: int
    name: str
    price: float

class CheckoutRequest(BaseModel):
    cart: List[CartItem]
    customer_name: str = "Walk-in Customer"
    payment_method: str = "cash"