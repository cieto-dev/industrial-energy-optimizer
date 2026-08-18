import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./global.css"
import { ThemeProvider } from "@/components/theme/ThemeProvider"

const inter = Inter({ subsets: ["latin"] })

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
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
