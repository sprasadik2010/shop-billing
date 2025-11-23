import React, { useState } from 'react';
import POS from './components/POS';
import AdminDashboard from './components/AdminDashboard';
import { ShoppingCart, BarChart3 } from 'lucide-react';
import './index.css';

type AppMode = 'pos' | 'admin';

const App: React.FC = () => {
  const [mode, setMode] = useState<AppMode>('pos');

  // Common header with mode switcher
  const Header = () => (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            {mode === 'pos' ? (
              <ShoppingCart className="h-8 w-8 text-green-600" />
            ) : (
              <BarChart3 className="h-8 w-8 text-blue-600" />
            )}
            <h1 className="ml-2 text-2xl font-bold text-gray-900">
              {mode === 'pos' ? 'ShopPOS' : 'Admin Panel'}
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex gap-2">
              <button
                onClick={() => setMode('pos')}
                className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  mode === 'pos'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <ShoppingCart className="h-4 w-4 mr-1" />
                POS
              </button>
              <button
                onClick={() => setMode('admin')}
                className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  mode === 'admin'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <BarChart3 className="h-4 w-4 mr-1" />
                Admin
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );

  return (
    <div className="App min-h-screen bg-gray-100">
      <Header />
      <main>
        {mode === 'pos' ? <POS /> : <AdminDashboard />}
      </main>
    </div>
  );
};

export default App;