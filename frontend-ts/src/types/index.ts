// Product types
export interface Product {
  id: number;
  name: string;
  price: number;
  stock: number;
  barcode: string | null;
  created_at: string;
}

export interface ProductCreate {
  name: string;
  price: number;
  stock: number;
  barcode?: string;
}

export interface ProductFormData {
  name: string;
  price: number;
  stock: number;
  barcode: string;
}

// Invoice types
export interface InvoiceItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  product: Product;
}

export interface Invoice {
  id: number;
  customer_name: string;
  total_amount: number;
  tax_amount: number;
  payment_method: string;
  created_at: string;
  items: InvoiceItem[];
}

export interface InvoiceCreate {
  customer_name: string;
  payment_method: string;
  items: InvoiceItemCreate[];
}

export interface InvoiceItemCreate {
  product_id: number;
  quantity: number;
  unit_price: number;
}

// Cart types
export interface CartItem {
  product_id: number;
  name: string;
  price: number;
  quantity: number;
}

export interface CheckoutRequest {
  cart: CartItem[];
  customer_name: string;
  payment_method: string;
}

// Dashboard types
export interface DashboardStats {
  total_products: number;
  low_stock_products: number;
  total_invoices: number;
  today_revenue: number;
  total_revenue: number;
}