"use client"

import React from "react"
import { CredibilityProvider } from "../../components/industrial-intelligence/CredibilityPanel"

export default function IndustrialIntelligenceLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <CredibilityProvider>
      {children}
    </CredibilityProvider>
  )
}
