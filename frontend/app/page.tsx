import { Sidebar } from "@/components/layout/Sidebar"
import { Navbar } from "@/components/layout/Navbar"

export default function Home() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="mx-auto max-w-4xl space-y-4">
            <h1 className="text-3xl font-bold tracking-tight">Welcome to the Industrial Energy Optimizer</h1>
            <p className="text-muted-foreground">Select an option from the sidebar to begin.</p>
          </div>
        </main>
      </div>
    </div>
  )
}
