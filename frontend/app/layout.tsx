import type { Metadata } from "next"
import { Outfit } from "next/font/google"
import "./global.css"
import { ThemeProvider } from "@/components/theme/ThemeProvider"
import { ErrorBoundary } from "@/components/layout/ErrorBoundary"

const outfit = Outfit({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Industrial Energy Optimizer",
  description: "Techno-economic decision-support tool for industrial MSMEs",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${outfit.className} bg-background text-foreground antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  )
}
