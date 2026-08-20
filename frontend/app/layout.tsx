import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./global.css"
import { ThemeProvider } from "@/components/theme/ThemeProvider"
import { ErrorBoundary } from "@/components/layout/ErrorBoundary"
import { Sidebar } from "@/components/layout/Sidebar"
import { TopBar } from "@/components/layout/TopBar"
import { SidebarProvider } from "@/components/layout/SidebarContext"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "CIETO Energy Platform",
  description: "AI-powered clean energy transition platform for Indian MSMEs",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-zinc-950 text-foreground antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <ErrorBoundary>
            <SidebarProvider>
              {/* Sidebar is a fixed overlay drawer — renders once globally */}
              <Sidebar />

              {/* Main content column */}
              <div className="flex h-screen flex-col overflow-hidden">
                <TopBar />
                <main className="flex-1 overflow-y-auto">
                  {children}
                </main>
              </div>
            </SidebarProvider>
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  )
}
