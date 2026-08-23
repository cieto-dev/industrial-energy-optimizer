"use client"

import { useEffect, useMemo, useState } from "react"
import { Loader2, RotateCcw, Zap } from "lucide-react"

import { apiService } from "@/services/api"

import {
  ScenarioInputs,
  ScenarioPathway,
  ScenarioPlaygroundResponse,
} from "@/types/scenario"


const DEFAULT_SCENARIO: ScenarioInputs = {
  biomass_price_inr_per_kg: 7.0,
  electricity_tariff_inr_per_kwh: 8.0,
  subsidy_pct: 0,
  budget_inr: 3000000,
  carbon_price_inr_per_tco2: 0,
}


function formatINR(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value)
}


function getLastOptimization(): {
  pathways: ScenarioPathway[]
  weights?: Record<string, number>
} | null {

  if (typeof window === "undefined") {
    return null
  }

  try {
    const raw =
      localStorage.getItem(
        "scenario_playground_pathways"
      )

    if (!raw) {
      return null
    }

    return JSON.parse(raw)
  } catch {
    return null
  }
}


export default function ScenarioPlaygroundPage() {

  const [scenario, setScenario] =
    useState<ScenarioInputs>(
      DEFAULT_SCENARIO
    )

  const [pathways, setPathways] =
    useState<ScenarioPathway[]>([])

  const [weights, setWeights] =
    useState<Record<string, number> | undefined>()

  const [result, setResult] =
    useState<ScenarioPlaygroundResponse | null>(null)

  const [isLoading, setIsLoading] =
    useState(false)

  const [error, setError] =
    useState<string | null>(null)


  useEffect(() => {

    const saved =
      getLastOptimization()

    if (saved?.pathways?.length) {

      setPathways(
        saved.pathways
      )

      setWeights(
        saved.weights
      )

      return
    }

    // Fallback only for frontend development.
    // In production the user should arrive here after optimization.
    const demoPathways: ScenarioPathway[] = [
      {
        scenario_id: "scenario_biomass",
        technology_sequence: [
          "biomass_boiler",
        ],
        base_capex_inr: 1500000,
        base_annual_opex_inr: 700000,
        base_biomass_kg_year: 100000,
        annual_co2_tonnes: 600,
        feasible: true,
        biomass_dependence: 1,
        reliability_score_pct: 82,
        co2_reduction_pct: 35,
      },

      {
        scenario_id: "scenario_electric",
        technology_sequence: [
          "electric_boiler",
        ],
        base_capex_inr: 2200000,
        base_annual_opex_inr: 650000,
        base_electricity_kwh_year: 120000,
        annual_co2_tonnes: 450,
        feasible: true,
        electricity_dependence: 1,
        reliability_score_pct: 90,
        co2_reduction_pct: 50,
      },

      {
        scenario_id: "scenario_heat_pump",
        technology_sequence: [
          "heat_pump",
        ],
        base_capex_inr: 2800000,
        base_annual_opex_inr: 500000,
        base_electricity_kwh_year: 95000,
        annual_co2_tonnes: 300,
        feasible: true,
        electricity_dependence: 1,
        reliability_score_pct: 88,
        co2_reduction_pct: 65,
      },
    ]

    setPathways(
      demoPathways
    )

  }, [])


  const canEvaluate =
    pathways.length >= 1


  const updateScenario = (
    key: keyof ScenarioInputs,
    value: number
  ) => {

    setScenario(
      previous => ({
        ...previous,
        [key]: value,
      })
    )
  }


  async function evaluate() {

    if (!canEvaluate) {
      return
    }

    try {

      setIsLoading(true)
      setError(null)

      const response =
        await apiService.evaluateScenario(
          scenario,
          pathways,
          weights
        )

      setResult(response)

    } catch (err: any) {

      console.error(err)

      setError(
        err?.message ??
        "Scenario evaluation failed."
      )

    } finally {

      setIsLoading(false)

    }
  }


  function reset() {

    setScenario(
      DEFAULT_SCENARIO
    )

    setResult(null)
    setError(null)
  }


  const recommended =
    result?.recommendation


  const rankedRows =
    result?.optimizer?.ranked_scenarios ??
    []


  const recommendationColor =
    useMemo(
      () =>
        recommended
          ? "border-emerald-500/30 bg-emerald-500/10"
          : "border-white/10 bg-white/5",
      [recommended]
    )


  return (
    <div className="min-h-screen bg-zinc-950 text-white p-6">

      <div className="mx-auto max-w-7xl space-y-8">

        {/* Header */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">

          <div>

            <div className="flex items-center gap-3">

              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15">

                <Zap className="h-5 w-5 text-emerald-400" />

              </div>

              <h1 className="text-3xl font-bold">
                Digital Twin / Scenario Playground
              </h1>

            </div>

            <p className="mt-2 max-w-3xl text-sm text-zinc-400">
              Change the economic assumptions and instantly
              see which technically feasible pathway becomes
              the best recommendation.
            </p>

          </div>


          <div className="flex gap-2">

            <button
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </button>

            <button
              onClick={evaluate}
              disabled={isLoading || !canEvaluate}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-black disabled:cursor-not-allowed disabled:opacity-50"
            >

              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}

              {isLoading
                ? "Recalculating..."
                : "Run Scenario"}

            </button>

          </div>

        </div>


        {/* Controls */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">

          <ScenarioField
            label="Biomass price"
            suffix="₹/kg"
            value={
              scenario.biomass_price_inr_per_kg
            }
            min={0}
            max={30}
            step={0.1}
            onChange={(value) =>
              updateScenario(
                "biomass_price_inr_per_kg",
                value
              )
            }
          />


          <ScenarioField
            label="Electricity tariff"
            suffix="₹/kWh"
            value={
              scenario.electricity_tariff_inr_per_kwh
            }
            min={0}
            max={30}
            step={0.1}
            onChange={(value) =>
              updateScenario(
                "electricity_tariff_inr_per_kwh",
                value
              )
            }
          />


          <ScenarioField
            label="Subsidy"
            suffix="%"
            value={
              scenario.subsidy_pct
            }
            min={0}
            max={100}
            step={1}
            onChange={(value) =>
              updateScenario(
                "subsidy_pct",
                value
              )
            }
          />


          <ScenarioField
            label="Budget"
            suffix="₹"
            value={
              scenario.budget_inr
            }
            min={0}
            max={50000000}
            step={100000}
            onChange={(value) =>
              updateScenario(
                "budget_inr",
                value
              )
            }
          />


          <ScenarioField
            label="Carbon price"
            suffix="₹/tCO₂"
            value={
              scenario.carbon_price_inr_per_tco2
            }
            min={0}
            max={50000}
            step={500}
            onChange={(value) =>
              updateScenario(
                "carbon_price_inr_per_tco2",
                value
              )
            }
          />

        </div>


        {/* Scenario state */}
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">

          <div className="mb-3 flex items-center justify-between">

            <div>

              <h2 className="font-semibold">
                Active scenario
              </h2>

              <p className="text-xs text-zinc-500">
                Changes are isolated from the baseline
                optimization result.
              </p>

            </div>

            <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
              Live sandbox
            </span>

          </div>


          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">

            <ScenarioValue
              label="Biomass"
              value={`₹${scenario.biomass_price_inr_per_kg.toFixed(2)}/kg`}
            />

            <ScenarioValue
              label="Electricity"
              value={`₹${scenario.electricity_tariff_inr_per_kwh.toFixed(2)}/kWh`}
            />

            <ScenarioValue
              label="Subsidy"
              value={`${scenario.subsidy_pct}%`}
            />

            <ScenarioValue
              label="Budget"
              value={formatINR(scenario.budget_inr)}
            />

            <ScenarioValue
              label="Carbon"
              value={`₹${scenario.carbon_price_inr_per_tco2.toLocaleString("en-IN")}/t`}
            />

          </div>

        </div>


        {/* Errors */}
        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}


        {/* Recommendation */}
        {recommended && (
          <div className={`rounded-2xl border p-6 ${recommendationColor}`}>

            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">

              <div>

                <p className="text-xs uppercase tracking-wide text-emerald-300">
                  Updated recommendation
                </p>

                <h2 className="mt-1 text-2xl font-bold">
                  {recommended.scenario_id}
                </h2>

                <p className="mt-1 text-sm text-zinc-300">
                  {recommended.technology_sequence.join(
                    " → "
                  )}
                </p>

              </div>


              <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-3">

                <p className="text-xs text-zinc-500">
                  Budget status
                </p>

                <p className={`mt-1 text-sm font-semibold ${
                  recommended.within_budget
                    ? "text-emerald-300"
                    : "text-red-300"
                }`}>
                  {recommended.within_budget
                    ? "Within budget"
                    : "Over budget"}
                </p>

              </div>

            </div>


            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

              <MetricCard
                label="Net CAPEX"
                value={formatINR(
                  recommended.net_capex_inr
                )}
              />

              <MetricCard
                label="Annual cost"
                value={formatINR(
                  recommended.annual_total_cost_inr
                )}
              />

              <MetricCard
                label="Energy cost"
                value={formatINR(
                  recommended.annual_energy_cost_inr
                )}
              />

              <MetricCard
                label="Carbon cost"
                value={formatINR(
                  recommended.annual_carbon_cost_inr
                )}
              />

            </div>

          </div>
        )}


        {/* Ranking */}
        {rankedRows.length > 0 && (
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

            <div className="mb-5">

              <h2 className="text-xl font-semibold">
                Scenario ranking
              </h2>

              <p className="text-sm text-zinc-500">
                Ranking after applying the active economic
                scenario to the same feasible pathway set.
              </p>

            </div>


            <div className="overflow-x-auto">

              <table className="w-full text-left text-sm">

                <thead>

                  <tr className="border-b border-white/10 text-zinc-500">

                    <th className="px-3 py-3">
                      Rank
                    </th>

                    <th className="px-3 py-3">
                      Pathway
                    </th>

                    <th className="px-3 py-3">
                      Score
                    </th>

                    <th className="px-3 py-3">
                      Cost
                    </th>

                    <th className="px-3 py-3">
                      Emissions
                    </th>

                    <th className="px-3 py-3">
                      Status
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {rankedRows.map(
                    row => (

                      <tr
                        key={row.scenario_id}
                        className="border-b border-white/5"
                      >

                        <td className="px-3 py-3 font-medium">
                          #{row.rank}
                        </td>

                        <td className="px-3 py-3">

                          <div className="font-medium">
                            {row.scenario_id}
                          </div>

                          <div className="text-xs text-zinc-500">
                            {row.technology_sequence.join(
                              " → "
                            )}
                          </div>

                        </td>

                        <td className="px-3 py-3">
                          {row.composite_score.toFixed(
                            3
                          )}
                        </td>

                        <td className="px-3 py-3">
                          {formatINR(row.raw_cost)}
                        </td>

                        <td className="px-3 py-3">
                          {row.raw_emissions.toFixed(1)}
                        </td>

                        <td className="px-3 py-3">

                          {row.is_recommended ? (
                            <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-xs text-emerald-300">
                              Recommended
                            </span>
                          ) : row.is_cheapest ? (
                            <span className="rounded-full bg-blue-500/10 px-2 py-1 text-xs text-blue-300">
                              Cheapest
                            </span>
                          ) : (
                            <span className="text-xs text-zinc-500">
                              Ranked
                            </span>
                          )}

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          </div>
        )}


        {/* Why it changed */}
        {result?.changes_that_matter && (
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6">

            <h2 className="text-lg font-semibold">
              Why the recommendation changed
            </h2>

            <div className="mt-3 space-y-2">

              {result.changes_that_matter.signals.map(
                signal => (

                  <div
                    key={signal}
                    className="rounded-lg border border-white/5 bg-black/10 px-4 py-3 text-sm text-zinc-300"
                  >
                    {signal}
                  </div>

                )
              )}

            </div>

          </div>
        )}


      </div>

    </div>
  )
}


function ScenarioField({
  label,
  suffix,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string
  suffix: string
  value: number
  min: number
  max: number
  step: number
  onChange: (value: number) => void
}) {

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">

      <div className="flex items-center justify-between">

        <label className="text-sm font-medium text-zinc-200">
          {label}
        </label>

        <span className="text-xs text-zinc-500">
          {suffix}
        </span>

      </div>


      <div className="mt-4">

        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={event =>
            onChange(
              Number(event.target.value)
            )
          }
          className="w-full accent-emerald-400"
        />

      </div>


      <div className="mt-3">

        <input
          type="number"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={event =>
            onChange(
              Math.max(
                min,
                Math.min(
                  max,
                  Number(event.target.value)
                )
              )
            )
          }
          className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500/50"
        />

      </div>

    </div>
  )
}


function ScenarioValue({
  label,
  value,
}: {
  label: string
  value: string
}) {

  return (
    <div className="rounded-lg border border-white/5 bg-black/10 p-3">

      <p className="text-xs text-zinc-500">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold">
        {value}
      </p>

    </div>
  )
}


function MetricCard({
  label,
  value,
}: {
  label: string
  value: string
}) {

  return (
    <div className="rounded-xl border border-white/10 bg-black/10 p-4">

      <p className="text-xs text-zinc-500">
        {label}
      </p>

      <p className="mt-1 text-lg font-semibold text-white">
        {value}
      </p>

    </div>
  )
}