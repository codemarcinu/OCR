'use client';

import { useState } from 'react';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';

interface FAQItem {
  question: string;
  answer: string;
}

interface InstructionSection {
  title: string;
  content: string[];
}

export default function HelpPage() {
  const [openFAQ, setOpenFAQ] = useState<number | null>(null);

  const faqItems: FAQItem[] = [
    {
      question: 'Jak dodać nowy paragon?',
      answer: 'Przejdź do zakładki "Paragony" i kliknij przycisk "Dodaj Paragon". Możesz przeciągnąć zdjęcie paragonu lub wybrać je z dysku. System automatycznie przetworzy paragon i wyodrębni dane.'
    },
    {
      question: 'Jak zarządzać kategoriami wydatków?',
      answer: 'W zakładce "Kategorie" możesz dodawać, edytować i usuwać kategorie wydatków. Dla każdej kategorii możesz zdefiniować reguły automatycznego przypisywania produktów.'
    },
    {
      question: 'Jak działa zarządzanie spiżarnią?',
      answer: 'Zakładka "Spiżarnia" pozwala na śledzenie zapasów. Produkty są automatycznie dodawane po przetworzeniu paragonów. Możesz ręcznie aktualizować ilości i oznaczać produkty jako mrożone.'
    },
    {
      question: 'Jak zaplanować posiłki?',
      answer: 'W zakładce "Gotowanie" znajdziesz kalendarz planowania posiłków. Możesz przypisywać przepisy do konkretnych dni i automatycznie generować listę zakupów na podstawie brakujących składników.'
    },
    {
      question: 'Jak eksportować dane?',
      answer: 'W zakładce "Ustawienia" znajdziesz sekcję "Zarządzanie Danymi" z opcjami eksportu i importu danych. Możesz wybrać format eksportu (CSV lub Excel) i zakres dat.'
    }
  ];

  const instructions: InstructionSection[] = [
    {
      title: 'Rozpoczęcie pracy',
      content: [
        'Zaloguj się do aplikacji używając swoich danych.',
        'Przejdź do zakładki "Kategorie" i skonfiguruj podstawowe kategorie wydatków.',
        'W zakładce "Ustawienia" dostosuj preferencje aplikacji do swoich potrzeb.',
        'Możesz rozpocząć dodawanie paragonów w zakładce "Paragony".'
      ]
    },
    {
      title: 'Przetwarzanie paragonów',
      content: [
        'Zrób wyraźne zdjęcie paragonu lub zeskanuj go.',
        'Upewnij się, że paragon jest dobrze oświetlony i wszystkie dane są czytelne.',
        'Dodaj paragon w aplikacji i poczekaj na przetworzenie.',
        'Sprawdź poprawność rozpoznanych danych i w razie potrzeby skoryguj je.'
      ]
    },
    {
      title: 'Zarządzanie spiżarnią',
      content: [
        'Produkty są automatycznie dodawane do spiżarni po przetworzeniu paragonu.',
        'Możesz ręcznie dodawać i usuwać produkty.',
        'Ustaw powiadomienia o niskim stanie zapasów.',
        'Oznacz produkty jako mrożone, aby lepiej śledzić ich lokalizację.'
      ]
    },
    {
      title: 'Planowanie posiłków',
      content: [
        'Dodaj swoje ulubione przepisy w zakładce "Gotowanie".',
        'Zaplanuj posiłki na cały tydzień w kalendarzu.',
        'Sprawdź dostępność składników w spiżarni.',
        'Wygeneruj listę zakupów brakujących składników.'
      ]
    }
  ];

  return (
    <div className="space-y-6">
      {/* FAQ Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6">
          Często Zadawane Pytania
        </h2>
        <div className="space-y-4">
          {faqItems.map((item, index) => (
            <div
              key={index}
              className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
            >
              <button
                className="w-full flex justify-between items-center p-4 text-left focus:outline-none"
                onClick={() => setOpenFAQ(openFAQ === index ? null : index)}
              >
                <span className="font-medium text-gray-800 dark:text-gray-200">
                  {item.question}
                </span>
                {openFAQ === index ? (
                  <FiChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <FiChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
              {openFAQ === index && (
                <div className="p-4 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
                  <p className="text-gray-600 dark:text-gray-300">
                    {item.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Instructions Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6">
          Instrukcje Użytkowania
        </h2>
        <div className="space-y-6">
          {instructions.map((section, index) => (
            <div key={index}>
              <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-3">
                {section.title}
              </h3>
              <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-300">
                {section.content.map((item, itemIndex) => (
                  <li key={itemIndex}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Contact Support */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
          Potrzebujesz pomocy?
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-4">
          Jeśli nie znalazłeś odpowiedzi na swoje pytanie, skontaktuj się z nami:
        </p>
        <div className="space-y-2">
          <p className="text-gray-600 dark:text-gray-300">
            Email: pomoc@ocrmanager.pl
          </p>
          <p className="text-gray-600 dark:text-gray-300">
            Godziny wsparcia: Pon-Pt 9:00 - 17:00
          </p>
        </div>
      </div>
    </div>
  );
} 