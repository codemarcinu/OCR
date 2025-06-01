'use client';

import { useState } from 'react';
import { FiPlus, FiEdit2, FiTrash2, FiCheck, FiX } from 'react-icons/fi';

interface Category {
  id: string;
  name: string;
  description: string;
  color: string;
  rules: string[];
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([
    {
      id: '1',
      name: 'Żywność',
      description: 'Artykuły spożywcze i napoje',
      color: '#4CAF50',
      rules: ['mleko', 'chleb', 'mięso']
    },
    {
      id: '2',
      name: 'Chemia',
      description: 'Środki czystości i higieny',
      color: '#2196F3',
      rules: ['proszek', 'mydło', 'szampon']
    }
  ]);

  const [editingCategory, setEditingCategory] = useState<string | null>(null);
  const [newCategory, setNewCategory] = useState<Partial<Category>>({
    name: '',
    description: '',
    color: '#4CAF50',
    rules: []
  });
  const [showAddForm, setShowAddForm] = useState(false);
  const [newRule, setNewRule] = useState('');

  const handleAddCategory = () => {
    if (!newCategory.name) return;

    const category: Category = {
      id: Date.now().toString(),
      name: newCategory.name,
      description: newCategory.description || '',
      color: newCategory.color || '#4CAF50',
      rules: newCategory.rules || []
    };

    setCategories(prev => [...prev, category]);
    setShowAddForm(false);
    setNewCategory({
      name: '',
      description: '',
      color: '#4CAF50',
      rules: []
    });
  };

  const handleDeleteCategory = (id: string) => {
    setCategories(prev => prev.filter(category => category.id !== id));
  };

  const handleAddRule = (categoryId: string) => {
    if (!newRule.trim()) return;

    setCategories(prev =>
      prev.map(category =>
        category.id === categoryId
          ? { ...category, rules: [...category.rules, newRule.trim()] }
          : category
      )
    );
    setNewRule('');
  };

  const handleDeleteRule = (categoryId: string, ruleIndex: number) => {
    setCategories(prev =>
      prev.map(category =>
        category.id === categoryId
          ? {
              ...category,
              rules: category.rules.filter((_, index) => index !== ruleIndex)
            }
          : category
      )
    );
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Zarządzanie Kategoriami
          </h2>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center"
          >
            <FiPlus className="mr-2" />
            Dodaj Kategorię
          </button>
        </div>

        {showAddForm && (
          <div className="mb-6 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
              Dodaj Nową Kategorię
            </h3>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Nazwa kategorii"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                value={newCategory.name}
                onChange={e => setNewCategory(prev => ({ ...prev, name: e.target.value }))}
              />
              <input
                type="text"
                placeholder="Opis"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                value={newCategory.description}
                onChange={e => setNewCategory(prev => ({ ...prev, description: e.target.value }))}
              />
              <input
                type="color"
                className="w-full h-10 p-1 rounded-lg"
                value={newCategory.color}
                onChange={e => setNewCategory(prev => ({ ...prev, color: e.target.value }))}
              />
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                >
                  Anuluj
                </button>
                <button
                  onClick={handleAddCategory}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                >
                  Dodaj
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {categories.map((category) => (
            <div
              key={category.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: category.color }}
                  />
                  <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">
                    {category.name}
                  </h3>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleDeleteCategory(category.id)}
                    className="p-1 text-red-600 hover:text-red-900 dark:hover:text-red-400"
                  >
                    <FiTrash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                {category.description}
              </p>
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700 dark:text-gray-300">
                  Reguły przypisywania:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {category.rules.map((rule, index) => (
                    <div
                      key={index}
                      className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-full px-3 py-1"
                    >
                      <span className="text-sm text-gray-700 dark:text-gray-300">{rule}</span>
                      <button
                        onClick={() => handleDeleteRule(category.id, index)}
                        className="ml-2 text-gray-500 hover:text-red-500"
                      >
                        <FiX className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex mt-2">
                  <input
                    type="text"
                    placeholder="Dodaj nową regułę"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    value={newRule}
                    onChange={e => setNewRule(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && handleAddRule(category.id)}
                  />
                  <button
                    onClick={() => handleAddRule(category.id)}
                    className="ml-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                  >
                    <FiPlus className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 