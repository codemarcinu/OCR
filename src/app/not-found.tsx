'use client';

import Link from 'next/link';
import { FiHome } from 'react-icons/fi';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-gray-100">
            404 - Strona nie znaleziona
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Przepraszamy, nie mogliśmy znaleźć strony, której szukasz.
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <Link
            href="/dashboard"
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <FiHome className="mr-2 h-5 w-5" />
            Wróć do strony głównej
          </Link>
        </div>
      </div>
    </div>
  );
} 