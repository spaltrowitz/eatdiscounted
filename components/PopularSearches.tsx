"use client";

import { useRouter } from "next/navigation";

const POPULAR_NYC = [
  "Carbone",
  "Tatiana",
  "Thai Diner",
  "Oxomoco",
  "L'Artusi",
  "Via Carota",
  "Los Tacos No. 1",
  "Joe's Pizza",
  "Lilia",
  "Don Angie",
  "Atomix",
  "Dhamaka",
];

export function PopularSearches() {
  const router = useRouter();

  function handleClick(name: string) {
    router.push(`/?q=${encodeURIComponent(name)}`);
  }

  return (
    <div className="mt-8">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
        Popular in NYC
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {POPULAR_NYC.map((name) => (
          <button
            key={name}
            onClick={() => handleClick(name)}
            className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-700 transition-colors hover:border-gray-400 hover:bg-gray-50"
          >
            {name}
          </button>
        ))}
      </div>
    </div>
  );
}
