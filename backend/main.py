# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List
import json

# import your database helpers + models
from database import get_db, create_tables, init_sample_data, Product, Invoice, InvoiceItem

app = FastAPI(title="Shop Billing System", version="1.0.0")

# CORS middleware - allow your frontend dev server and local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://shop-billing.onrender.com",  # your frontend
        "https://shop-billing-backend-n3ro.onrender.com"  # optional
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    create_tables()
    init_sample_data()

# -------------------------
# Helper converters
# -------------------------
def product_to_dict(product: Product) -> Dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "barcode": product.barcode,
        "created_at": product.created_at.isoformat() if product.created_at else None
    }

def invoice_to_dict(invoice: Invoice) -> Dict[str, Any]:
    return {
        "id": invoice.id,
        "customer_name": invoice.customer_name,
        "total_amount": invoice.total_amount,
        "tax_amount": invoice.tax_amount,
        "payment_method": invoice.payment_method,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "product": product_to_dict(item.product) if item.product else None
            }
            for item in invoice.items
        ]
    }

# -------------------------
# Utility: recalc invoice totals
# -------------------------
TAX_RATE = 0.08

def recalc_invoice_totals(db: Session, invoice: Invoice):
    """
    Recalculate and persist invoice.tax_amount and invoice.total_amount
    based on current InvoiceItems.
    """
    db.refresh(invoice)  # ensure fresh items
    subtotal = 0.0
    for item in invoice.items:
        subtotal += (item.unit_price or 0.0) * (item.quantity or 0)
    tax_amount = subtotal * TAX_RATE
    total_amount = subtotal + tax_amount

    invoice.tax_amount = tax_amount
    invoice.total_amount = total_amount

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

# -------------------------
# PRODUCT endpoints (existing + CRUD)
# -------------------------

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    """Get all products with stock > 0"""
    products = db.query(Product).filter(Product.stock > 0).all()
    return [product_to_dict(product) for product in products]

@app.get("/products/all")
def get_products_all(db: Session = Depends(get_db)):
    """Get all products regardless of stock"""
    products = db.query(Product).order_by(Product.id).all()
    return [product_to_dict(product) for product in products]

@app.get("/products/{barcode}")
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """Get product by barcode"""
    product = db.query(Product).filter(Product.barcode == barcode, Product.stock > 0).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_dict(product)

