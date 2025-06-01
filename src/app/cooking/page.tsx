'use client';

import { useState } from 'react';
import { FiPlus, FiClock, FiUsers, FiList, FiCalendar } from 'react-icons/fi';

interface Recipe {
  id: string;
  name: string;
  preparationTime: number;
  servings: number;
  ingredients: Ingredient[];
  instructions: string[];
  category: string;
}

interface Ingredient {
  name: string;
  quantity: number;
  unit: string;
}

interface MealPlan {
  date: string;
  meals: {
    type: 'breakfast' | 'lunch' | 'dinner';
    recipeId: string;
  }[];
}

export default function CookingPage() {
  const [activeTab, setActiveTab] = useState<'recipes' | 'planning'>('recipes');
  const [recipes, setRecipes] = useState<Recipe[]>([
    {
      id: '1',
      name: 'Spaghetti Bolognese',
      preparationTime: 45,
      servings: 4,
      ingredients: [
        { name: 'Makaron spaghetti', quantity: 500, unit: 'g' },
        { name: 'Mięso mielone', quantity: 400, unit: 'g' },
        { name: 'Passata pomidorowa', quantity: 500, unit: 'ml' },
      ],
      instructions: [
        'Zagotuj wodę na makaron',
        'Podsmaż mięso mielone',
        'Dodaj passatę i gotuj 30 minut',
      ],
      category: 'Dania główne'
    }
  ]);

  const [showAddRecipe, setShowAddRecipe] = useState(false);
  const [newRecipe, setNewRecipe] = useState<Partial<Recipe>>({
    name: '',
    preparationTime: 30,
    servings: 4,
    ingredients: [],
    instructions: [],
    category: ''
  });

  const handleAddRecipe = () => {
    if (!newRecipe.name || !newRecipe.category) {
      return; // Show error message in real app
    }

    const recipe: Recipe = {
      id: Date.now().toString(),
      name: newRecipe.name,
      preparationTime: newRecipe.preparationTime || 30,
      servings: newRecipe.servings || 4,
      ingredients: newRecipe.ingredients || [],
      instructions: newRecipe.instructions || [],
      category: newRecipe.category
    };

    setRecipes(prev => [...prev, recipe]);
    setShowAddRecipe(false);
    setNewRecipe({
      name: '',
      preparationTime: 30,
      servings: 4,
      ingredients: [],
      instructions: [],
      category: ''
    });
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveTab('recipes')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'recipes'
                  ? 'bg-green-500 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Przepisy
            </button>
            <button
              onClick={() => setActiveTab('planning')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'planning'
                  ? 'bg-green-500 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Planowanie Posiłków
            </button>
          </div>
          {activeTab === 'recipes' && (
            <button
              onClick={() => setShowAddRecipe(true)}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center"
            >
              <FiPlus className="mr-2" />
              Dodaj Przepis
            </button>
          )}
        </div>

        {activeTab === 'recipes' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recipes.map((recipe) => (
              <div
                key={recipe.id}
                className="bg-white dark:bg-gray-700 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-600"
              >
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
                  {recipe.name}
                </h3>
                <div className="flex items-center text-gray-600 dark:text-gray-400 text-sm mb-4">
                  <FiClock className="mr-2" />
                  {recipe.preparationTime} min
                  <FiUsers className="ml-4 mr-2" />
                  {recipe.servings} porcji
                </div>
                <div className="mb-4">
                  <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Składniki:
                  </h4>
                  <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 text-sm">
                    {recipe.ingredients.map((ingredient, index) => (
                      <li key={index}>
                        {ingredient.name} - {ingredient.quantity} {ingredient.unit}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Instrukcje:
                  </h4>
                  <ol className="list-decimal list-inside text-gray-600 dark:text-gray-400 text-sm">
                    {recipe.instructions.map((instruction, index) => (
                      <li key={index}>{instruction}</li>
                    ))}
                  </ol>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'planning' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                Plan na ten tydzień
              </h3>
              <button className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg flex items-center">
                <FiCalendar className="mr-2" />
                Wybierz tydzień
              </button>
            </div>
            <div className="grid grid-cols-7 gap-4">
              {Array.from({ length: 7 }).map((_, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-gray-700 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-600"
                >
                  <div className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    {new Date(Date.now() + index * 24 * 60 * 60 * 1000).toLocaleDateString('pl-PL', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric'
                    })}
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Śniadanie</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Obiad</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Kolacja</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {showAddRecipe && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full m-4">
              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
                Dodaj Nowy Przepis
              </h3>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Nazwa przepisu"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  value={newRecipe.name}
                  onChange={e => setNewRecipe(prev => ({ ...prev, name: e.target.value }))}
                />
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="number"
                    placeholder="Czas przygotowania (min)"
                    className="px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    value={newRecipe.preparationTime}
                    onChange={e => setNewRecipe(prev => ({ ...prev, preparationTime: Number(e.target.value) }))}
                  />
                  <input
                    type="number"
                    placeholder="Liczba porcji"
                    className="px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    value={newRecipe.servings}
                    onChange={e => setNewRecipe(prev => ({ ...prev, servings: Number(e.target.value) }))}
                  />
                </div>
                <input
                  type="text"
                  placeholder="Kategoria"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  value={newRecipe.category}
                  onChange={e => setNewRecipe(prev => ({ ...prev, category: e.target.value }))}
                />
                <div className="mt-4 flex justify-end space-x-2">
                  <button
                    onClick={() => setShowAddRecipe(false)}
                    className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                  >
                    Anuluj
                  </button>
                  <button
                    onClick={handleAddRecipe}
                    className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                  >
                    Dodaj
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 