'use client';

import { useEffect } from 'react';
import { FiAlertTriangle } from 'react-icons/fi';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900">
            <FiAlertTriangle className="h-6 w-6 text-red-600 dark:text-red-200" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-gray-100">
            Wystąpił błąd
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Przepraszamy, coś poszło nie tak.
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <button
            onClick={reset}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            Spróbuj ponownie
          </button>
        </div>
      </div>
    </div>
  );
} 