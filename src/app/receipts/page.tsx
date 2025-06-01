'use client';

import { useState } from 'react';
import { FiUpload, FiFile, FiTrash2 } from 'react-icons/fi';

interface Receipt {
  id: string;
  date: string;
  store: string;
  totalAmount: number;
  items: ReceiptItem[];
}

interface ReceiptItem {
  name: string;
  quantity: number;
  unit: string;
  price: number;
  discount?: number;
  finalPrice: number;
}

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files?.length) return;

    setIsUploading(true);
    
    try {
      // Here we would process the files with OCR
      // For now, just a mock implementation
      const newReceipts: Receipt[] = Array.from(files).map((file, index) => ({
        id: `receipt-${Date.now()}-${index}`,
        date: new Date().toISOString().split('T')[0],
        store: 'Przykładowy Sklep',
        totalAmount: 123.45,
        items: [
          {
            name: 'Przykładowy Produkt',
            quantity: 1,
            unit: 'szt',
            price: 123.45,
            finalPrice: 123.45
          }
        ]
      }));

      setReceipts(prev => [...prev, ...newReceipts]);
    } catch (error) {
      console.error('Error processing receipts:', error);
      // Here we would show an error notification
    } finally {
      setIsUploading(false);
    }
  };

  const deleteReceipt = (id: string) => {
    setReceipts(prev => prev.filter(receipt => receipt.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
          Dodaj Paragony
        </h2>
        <div className="flex items-center justify-center w-full">
          <label
            htmlFor="receipt-upload"
            className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-700 hover:bg-gray-100"
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <FiUpload className="w-8 h-8 mb-3 text-gray-400" />
              <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                <span className="font-semibold">Kliknij aby wybrać</span> lub przeciągnij i upuść
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                PNG, JPG lub PDF (max. 10MB)
              </p>
            </div>
            <input
              id="receipt-upload"
              type="file"
              className="hidden"
              multiple
              accept="image/*,.pdf"
              onChange={handleFileUpload}
              disabled={isUploading}
            />
          </label>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
            Przetworzone Paragony
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Data
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Sklep
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Kwota
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Akcje
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {receipts.map((receipt) => (
                  <tr key={receipt.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {receipt.date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {receipt.store}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {receipt.totalAmount.toFixed(2)} zł
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <button
                        onClick={() => deleteReceipt(receipt.id)}
                        className="text-red-600 hover:text-red-900 dark:hover:text-red-400"
                      >
                        <FiTrash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {receipts.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                      Brak przetworzonych paragonów
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
} 