@app.get("/product/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_dict(product)

@app.post("/products")
def create_product(product_data: Dict[Any, Any], db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        db_product = Product(
            name=product_data.get("name"),
            price=float(product_data.get("price", 0) or 0),
            stock=int(product_data.get("stock", 0) or 0),
            barcode=product_data.get("barcode")
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return product_to_dict(db_product)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/products/{product_id}")
def update_product(product_id: int, product_data: Dict[Any, Any], db: Session = Depends(get_db)):
    """Update product fields"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = product_data.get("name", product.name)
    if "price" in product_data:
        product.price = float(product_data.get("price", product.price) or product.price)
    if "stock" in product_data:
        product.stock = int(product_data.get("stock", product.stock) or product.stock)
    product.barcode = product_data.get("barcode", product.barcode)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product_to_dict(product)

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete product if it's not used in any invoice items"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    used = db.query(InvoiceItem).filter(InvoiceItem.product_id == product_id).first()
    if used:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product as it is used in invoice items."
        )

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully", "id": product_id}

# -------------------------
# CHECKOUT endpoint (keeps original behavior)
# -------------------------
@app.post("/checkout")
def checkout(checkout_data: Dict[Any, Any], db: Session = Depends(get_db)):
    """Process a sale (creates invoice + items and reduces product stock)"""
    try:
        cart = checkout_data.get("cart", [])
        customer_name = checkout_data.get("customer_name", "Walk-in Customer")
        payment_method = checkout_data.get("payment_method", "cash")

        # Calculate totals
        subtotal = sum((item.get("price", 0) or 0) * (item.get("quantity", 0) or 0) for item in cart)
        tax_amount = subtotal * TAX_RATE
        total_amount = subtotal + tax_amount

        # Create invoice
        db_invoice = Invoice(
            customer_name=customer_name,
            total_amount=total_amount,
            tax_amount=tax_amount,
            payment_method=payment_method
        )
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)

        # Create invoice items and update stock
        for cart_item in cart:
            product_id = cart_item["product_id"]
            quantity = int(cart_item["quantity"])
            unit_price = float(cart_item["price"])

            product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
            if not product:
                db.rollback()
                raise HTTPException(status_code=404, detail=f"Product id {product_id} not found")
            if product.stock < quantity:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

            db_invoice_item = InvoiceItem(
                invoice_id=db_invoice.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price
            )
            db.add(db_invoice_item)

            # reduce stock
            product.stock -= quantity
            db.add(product)

        db.commit()
        db.refresh(db_invoice)
        return invoice_to_dict(db_invoice)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")

# -------------------------
# INVOICE endpoints (CRUD)
# -------------------------

@app.get("/invoices")
def get_invoices(db: Session = Depends(get_db)):
    """Get all invoices (latest first)"""
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    return [invoice_to_dict(invoice) for invoice in invoices]

@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get a specific invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice_to_dict(invoice)

@app.post("/invoices")
def create_invoice(invoice_data: Dict[Any, Any], db: Session = Depends(get_db)):
    """
    Create an invoice without items (you can add items later via invoice-items endpoints).
    If invoice_data contains 'items' list, those items will be added as well and stock adjusted.
    """
    try:
        customer_name = invoice_data.get("customer_name", "Walk-in Customer")
        payment_method = invoice_data.get("payment_method", "cash")
        items = invoice_data.get("items", [])

        db_invoice = Invoice(
            customer_name=customer_name,
            total_amount=0.0,
            tax_amount=0.0,
            payment_method=payment_method
        )
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)

        # optional items
        if items:
            for it in items:
                product_id = it["product_id"]
                qty = int(it["quantity"])
                unit_price = float(it["unit_price"])

                product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
                if not product:
                    db.rollback()
                    raise HTTPException(status_code=404, detail=f"Product id {product_id} not found")
                if product.stock < qty:
                    db.rollback()
                    raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

                inv_item = InvoiceItem(
                    invoice_id=db_invoice.id,
                    product_id=product_id,
                    quantity=qty,
                    unit_price=unit_price
                )
                db.add(inv_item)
                product.stock -= qty
                db.add(product)

            db.commit()
            db.refresh(db_invoice)

        # recalc totals
        recalc_invoice_totals(db, db_invoice)
        return invoice_to_dict(db_invoice)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/invoices/{invoice_id}")
def update_invoice(invoice_id: int, invoice_data: Dict[Any, Any], db: Session = Depends(get_db)):
    """
    Update invoice metadata (customer_name, payment_method).
    Totals are recalculated from items when requested or after item changes.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if "customer_name" in invoice_data:
        invoice.customer_name = invoice_data.get("customer_name", invoice.customer_name)
    if "payment_method" in invoice_data:
        invoice.payment_method = invoice_data.get("payment_method", invoice.payment_method)

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice_to_dict(invoice)

@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """
    Option B behavior: Prevent delete if invoice has items.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    item_count = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).count()
    if item_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete invoice because it has items.")

    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully", "id": invoice_id}

# -------------------------
# INVOICE ITEM endpoints (CRUD)
# -------------------------

@app.get("/invoices/{invoice_id}/items")
def get_invoice_items(invoice_id: int, db: Session = Depends(get_db)):
    """Return all items for an invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
    return [
        {
            "id": item.id,
            "invoice_id": item.invoice_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "product": product_to_dict(item.product) if item.product else None
        }
        for item in items
    ]

@app.post("/invoices/{invoice_id}/items")
def create_invoice_item(invoice_id: int, item_data: Dict[Any, Any], db: Session = Depends(get_db)):
    """
    Create invoice item and reduce product stock.
    Then recalculate invoice totals.
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        product_id = item_data["product_id"]
        quantity = int(item_data["quantity"])
        unit_price = float(item_data["unit_price"])

        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.stock < quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

        item = InvoiceItem(
            invoice_id=invoice_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        )
        db.add(item)

        product.stock -= quantity
        db.add(product)

        db.commit()
        db.refresh(item)

        # recalc totals
        recalc_invoice_totals(db, invoice)
        return {
            "message": "Item added",
            "item": {
                "id": item.id,
                "invoice_id": item.invoice_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/invoice-items/{item_id}")
def update_invoice_item(item_id: int, item_data: Dict[Any, Any], db: Session = Depends(get_db)):
    """
    Update an invoice item:
    - Adjust product stock by delta (new_qty - old_qty)
    - Update unit_price if provided
    - Recalculate invoice totals
    """
    try:
        item = db.query(InvoiceItem).filter(InvoiceItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        old_qty = item.quantity or 0
        new_qty = int(item_data.get("quantity", old_qty))
        new_price = float(item_data.get("unit_price", item.unit_price))

        delta = new_qty - old_qty
        if delta > 0:
            # need to reduce additional stock
            if product.stock < delta:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")
            product.stock -= delta
        elif delta < 0:
            # return stock back
            product.stock += (-delta)

        item.quantity = new_qty
        item.unit_price = new_price

        db.add(product)
        db.add(item)
        db.commit()
        db.refresh(item)

        # recalc totals
        invoice = db.query(Invoice).filter(Invoice.id == item.invoice_id).first()
        recalc_invoice_totals(db, invoice)

        return {"message": "Item updated", "item": item.id}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/invoice-items/{item_id}")
def delete_invoice_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete invoice item and return stock to product, then recalc invoice totals.
    """
    try:
        item = db.query(InvoiceItem).filter(InvoiceItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if product:
            product.stock += item.quantity
            db.add(product)

        invoice_id = item.invoice_id

        db.delete(item)
        db.commit()

        # recalc totals
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            recalc_invoice_totals(db, invoice)

        return {"message": "Item deleted", "id": item_id}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# Health / quick check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# -------------------------
# Run (for direct run)
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
