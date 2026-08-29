import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./global.css"
import { ThemeProvider } from "@/components/theme/ThemeProvider"
import { ErrorBoundary } from "@/components/layout/ErrorBoundary"

import { LayoutWrapper } from "@/components/layout/LayoutWrapper"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Urjiva Energy Platform",
  description: "AI-powered clean energy transition platform for Indian MSMEs",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-background text-foreground antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange
        >
          <ErrorBoundary>
            <LayoutWrapper>
              {children}
            </LayoutWrapper>
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  )
}
