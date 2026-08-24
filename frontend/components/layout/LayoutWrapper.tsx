"use client"

import { usePathname } from "next/navigation"

import { TopBar } from "./TopBar"

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const publicPages = ["/", "/story", "/technology", "/subsidies", "/knowledge-base", "/conventions", "/features"]
  const isPublicPage = publicPages.includes(pathname)

  if (isPublicPage) {
    return <main className="min-h-screen flex flex-col">{children}</main>
  }

  return (
    <>
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
