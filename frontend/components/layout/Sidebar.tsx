"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/utils"
import { LayoutDashboard, FileText, FileBarChart } from "lucide-react"

const routes = [
  {
    label: "Input Assessment",
    icon: FileText,
    href: "/assessment",
  },
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/dashboard",
  },
  {
    label: "Reports",
    icon: FileBarChart,
    href: "/reports",
  }
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col overflow-y-auto border-r bg-card py-4">
      <div className="px-3 py-2">
        <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
          Workflow
        </h2>
        <div className="space-y-1">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "group flex w-full items-center justify-start rounded-md p-3 text-sm font-medium transition-colors",
                pathname === route.href
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <route.icon className={cn("mr-2 h-5 w-5", pathname === route.href ? "text-primary" : "text-muted-foreground")} />
              {route.label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
