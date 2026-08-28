"use client"
import React, { useState } from "react"
import { FileDown, FileSpreadsheet, FileText, CheckCircle2, Loader2 } from "lucide-react"

interface ReportDownloadProps {
  reportId: string
}

export function ReportDownload({ reportId }: ReportDownloadProps) {
  const [pdfLoading, setPdfLoading] = useState(false)
  const [excelLoading, setExcelLoading] = useState(false)
  const [pdfDone, setPdfDone] = useState(false)
  const [excelDone, setExcelDone] = useState(false)

  // ── PDF: generate client-side using window.print() on a styled div ──────────
  const handlePdfDownload = async () => {
    setPdfLoading(true)
    try {
      // Grab the recommendation from localStorage
      const saved = localStorage.getItem("last_optimization")
      const opt = saved ? JSON.parse(saved) : {}
      const recId = opt.recommended_scenario_id ?? reportId
      const factoryName = opt.factory_name ?? "TN Textile MSME Demo"

      // Fetch full recommendation from backend
      const res = await fetch(`http://localhost:8000/recommendations/${recId}`)
      const data = await res.json()
      const rec = data.recommendation

      // Build a printable HTML page
      const html = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8" />
          <title>Urjiva Report — ${rec?.factory_name ?? factoryName}</title>
          <style>
            body { font-family: sans-serif; padding: 40px; color: #111; }
            h1 { color: #059669; font-size: 24px; margin-bottom: 4px; }
            h2 { font-size: 16px; color: #374151; margin-top: 24px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }
            .meta { color: #6b7280; font-size: 13px; margin-bottom: 24px; }
            .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 16px 0; }
            .kpi { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px; }
            .kpi-label { font-size: 11px; color: #6b7280; text-transform: uppercase; }
            .kpi-value { font-size: 20px; font-weight: bold; color: #065f46; }
            .section { margin-top: 24px; }
            ul { padding-left: 20px; }
            li { margin-bottom: 6px; font-size: 13px; }
            table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
            th { background: #f0fdf4; padding: 8px; text-align: left; border: 1px solid #d1fae5; }
            td { padding: 8px; border: 1px solid #e5e7eb; }
            .badge { background: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 99px; font-size: 11px; font-weight: bold; }
            .disclaimer { font-size: 11px; color: #9ca3af; margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 12px; }
            .brand { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; }
            .brand-dot { width: 12px; height: 12px; background: #059669; border-radius: 50%; }
          </style>
        </head>
        <body>
          <div class="brand"><div class="brand-dot"></div><span style="font-weight:900;font-size:18px;letter-spacing:2px">Urjiva</span><span style="color:#6b7280;font-size:12px">ENERGY PLATFORM</span></div>
          <h1>Clean Energy Transition Report</h1>
          <div class="meta">${rec?.factory_name ?? factoryName} &bull; ${rec?.industry ?? "Textile"} &bull; ${rec?.state ?? "Tamil Nadu"} &bull; Generated ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</div>
          
          <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">CAPEX</div><div class="kpi-value">₹${((rec?.capex_total_inr ?? 12000000) / 100000).toFixed(1)}L</div></div>
            <div class="kpi"><div class="kpi-label">CO₂ Reduction</div><div class="kpi-value">${rec?.co2_reduction_pct ?? 62.5}%</div></div>
            <div class="kpi"><div class="kpi-label">Payback Range</div><div class="kpi-value">${rec?.payback_range_years?.[0] ?? 2.8}–${rec?.payback_range_years?.[1] ?? 4.2} yrs</div></div>
            <div class="kpi"><div class="kpi-label">MCDA Score</div><div class="kpi-value">${((rec?.composite_score ?? 0.847) * 100).toFixed(0)}/100</div></div>
          </div>

          <h2>Recommended Pathway</h2>
          <p style="font-weight:bold;font-size:18px;text-transform:capitalize">${(rec?.recommended_technology_sequence ?? ["Biomass"]).join(" + ").replace(/_/g, " ")}</p>
          <ul>${(rec?.explanation?.why_selected ?? []).map((r: string) => `<li>${r}</li>`).join("")}</ul>

          <h2>Scenario Ranking</h2>
          <table>
            <tr><th>Rank</th><th>Pathway</th><th>MCDA Score</th><th>Note</th></tr>
            <tr><td>1</td><td style="text-transform:capitalize">${(rec?.recommended_technology_sequence ?? ["Biomass"]).join(" + ").replace(/_/g, " ")}</td><td>${((rec?.composite_score ?? 0.847) * 100).toFixed(0)}</td><td><span class="badge">Recommended</span></td></tr>
            ${(rec?.explanation?.why_others_rejected ?? []).map((s: any) => `<tr><td>${s.rank}</td><td style="text-transform:capitalize">${s.technology_sequence.join(" + ").replace(/_/g, " ")}</td><td>${(s.composite_score * 100).toFixed(0)}</td><td>${s.key_weakness}</td></tr>`).join("")}
          </table>

          <h2>Policy & Financing</h2>
          <p>Eligible schemes: <strong>${(rec?.explanation?.policy_benefits?.eligible_schemes ?? []).join(", ") || "None matched"}</strong></p>
          <p>Estimated benefit: <strong>₹${((rec?.explanation?.policy_benefits?.estimated_total_benefit_inr ?? 3200000) / 100000).toFixed(1)} Lakhs</strong></p>

          <h2>Sensitivity Analysis</h2>
          <table>
            <tr><th>Percentile</th><th>Payback (Years)</th></tr>
            <tr><td>P10 (Optimistic)</td><td>${rec?.explanation?.sensitivity_notes?.payback_p10_years ?? 2.1}</td></tr>
            <tr><td>P50 (Median)</td><td>${rec?.explanation?.sensitivity_notes?.payback_p50_years ?? 3.4}</td></tr>
            <tr><td>P90 (Adverse)</td><td>${rec?.explanation?.sensitivity_notes?.payback_p90_years ?? 5.2}</td></tr>
          </table>
          <p style="font-size:13px;margin-top:8px">${rec?.explanation?.sensitivity_notes?.risk_interpretation ?? ""}</p>

          <div class="disclaimer">Generated by Urjiva Energy Platform &bull; Prototype v1.0 &bull; All figures are estimates based on MSME-provided inputs. This report does not constitute financial or legal advice.</div>
        </body>
        </html>
      `

      const win = window.open("", "_blank", "width=900,height=700")
      if (win) {
        win.document.write(html)
        win.document.close()
        win.focus()
        setTimeout(() => { win.print() }, 500)
      }
      setPdfDone(true)
    } catch (e) {
      console.error(e)
    } finally {
      setPdfLoading(false)
    }
  }

  // ── Excel: generate client-side CSV and trigger download ────────────────────
  const handleExcelDownload = async () => {
    setExcelLoading(true)
    try {
      const saved = localStorage.getItem("last_optimization")
      const opt = saved ? JSON.parse(saved) : {}
      const recId = opt.recommended_scenario_id ?? reportId

      const res = await fetch(`http://localhost:8000/recommendations/${recId}`)
      const data = await res.json()
      const rec = data.recommendation

      const rows = [
        ["Urjiva Energy Transition Report"],
        ["Factory", rec?.factory_name ?? ""],
        ["Industry", rec?.industry ?? ""],
        ["State", rec?.state ?? ""],
        ["Generated", new Date().toLocaleDateString()],
        [],
        ["--- KEY METRICS ---"],
        ["CAPEX (INR)", rec?.capex_total_inr ?? ""],
        ["Annual OPEX (INR)", rec?.annual_opex_inr ?? ""],
        ["CO2 Reduction (%)", rec?.co2_reduction_pct ?? ""],
        ["Payback Min (yrs)", rec?.payback_range_years?.[0] ?? ""],
        ["Payback Max (yrs)", rec?.payback_range_years?.[1] ?? ""],
        ["MCDA Composite Score", rec?.composite_score ?? ""],
        [],
        ["--- RECOMMENDED PATHWAY ---"],
        ["Technology", (rec?.recommended_technology_sequence ?? []).join(" + ").replace(/_/g, " ")],
        [],
        ["--- SCENARIO RANKING ---"],
        ["Rank", "Pathway", "MCDA Score", "Key Weakness"],
        ["1", (rec?.recommended_technology_sequence ?? []).join(" + ").replace(/_/g, " "), ((rec?.composite_score ?? 0) * 100).toFixed(0), "Recommended"],
        ...(rec?.explanation?.why_others_rejected ?? []).map((s: any) => [
          s.rank,
          s.technology_sequence.join(" + ").replace(/_/g, " "),
          (s.composite_score * 100).toFixed(0),
          s.key_weakness
        ]),
        [],
        ["--- POLICY SCHEMES ---"],
        ["Eligible Schemes", (rec?.explanation?.policy_benefits?.eligible_schemes ?? []).join("; ")],
        ["Estimated Benefit (INR)", rec?.explanation?.policy_benefits?.estimated_total_benefit_inr ?? ""],
        [],
        ["--- SENSITIVITY ANALYSIS ---"],
        ["P10 Payback (yrs)", rec?.explanation?.sensitivity_notes?.payback_p10_years ?? ""],
        ["P50 Payback (yrs)", rec?.explanation?.sensitivity_notes?.payback_p50_years ?? ""],
        ["P90 Payback (yrs)", rec?.explanation?.sensitivity_notes?.payback_p90_years ?? ""],
        ["Spread Ratio", rec?.explanation?.sensitivity_notes?.spread_ratio ?? ""],
      ]

      const csv = rows.map(r => r.map((cell: any) => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n")
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `cieto-report-${recId}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      setExcelDone(true)
    } catch (e) {
      console.error(e)
    } finally {
      setExcelLoading(false)
    }
  }

  const btn = (
    onClick: () => void,
    loading: boolean,
    done: boolean,
    label: string,
    subLabel: string,
    icon: React.ReactNode,
    doneIcon: React.ReactNode,
    id: string
  ) => (
    <button
      id={id}
      onClick={onClick}
      disabled={loading}
      className="group relative flex items-center gap-4 w-full rounded-2xl border border-zinc-700 bg-zinc-800/60 hover:bg-zinc-700/60 hover:border-emerald-500/40 px-6 py-5 text-left transition-all duration-200 disabled:opacity-60"
    >
      <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-colors ${done ? "bg-emerald-500/20" : "bg-zinc-700 group-hover:bg-emerald-500/10"}`}>
        {loading ? <Loader2 className="h-6 w-6 animate-spin text-zinc-400" /> : done ? doneIcon : icon}
      </div>
      <div className="flex-1">
        <p className="font-semibold text-white">{label}</p>
        <p className="text-sm text-zinc-400 mt-0.5">
          {loading ? "Generating…" : done ? "Done — click again to regenerate" : subLabel}
        </p>
      </div>
      {!loading && <FileDown className="h-5 w-5 text-zinc-500 group-hover:text-emerald-400 transition-colors shrink-0" />}
    </button>
  )

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {btn(
        handlePdfDownload, pdfLoading, pdfDone,
        "PDF Report",
        "Full report with analysis — opens print dialog",
        <FileText className="h-6 w-6 text-red-400" />,
        <CheckCircle2 className="h-6 w-6 text-emerald-400" />,
        "download-pdf-btn"
      )}
      {btn(
        handleExcelDownload, excelLoading, excelDone,
        "Excel / CSV Report",
        "Scenario data & figures — downloads as .csv",
        <FileSpreadsheet className="h-6 w-6 text-emerald-400" />,
        <CheckCircle2 className="h-6 w-6 text-emerald-400" />,
        "download-excel-btn"
      )}
    </div>
  )
}
