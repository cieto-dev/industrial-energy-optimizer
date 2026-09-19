"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function DemoSetupPage() {
  const router = useRouter();
  const [status, setStatus] = useState("Initializing Demo Mode...");

  useEffect(() => {
    async function loadDemo() {
      try {
        setStatus("Fetching demo scenario...");
        const res = await fetch("/demo_payload.json");
        if (!res.ok) {
          throw new Error("Failed to load demo_payload.json");
        }
        
        const payload = await res.json();
        
        setStatus("Applying Uttar Pradesh context...");
        // Mutate the payload to simulate the Uttar Pradesh Textile Plant
        if (payload.dashboard && payload.dashboard.factory) {
          payload.dashboard.factory.state = "Uttar Pradesh";
          payload.dashboard.factory.district = "Kanpur";
          payload.dashboard.factory.industry = "Textile";
          // Ensure it's blocked
          payload.firm_recommendation_blocked = true;
          if (payload.dashboard.recommendation) {
            payload.dashboard.recommendation.firm_recommendation_blocked = true;
            payload.dashboard.recommendation.status = "blocked";
          }
        }

        setStatus("Seeding engine state...");
        localStorage.setItem("last_optimize_result", JSON.stringify(payload));
        
        setStatus("Redirecting to honest results view...");
        setTimeout(() => {
          router.push("/results");
        }, 500);

      } catch (err) {
        console.error(err);
        setStatus("Error loading demo mode. Check console.");
      }
    }

    loadDemo();
  }, [router]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-surface border border-border p-8 rounded-lg shadow-sm text-center">
        <h1 className="text-xl font-bold text-foreground mb-4">National Stage Demo</h1>
        <div className="flex items-center justify-center mb-6">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-foreground border-t-transparent" />
        </div>
        <p className="text-sm font-medium text-foreground-muted animate-pulse">
          {status}
        </p>
      </div>
    </div>
  );
}
