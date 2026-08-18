import Link from "next/link"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { Zap } from "lucide-react"

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full glass-panel border-b-0 border-border/40 backdrop-blur-md supports-[backdrop-filter]:bg-background/40">
      <div className="container flex h-16 items-center">
        <div className="mr-4 flex">
          <Link href="/" className="mr-6 flex items-center space-x-3 transition-transform hover:scale-105">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-primary-foreground shadow-[0_0_15px_rgba(32,201,151,0.5)]">
              <Zap size={18} className="fill-current" />
            </div>
            <span className="font-bold inline-block text-lg bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
              Energy Optimizer
            </span>
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <nav className="flex items-center space-x-2">
            <ThemeToggle />
          </nav>
        </div>
      </div>
    </header>
  )
}
