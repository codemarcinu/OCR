'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  FiHome,
  FiFileText, 
  FiBox, 
  FiBook, 
  FiPieChart, 
  FiGrid, 
  FiSettings, 
  FiHelpCircle,
  FiSun,
  FiMoon 
} from 'react-icons/fi';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: <FiHome className="w-5 h-5" /> },
  { label: 'Paragony', href: '/receipts', icon: <FiFileText className="w-5 h-5" /> },
  { label: 'Spiżarnia', href: '/pantry', icon: <FiBox className="w-5 h-5" /> },
  { label: 'Gotowanie', href: '/cooking', icon: <FiBook className="w-5 h-5" /> },
  { label: 'Analiza', href: '/analysis', icon: <FiPieChart className="w-5 h-5" /> },
  { label: 'Kategorie', href: '/categories', icon: <FiGrid className="w-5 h-5" /> },
  { label: 'Ustawienia', href: '/settings', icon: <FiSettings className="w-5 h-5" /> },
  { label: 'Pomoc', href: '/help', icon: <FiHelpCircle className="w-5 h-5" /> },
];

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const pathname = usePathname();

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className={`min-h-screen ${isDarkMode ? 'dark' : ''}`}>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
        {/* Sidebar */}
        <aside className="z-20 hidden w-64 overflow-y-auto bg-white dark:bg-gray-800 md:block flex-shrink-0">
          <div className="py-4 text-gray-500 dark:text-gray-400">
            <div className="ml-6 text-lg font-bold text-gray-800 dark:text-gray-200">
              OCR Manager
            </div>
            <nav className="mt-6">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center px-6 py-3 font-medium ${
                      isActive
                        ? 'text-green-500 bg-green-100 dark:bg-green-900 dark:bg-opacity-30'
                        : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                    }`}
                  >
                    {item.icon}
                    <span className="ml-4">{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </aside>

        {/* Main content */}
        <div className="flex flex-col flex-1">
          {/* Header */}
          <header className="z-10 py-4 bg-white dark:bg-gray-800 shadow-md">
            <div className="flex items-center justify-between px-6">
              <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-200">
                OCR Manager
              </h1>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                aria-label="Toggle theme"
              >
                {isDarkMode ? (
                  <FiSun className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                ) : (
                  <FiMoon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                )}
              </button>
            </div>
          </header>

          {/* Main content */}
          <main className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
            <div className="container px-6 py-8 mx-auto">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
} 