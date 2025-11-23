from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./shop.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    barcode = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, default="Walk-in Customer")
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)
    payment_method = Column(String, default="cash")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")

def create_tables():
    Base.metadata.create_all(bind=engine)

def init_sample_data():
    db = SessionLocal()
    
    if db.query(Product).count() == 0:
        sample_products = [
            Product(name="Laptop", price=999.99, stock=10, barcode="123456"),
            Product(name="Wireless Mouse", price=25.50, stock=50, barcode="123457"),
            Product(name="Mechanical Keyboard", price=75.00, stock=30, barcode="123458"),
            Product(name="27\" Monitor", price=299.99, stock=15, barcode="123459"),
            Product(name="USB-C Cable", price=15.99, stock=100, barcode="123460"),
        ]
        
        db.add_all(sample_products)
        db.commit()
    
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()