'use client';

import { useState } from 'react';
import { FiBarChart2, FiPieChart, FiTrendingUp, FiCalendar } from 'react-icons/fi';

interface ExpenseData {
  date: string;
  amount: number;
  category: string;
  store: string;
}

interface CategoryTotal {
  category: string;
  total: number;
  percentage: number;
}

export default function AnalysisPage() {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('month');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Example data - in real app this would come from API/database
  const expenseData: ExpenseData[] = [
    { date: '2024-03-20', amount: 156.78, category: 'Żywność', store: 'Biedronka' },
    { date: '2024-03-19', amount: 89.99, category: 'Chemia', store: 'Lidl' },
    { date: '2024-03-18', amount: 45.50, category: 'Żywność', store: 'Auchan' },
  ];

  const calculateTotalExpenses = () => {
    return expenseData.reduce((total, expense) => total + expense.amount, 0);
  };

  const calculateCategoryTotals = (): CategoryTotal[] => {
    const totals: { [key: string]: number } = {};
    const total = calculateTotalExpenses();

    expenseData.forEach(expense => {
      totals[expense.category] = (totals[expense.category] || 0) + expense.amount;
    });

    return Object.entries(totals).map(([category, amount]) => ({
      category,
      total: amount,
      percentage: (amount / total) * 100
    })).sort((a, b) => b.total - a.total);
  };

  const calculateDailyExpenses = () => {
    const dailyTotals: { [key: string]: number } = {};
    
    expenseData.forEach(expense => {
      dailyTotals[expense.date] = (dailyTotals[expense.date] || 0) + expense.amount;
    });

    return Object.entries(dailyTotals).map(([date, total]) => ({
      date,
      total
    })).sort((a, b) => a.date.localeCompare(b.date));
  };

  return (
    <div className="space-y-6">
      {/* Time range selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Analiza Wydatków
          </h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setTimeRange('week')}
              className={`px-4 py-2 rounded-lg ${
                timeRange === 'week'
                  ? 'bg-green-500 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Tydzień
            </button>
            <button
              onClick={() => setTimeRange('month')}
              className={`px-4 py-2 rounded-lg ${
                timeRange === 'month'
                  ? 'bg-green-500 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Miesiąc
            </button>
            <button
              onClick={() => setTimeRange('year')}
              className={`px-4 py-2 rounded-lg ${
                timeRange === 'year'
                  ? 'bg-green-500 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Rok
            </button>
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Całkowite Wydatki</p>
              <p className="text-2xl font-semibold text-gray-800 dark:text-gray-200">
                {calculateTotalExpenses().toFixed(2)} zł
              </p>
            </div>
            <FiBarChart2 className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Średnie Dzienne</p>
              <p className="text-2xl font-semibold text-gray-800 dark:text-gray-200">
                {(calculateTotalExpenses() / expenseData.length).toFixed(2)} zł
              </p>
            </div>
            <FiTrendingUp className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Liczba Transakcji</p>
              <p className="text-2xl font-semibold text-gray-800 dark:text-gray-200">
                {expenseData.length}
              </p>
            </div>
            <FiPieChart className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Category breakdown */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">
          Wydatki według Kategorii
        </h3>
        <div className="space-y-4">
          {calculateCategoryTotals().map((category) => (
            <div key={category.category} className="flex items-center">
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {category.category}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {category.total.toFixed(2)} zł
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${category.percentage}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Expense history */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">
          Historia Wydatków
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Data
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Kategoria
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Sklep
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Kwota
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {expenseData.map((expense, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {expense.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {expense.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {expense.store}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {expense.amount.toFixed(2)} zł
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 