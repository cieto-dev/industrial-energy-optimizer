"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { usePathname } from "next/navigation"
import { Button } from "@/components/reports/common/Button"

export function ThemeToggle() {
  const { setTheme, theme } = useTheme()

  const pathname = usePathname()
  const isStoryPage = pathname === "/story"

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      className={isStoryPage ? "bg-black/20 border-white/20 text-white hover:bg-white/10 hover:text-white" : ""}
    >
      <Sun className={`h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0 ${isStoryPage ? 'dark:-rotate-90 dark:scale-0' : ''}`} />
      <Moon className={`absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100 ${isStoryPage ? 'dark:rotate-0 dark:scale-100' : ''}`} />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
