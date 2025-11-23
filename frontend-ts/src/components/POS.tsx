import React, { useState, useEffect, useRef } from 'react';
import { Search, Plus, Minus, X, ShoppingCart, Receipt } from 'lucide-react';
import axios from 'axios';
import { Product, Invoice, CartItem } from '../types';

const API_BASE = 'http://localhost:8000';

const POS: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [customerName, setCustomerName] = useState<string>('Walk-in Customer');
  const [paymentMethod, setPaymentMethod] = useState<string>('cash');
  const [barcodeInput, setBarcodeInput] = useState<string>('');
  const [showReceipt, setShowReceipt] = useState<boolean>(false);
  const [currentInvoice, setCurrentInvoice] = useState<Invoice | null>(null);
  const barcodeRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadProducts();
    barcodeRef.current?.focus();
  }, []);

  const loadProducts = async (): Promise<void> => {
    try {
      const response = await axios.get<Product[]>(`${API_BASE}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error loading products:', error);
    }
  };

const searchByBarcode = async (): Promise<void> => {
  if (!barcodeInput.trim()) return;
  
  try {
    const response = await axios.get<Product>(`${API_BASE}/products/${barcodeInput}`);
    addToCart(response.data);
    setBarcodeInput('');
    barcodeRef.current?.focus();
  } catch (error: unknown) {
    let errorMessage = 'Product not found!';
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        errorMessage = 'Product not found!';
      } else {
        errorMessage = error.response?.data?.detail || error.message || 'Search failed';
      }
    } else if (error instanceof Error) {
      errorMessage = error.message;
    }
    
    alert(errorMessage);
    console.error('Barcode search error:', error);
  }
};

  const addToCart = (product: Product): void => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product_id === product.id);
      
      if (existingItem) {
        return prevCart.map(item =>
          item.product_id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      } else {
        return [
          ...prevCart,
          {
            product_id: product.id,
            name: product.name,
            price: product.price,
            quantity: 1
          }
        ];
      }
    });
  };

  const updateQuantity = (productId: number, change: number): void => {
    setCart(prevCart => {
      const item = prevCart.find(item => item.product_id === productId);
      if (!item) return prevCart;

      const newQuantity = item.quantity + change;
      
      if (newQuantity <= 0) {
        return prevCart.filter(item => item.product_id !== productId);
      }
      
      return prevCart.map(item =>
        item.product_id === productId
          ? { ...item, quantity: newQuantity }
          : item
      );
    });
  };

  const removeFromCart = (productId: number): void => {
    setCart(prevCart => prevCart.filter(item => item.product_id !== productId));
  };

  const clearCart = (): void => {
    if (cart.length > 0 && window.confirm('Clear the cart?')) {
      setCart([]);
    }
  };

  const calculateTotals = (): { subtotal: number; tax: number; total: number } => {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const taxRate = 0.08;
    const tax = subtotal * taxRate;
    const total = subtotal + tax;
    
    return { subtotal, tax, total };
  };

const processCheckout = async (): Promise<void> => {
  if (cart.length === 0) {
    alert('Cart is empty!');
    return;
  }

  try {
    const checkoutData = {
      cart: cart,
      customer_name: customerName,
      payment_method: paymentMethod
    };

    const response = await axios.post<Invoice>(`${API_BASE}/checkout`, checkoutData);
    setCurrentInvoice(response.data);
    setShowReceipt(true);
    setCart([]);
    loadProducts(); // Refresh product stock
  } catch (error: unknown) {
    console.error('Checkout error:', error);
    
    let errorMessage = 'Checkout failed';
    
    if (axios.isAxiosError(error)) {
      // This is an Axios error
      errorMessage = error.response?.data?.detail || error.message || 'Checkout failed';
    } else if (error instanceof Error) {
      // This is a standard Error
      errorMessage = error.message;
    }
    
    alert(errorMessage);
  }
};

  const handleBarcodeKeyPress = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter') {
      searchByBarcode();
    }
  };

  const { subtotal, tax, total } = calculateTotals();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* <div className="flex items-center">
              <ShoppingCart className="h-8 w-8 text-green-600" />
              <h1 className="ml-2 text-2xl font-bold text-gray-900">ShopPOS</h1>
            </div> */}
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                {cart.length} items in cart
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Products Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Products</h2>
                
                {/* Barcode Search */}
                <div className="flex gap-2 mb-6">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <input
                      ref={barcodeRef}
                      type="text"
                      value={barcodeInput}
                      onChange={(e) => setBarcodeInput(e.target.value)}
                      onKeyPress={handleBarcodeKeyPress}
                      placeholder="Scan barcode or search..."
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                  <button
                    onClick={searchByBarcode}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500"
                  >
                    Search
                  </button>
                </div>

                {/* Products Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {products.map((product) => (
                    <div
                      key={product.id}
                      onClick={() => addToCart(product)}
                      className="bg-gray-50 rounded-lg p-4 border border-gray-200 cursor-pointer hover:bg-gray-100 hover:border-green-300 transition-colors"
                    >
                      <h3 className="font-medium text-gray-900 text-sm mb-1">
                        {product.name}
                      </h3>
                      <p className="text-green-600 font-semibold text-lg">
                        ${product.price.toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Stock: {product.stock}
                      </p>
                      {product.barcode && (
                        <p className="text-xs text-gray-400 mt-1">
                          #{product.barcode}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Cart Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border h-full flex flex-col">
              <div className="p-6 flex-1 flex flex-col">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Sale</h2>
                
                {/* Customer Info */}
                <div className="space-y-3 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Customer Name
                    </label>
                    <input
                      type="text"
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Payment Method
                    </label>
                    <select
                      value={paymentMethod}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    >
                      <option value="cash">Cash</option>
                      <option value="card">Card</option>
                      <option value="digital">Digital Wallet</option>
                    </select>
                  </div>
                </div>

                {/* Cart Items */}
                <div className="flex-1 overflow-y-auto mb-4">
                  {cart.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      <ShoppingCart className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>Cart is empty</p>
                      <p className="text-sm">Add products to get started</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {cart.map((item) => (
                        <div
                          key={item.product_id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div className="flex-1">
                            <h4 className="font-medium text-sm text-gray-900">
                              {item.name}
                            </h4>
                            <p className="text-xs text-gray-500">
                              ${item.price.toFixed(2)} × {item.quantity}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => updateQuantity(item.product_id, -1)}
                              className="p-1 text-gray-500 hover:text-gray-700"
                            >
                              <Minus className="h-4 w-4" />
                            </button>
                            <span className="font-medium text-sm w-8 text-center">
                              {item.quantity}
                            </span>
                            <button
                              onClick={() => updateQuantity(item.product_id, 1)}
                              className="p-1 text-gray-500 hover:text-gray-700"
                            >
                              <Plus className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => removeFromCart(item.product_id)}
                              className="p-1 text-red-500 hover:text-red-700 ml-2"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Totals */}
                {cart.length > 0 && (
                  <div className="border-t pt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Subtotal:</span>
                      <span>${subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Tax (8%):</span>
                      <span>${tax.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between font-semibold text-lg border-t pt-2">
                      <span>Total:</span>
                      <span>${total.toFixed(2)}</span>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="space-y-2 mt-4">
                  {cart.length > 0 && (
                    <button
                      onClick={clearCart}
                      className="w-full px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 focus:ring-2 focus:ring-gray-500"
                    >
                      Clear Cart
                    </button>
                  )}
                  <button
                    onClick={processCheckout}
                    disabled={cart.length === 0}
                    className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed focus:ring-2 focus:ring-green-500"
                  >
                    Process Payment
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Receipt Modal */}
      {showReceipt && currentInvoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center">
                <Receipt className="h-5 w-5 mr-2 text-green-600" />
                Sale Complete
              </h3>
              <button
                onClick={() => setShowReceipt(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="font-medium">Invoice #:</span>
                <span>{currentInvoice.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Customer:</span>
                <span>{currentInvoice.customer_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Payment Method:</span>
                <span className="capitalize">{currentInvoice.payment_method}</span>
              </div>
              
              <hr />
              
              {currentInvoice.items.map((item) => (
                <div key={item.id} className="flex justify-between">
                  <span>
                    {item.product.name} × {item.quantity}
                  </span>
                  <span>${(item.unit_price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
              
              <hr />
              
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>${(currentInvoice.total_amount - currentInvoice.tax_amount).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax (8%):</span>
                <span>${currentInvoice.tax_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-semibold text-lg border-t pt-2">
                <span>Total:</span>
                <span>${currentInvoice.total_amount.toFixed(2)}</span>
              </div>
            </div>
            
            <div className="flex space-x-2 mt-6">
              <button
                onClick={() => window.print()}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Print Receipt
              </button>
              <button
                onClick={() => setShowReceipt(false)}
                className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default POS;