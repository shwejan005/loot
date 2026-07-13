import Link from "next/link";

export function NavBar() {
  return (
    <header className="border-b">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="rounded bg-primary px-2 py-1 text-sm text-primary-foreground">Loot</span>
          <span>Coding Memory</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm text-muted-foreground">
          <Link href="/" className="hover:text-foreground">Dashboard</Link>
          <Link href="/knowledge" className="hover:text-foreground">Knowledge</Link>
          <Link href="/analytics" className="hover:text-foreground">Analytics</Link>
        </nav>
      </div>
    </header>
  );
}
