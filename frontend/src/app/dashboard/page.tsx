'use client';

import { FiShoppingBag, FiPieChart, FiBox, FiCalendar } from 'react-icons/fi';

interface DashboardCard {
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
}

const DashboardCard = ({ title, icon, content }: DashboardCard) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">{title}</h3>
      <div className="text-green-500">{icon}</div>
    </div>
    <div className="text-gray-600 dark:text-gray-400">{content}</div>
  </div>
);

export default function DashboardPage() {
  const recentPurchases = [
    { date: '2024-03-20', store: 'Biedronka', amount: 156.78 },
    { date: '2024-03-19', store: 'Lidl', amount: 89.99 },
  ];

  const monthlyExpenses = {
    current: 1250.45,
    previous: 1100.20,
    difference: 150.25,
  };

  const lowStock = [
    'Mleko',
    'Chleb',
    'Jajka',
  ];

  const todaysMeals = [
    { meal: 'Śniadanie', recipe: 'Owsianka z owocami' },
    { meal: 'Obiad', recipe: 'Spaghetti Bolognese' },
    { meal: 'Kolacja', recipe: 'Sałatka z tuńczykiem' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <DashboardCard
        title="Ostatnie Zakupy"
        icon={<FiShoppingBag className="w-6 h-6" />}
        content={
          <div className="space-y-2">
            {recentPurchases.map((purchase, index) => (
              <div key={index} className="flex justify-between">
                <span>{purchase.date} - {purchase.store}</span>
                <span className="font-medium">{purchase.amount.toFixed(2)} zł</span>
              </div>
            ))}
          </div>
        }
      />

      <DashboardCard
        title="Podsumowanie Miesięczne"
        icon={<FiPieChart className="w-6 h-6" />}
        content={
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Bieżący miesiąc:</span>
              <span className="font-medium">{monthlyExpenses.current.toFixed(2)} zł</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Poprzedni miesiąc:</span>
              <span>{monthlyExpenses.previous.toFixed(2)} zł</span>
            </div>
            <div className={`flex justify-between text-sm ${monthlyExpenses.difference > 0 ? 'text-red-500' : 'text-green-500'}`}>
              <span>Różnica:</span>
              <span>{monthlyExpenses.difference > 0 ? '+' : ''}{monthlyExpenses.difference.toFixed(2)} zł</span>
            </div>
          </div>
        }
      />

      <DashboardCard
        title="Stan Spiżarni"
        icon={<FiBox className="w-6 h-6" />}
        content={
          <div className="space-y-2">
            <p className="text-sm mb-2">Produkty na wyczerpaniu:</p>
            <ul className="list-disc list-inside">
              {lowStock.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        }
      />

      <DashboardCard
        title="Plan Posiłków na Dziś"
        icon={<FiCalendar className="w-6 h-6" />}
        content={
          <div className="space-y-2">
            {todaysMeals.map((meal, index) => (
              <div key={index} className="flex justify-between">
                <span className="font-medium">{meal.meal}:</span>
                <span>{meal.recipe}</span>
              </div>
            ))}
          </div>
        }
      />
    </div>
  );
} 