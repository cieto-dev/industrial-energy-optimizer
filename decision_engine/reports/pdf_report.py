"""
pdf_report.py — PDF report generation (Sprint 3.4).

Purpose
-------
Generate a human-readable PDF report from a Recommendation object.

Key Requirements
----------------
- All numbers must have plain-language explanations
- estimated_total_benefit_inr must show total_benefit_verified status and disclaimer
- Disclaimer must be visible in the actual PDF document (footnote or warning box)
- No raw JSON dumps or unexplained jargon
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from datetime import datetime

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors

from models.recommendation import Recommendation


class PDFReportGenerator:
    """Generate PDF reports from Recommendation objects."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.darkblue,
                spaceAfter=20,
                alignment=TA_CENTER,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.darkblue,
                spaceAfter=12,
                spaceBefore=20,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Disclaimer",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.red,
                fontStyle="Italic",
                spaceBefore=10,
                spaceAfter=10,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CustomBodyText",
                parent=self.styles["Normal"],
                fontSize=11,
                spaceAfter=8,
                leading=14,
            )
        )

    def _format_currency(self, value: float) -> str:
        """Format currency value in INR with plain language."""
        if value >= 1_00_00_000:  # 1 crore
            crores = value / 1_00_00_000
            return f"₹{crores:.2f} crore (₹{value:,.0f})"
        elif value >= 1_00_000:  # 1 lakh
            lakhs = value / 1_00_000
            return f"₹{lakhs:.2f} lakh (₹{value:,.0f})"
        else:
            return f"₹{value:,.0f}"

    def _format_percentage(self, value: float) -> str:
        """Format percentage with plain language."""
        return f"{value:.1f}%"

    def _format_years(self, value: float) -> str:
        """Format years with plain language."""
        if value < 1:
            months = value * 12
            return f"{months:.0f} months ({value:.2f} years)"
        return f"{value:.1f} years"

    def generate(self, recommendation: Recommendation) -> Path:
        """
        Generate a PDF report from the Recommendation.

        Parameters
        ----------
        recommendation : Recommendation
            The recommendation object to convert to PDF

        Returns
        -------
        Path
            Path to the generated PDF file
        """
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []
        story.extend(self._build_title_section(recommendation))
        story.extend(self._build_summary_section(recommendation))
        story.extend(self._build_recommendation_section(recommendation))
        story.extend(self._build_economic_section(recommendation))
        story.extend(self._build_environmental_section(recommendation))
        story.extend(self._build_policy_section(recommendation))
        story.extend(self._build_sensitivity_section(recommendation))
        story.extend(self._build_alternatives_section(recommendation))
        story.extend(self._build_disclaimer_section(recommendation))

        doc.build(story)
        return self.output_path

    def _build_title_section(self, recommendation: Recommendation) -> list:
        """Build the title section of the report."""
        story = []

        title = Paragraph(
            f"Industrial Energy Transition Recommendation<br/>"
            f"{recommendation.factory_name}",
            self.styles["CustomTitle"],
        )
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))

        subtitle = Paragraph(
            f"Industry: {recommendation.industry} | State: {recommendation.state} | "
            f"Generated: {recommendation.generated_at.strftime('%Y-%m-%d %H:%M')}",
            self.styles["CustomBodyText"],
        )
        story.append(subtitle)
        story.append(Spacer(1, 0.3 * inch))

        return story

    def _build_summary_section(self, recommendation: Recommendation) -> list:
        """Build the executive summary section."""
        story = []

        heading = Paragraph("Executive Summary", self.styles["CustomHeading"])
        story.append(heading)

        # Technology sequence
        tech_text = (
            f"<b>Recommended Pathway:</b> {' → '.join(recommendation.recommended_technology_sequence)}"
        )
        story.append(Paragraph(tech_text, self.styles["CustomBodyText"]))
        story.append(Spacer(1, 0.1 * inch))

        # MCDA summary
        mcda_text = (
            f"<b>Overall Score:</b> {recommendation.composite_score:.2f} out of 1.0 "
            f"(Cost: {recommendation.objective_scores['cost']:.2f}, "
            f"Emissions: {recommendation.objective_scores['emissions']:.2f}, "
            f"Risk: {recommendation.objective_scores['risk']:.2f})"
        )
        story.append(Paragraph(mcda_text, self.styles["CustomBodyText"]))
        story.append(Spacer(1, 0.1 * inch))

        # Cost ranking note
        if recommendation.recommended_is_cheapest:
            cost_note = (
                "<b>Note:</b> This recommendation is also the most cost-effective option."
            )
        else:
            cost_note = (
                "<b>Note:</b> This recommendation prioritizes environmental benefits "
                "and risk reduction over lowest cost."
            )
        story.append(Paragraph(cost_note, self.styles["CustomBodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        return story

    def _build_recommendation_section(self, recommendation: Recommendation) -> list:
        """Build the detailed recommendation reasoning section."""
        story = []

        heading = Paragraph("Why This Pathway Was Recommended", self.styles["CustomHeading"])
        story.append(heading)

        for reason in recommendation.explanation.why_selected:
            story.append(Paragraph(f"• {reason}", self.styles["CustomBodyText"]))

        story.append(Spacer(1, 0.2 * inch))
        return story

    def _build_economic_section(self, recommendation: Recommendation) -> list:
        """Build the economic analysis section."""
        story = []

        heading = Paragraph("Economic Analysis", self.styles["CustomHeading"])
        story.append(heading)

        # Economic summary table
        data = [
            [
                "<b>Capital Expenditure (CAPEX)</b>",
                self._format_currency(recommendation.capex_total_inr),
            ],
            [
                "<b>Annual Operating Expenditure (OPEX)</b>",
                self._format_currency(recommendation.annual_opex_inr),
            ],
            [
                "<b>Payback Period</b>",
                f"{self._format_years(recommendation.payback_range_years[0])} to "
                f"{self._format_years(recommendation.payback_range_years[1])}",
            ],
        ]

        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Economic explanation
        economic_note = (
            f"<b>Investment Required:</b> {self._format_currency(recommendation.capex_total_inr)} "
            f"upfront, with annual operating costs of {self._format_currency(recommendation.annual_opex_inr)}. "
            f"The investment is recovered through energy savings over "
            f"{self._format_years(recommendation.payback_range_years[0])} to "
            f"{self._format_years(recommendation.payback_range_years[1])}."
        )
        story.append(Paragraph(economic_note, self.styles["CustomBodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        return story

    def _build_environmental_section(self, recommendation: Recommendation) -> list:
        """Build the environmental impact section."""
        story = []

        heading = Paragraph("Environmental Impact", self.styles["CustomHeading"])
        story.append(heading)

        # Environmental summary table
        data = [
            [
                "<b>CO₂ Emissions Reduction</b>",
                self._format_percentage(recommendation.co2_reduction_pct),
            ],
            [
                "<b>Fossil Fuel Reduction</b>",
                self._format_percentage(recommendation.fossil_fuel_reduction_pct),
            ],
        ]

        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgreen),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Environmental explanation
        env_note = (
            f"<b>Climate Benefit:</b> This pathway reduces CO₂ emissions by "
            f"{self._format_percentage(recommendation.co2_reduction_pct)} "
            f"and fossil fuel consumption by {self._format_percentage(recommendation.fossil_fuel_reduction_pct)}, "
            f"contributing to climate compliance and sustainability goals."
        )
        story.append(Paragraph(env_note, self.styles["CustomBodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        return story

    def _build_policy_section(self, recommendation: Recommendation) -> list:
        """Build the policy and financing section with disclaimer."""
        story = []

        heading = Paragraph("Government Financing & Policy Support", self.styles["CustomHeading"])
        story.append(heading)

        policy = recommendation.explanation.policy_benefits

        # Policy summary
        if policy.eligible_schemes:
            schemes_text = f"<b>Eligible Schemes ({len(policy.eligible_schemes)}):</b> {', '.join(policy.eligible_schemes[:5])}"
            if len(policy.eligible_schemes) > 5:
                schemes_text += f" and {len(policy.eligible_schemes) - 5} others"
            story.append(Paragraph(schemes_text, self.styles["CustomBodyText"]))
            story.append(Spacer(1, 0.1 * inch))

            # Total benefit with verification status
            benefit_text = (
                f"<b>Estimated Total Benefit:</b> {self._format_currency(policy.estimated_total_benefit_inr)} "
                f"({'Verified' if policy.total_benefit_verified else 'Unverified'})"
            )
            story.append(Paragraph(benefit_text, self.styles["CustomBodyText"]))
            story.append(Spacer(1, 0.1 * inch))

            # Disclaimer - prominently displayed as warning box
            if not policy.total_benefit_verified and policy.disclaimer:
                disclaimer_box = Paragraph(
                    f"<b>IMPORTANT:</b> {policy.disclaimer}",
                    self.styles["Disclaimer"],
                )
                story.append(disclaimer_box)
                story.append(Spacer(1, 0.2 * inch))
        else:
            story.append(
                Paragraph(
                    "<b>No eligible government schemes identified for this scenario.</b>",
                    self.styles["CustomBodyText"],
                )
            )
            story.append(Spacer(1, 0.2 * inch))

        return story

    def _build_sensitivity_section(self, recommendation: Recommendation) -> list:
        """Build the sensitivity analysis section."""
        story = []

        heading = Paragraph("Risk & Sensitivity Analysis", self.styles["CustomHeading"])
        story.append(heading)

        sensitivity = recommendation.explanation.sensitivity_notes

        # Payback range table
        data = [
            ["<b>Optimistic (P10)</b>", f"{self._format_years(sensitivity.payback_p10_years)}"],
            ["<b>Expected (P50)</b>", f"{self._format_years(sensitivity.payback_p50_years)}"],
            ["<b>Conservative (P90)</b>", f"{self._format_years(sensitivity.payback_p90_years)}"],
            ["<b>Uncertainty Spread</b>", f"{sensitivity.spread_ratio:.2f}"],
        ]

        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightyellow),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
        )
        story.append(table)
        story.append(Spacer(1, 0.1 * inch))

        # Risk interpretation
        story.append(Paragraph(f"<b>Risk Assessment:</b> {sensitivity.risk_interpretation}", self.styles["CustomBodyText"]))
        story.append(Spacer(1, 0.1 * inch))

        # Top risk factors
        if sensitivity.top_risk_factors:
            factors_text = "<b>Key Risk Factors:</b> " + ", ".join(sensitivity.top_risk_factors)
            story.append(Paragraph(factors_text, self.styles["CustomBodyText"]))

        story.append(Spacer(1, 0.2 * inch))
        return story

    def _build_alternatives_section(self, recommendation: Recommendation) -> list:
        """Build the alternatives analysis section."""
        story = []

        heading = Paragraph("Why Other Options Were Not Recommended", self.styles["CustomHeading"])
        story.append(heading)

        for rejected in recommendation.explanation.why_others_rejected:
            tech_sequence = " → ".join(rejected.technology_sequence)
            alternative_text = (
                f"<b>{tech_sequence}</b> (Rank #{rejected.rank}, Score: {rejected.composite_score:.2f}): "
                f"{rejected.reason}. Key weakness: {rejected.key_weakness}."
            )
            story.append(Paragraph(alternative_text, self.styles["CustomBodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        story.append(Spacer(1, 0.2 * inch))
        return story

    def _build_disclaimer_section(self, recommendation: Recommendation) -> list:
        """Build the final disclaimer section."""
        story = []

        # Final disclaimer box
        disclaimer_text = (
            "<b>Report Disclaimer:</b> This recommendation is based on the available data "
            "and assumptions documented in the knowledge base. Actual results may vary "
            "based on site-specific conditions, market fluctuations, and policy changes. "
            "Consult with qualified engineers and financial advisors before making "
            "investment decisions."
        )

        disclaimer = Paragraph(disclaimer_text, self.styles["Disclaimer"])
        story.append(disclaimer)
        story.append(Spacer(1, 0.1 * inch))

        return story


def generate_pdf_report(
    recommendation: Recommendation,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate a PDF report from a Recommendation object.

    Parameters
    ----------
    recommendation : Recommendation
        The recommendation object to convert to PDF
    output_path : Path, optional
        Path for the output PDF file. If None, uses a default name.

    Returns
    -------
    Path
        Path to the generated PDF file
    """
    if output_path is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = Path(
            f"recommendation_{recommendation.factory_id}_{timestamp}.pdf"
        )

    generator = PDFReportGenerator(output_path)
    return generator.generate(recommendation)