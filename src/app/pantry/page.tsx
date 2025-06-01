'use client';

import { useState } from 'react';
import { FiPlus, FiEdit2, FiTrash2, FiSnowflake } from 'react-icons/fi';

interface PantryItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  isFrozen: boolean;
  expirationDate?: string;
  category: string;
}

export default function PantryPage() {
  const [items, setItems] = useState<PantryItem[]>([
    {
      id: '1',
      name: 'Mleko',
      quantity: 2,
      unit: 'l',
      isFrozen: false,
      category: 'Nabiał',
      expirationDate: '2024-04-01'
    },
    {
      id: '2',
      name: 'Pierogi',
      quantity: 1,
      unit: 'opak',
      isFrozen: true,
      category: 'Dania gotowe'
    }
  ]);

  const [showAddForm, setShowAddForm] = useState(false);
  const [newItem, setNewItem] = useState<Partial<PantryItem>>({
    name: '',
    quantity: 1,
    unit: 'szt',
    isFrozen: false,
    category: ''
  });

  const handleAddItem = () => {
    if (!newItem.name || !newItem.quantity || !newItem.unit || !newItem.category) {
      return; // Show error message in real app
    }

    const item: PantryItem = {
      id: Date.now().toString(),
      name: newItem.name,
      quantity: newItem.quantity,
      unit: newItem.unit,
      isFrozen: newItem.isFrozen || false,
      category: newItem.category,
      expirationDate: newItem.expirationDate
    };

    setItems(prev => [...prev, item]);
    setShowAddForm(false);
    setNewItem({
      name: '',
      quantity: 1,
      unit: 'szt',
      isFrozen: false,
      category: ''
    });
  };

  const toggleFrozen = (id: string) => {
    setItems(prev =>
      prev.map(item =>
        item.id === id ? { ...item, isFrozen: !item.isFrozen } : item
      )
    );
  };

  const deleteItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Zarządzanie Spiżarnią
          </h2>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center"
          >
            <FiPlus className="mr-2" />
            Dodaj Produkt
          </button>
        </div>

        {showAddForm && (
          <div className="mb-6 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
              Dodaj Nowy Produkt
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Nazwa produktu"
                className="px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                value={newItem.name}
                onChange={e => setNewItem(prev => ({ ...prev, name: e.target.value }))}
              />
              <input
                type="number"
                placeholder="Ilość"
                min="0"
                className="px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                value={newItem.quantity}
                onChange={e => setNewItem(prev => ({ ...prev, quantity: Number(e.target.value) }))}
              />
              <select
                className="px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                value={newItem.unit}
                onChange={e => setNewItem(prev => ({ ...prev, unit: e.target.value }))}
              >
                <option value="szt">Sztuki</option>
                <option value="kg">Kilogramy</option>
                <option value="l">Litry</option>
                <option value="opak">Opakowania</option>
              </select>
              <input
                type="text"
                placeholder="Kategoria"
                className="px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                value={newItem.category}
                onChange={e => setNewItem(prev => ({ ...prev, category: e.target.value }))}
              />
              <input
                type="date"
                placeholder="Data ważności"
                className="px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                value={newItem.expirationDate}
                onChange={e => setNewItem(prev => ({ ...prev, expirationDate: e.target.value }))}
              />
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isFrozen"
                  className="mr-2"
                  checked={newItem.isFrozen}
                  onChange={e => setNewItem(prev => ({ ...prev, isFrozen: e.target.checked }))}
                />
                <label htmlFor="isFrozen" className="text-gray-700 dark:text-gray-300">
                  Produkt mrożony
                </label>
              </div>
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Anuluj
              </button>
              <button
                onClick={handleAddItem}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                Dodaj
              </button>
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Produkt
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Ilość
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Kategoria
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Data ważności
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Akcje
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    <div className="flex items-center">
                      {item.name}
                      {item.isFrozen && (
                        <FiSnowflake className="ml-2 text-blue-500" />
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {item.quantity} {item.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {item.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {item.expirationDate || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => toggleFrozen(item.id)}
                        className={`p-1 rounded-full ${
                          item.isFrozen ? 'text-blue-500 hover:text-blue-700' : 'text-gray-400 hover:text-gray-600'
                        }`}
                      >
                        <FiSnowflake className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => deleteItem(item.id)}
                        className="p-1 text-red-600 hover:text-red-900 dark:hover:text-red-400"
                      >
                        <FiTrash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                    Brak produktów w spiżarni
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 