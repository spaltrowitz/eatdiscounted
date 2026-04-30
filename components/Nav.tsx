"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-gray-200 bg-white" aria-label="Main navigation">
      <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold text-gray-900">
          🔍 EatDiscounted
        </Link>
        <div className="flex gap-4 text-sm">
          <Link
            href="/"
            className={`transition-colors ${pathname === "/" ? "text-gray-900 font-medium" : "text-gray-500 hover:text-gray-900"}`}
            {...(pathname === "/" ? { "aria-current": "page" as const } : {})}
          >
            Search
          </Link>
          <Link
            href="/platforms"
            className={`transition-colors ${pathname === "/platforms" ? "text-gray-900 font-medium" : "text-gray-500 hover:text-gray-900"}`}
            {...(pathname === "/platforms" ? { "aria-current": "page" as const } : {})}
          >
            Platforms
          </Link>
          <Link
            href="/about"
            className={`transition-colors ${pathname === "/about" ? "text-gray-900 font-medium" : "text-gray-500 hover:text-gray-900"}`}
            {...(pathname === "/about" ? { "aria-current": "page" as const } : {})}
          >
            About
          </Link>
        </div>
      </div>
    </nav>
  );
}
