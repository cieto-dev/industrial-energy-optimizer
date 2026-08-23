"use client"

import { usePathname } from "next/navigation"
import { Sidebar } from "./Sidebar"
import { TopBar } from "./TopBar"

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isPublicPage = pathname === "/" || pathname === "/story"

  if (isPublicPage) {
    return <main className="min-h-screen flex flex-col">{children}</main>
  }

  return (
    <>
      {/* Sidebar is a fixed overlay drawer — renders once globally */}
      <Sidebar />

      {/* Main content column */}
      <div className="flex h-screen flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto bg-background">
          {children}
        </main>
      </div>
    </>
  )
}
