# Report Generation Implementation Plan

When the environment is ready (i.e., `brew install pango cairo` or `apt-get install libpango-1.0-0 libcairo2` added to `Dockerfile`), a developer can execute this exact plan for PDF/Excel generation without guessing.

## 1. Required Libraries
- Run: `pip install weasyprint jinja2 openpyxl`
- Add these to `backend/requirements.txt`
- Update `backend/Dockerfile` to install OS-level dependencies: `libpango-1.0-0`, `libcairo2`, `libgdk-pixbuf2.0-0`, and `shared-mime-info`.

## 2. Files to Create

**`backend/services/pdf_service.py`**:
```python
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

def generate_pdf(optimize_response_dict: dict) -> bytes:
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")
    html_out = template.render(data=optimize_response_dict)
    return HTML(string=html_out).write_pdf()
```

**`backend/services/excel_service.py`**:
- Use `openpyxl.Workbook()`. Create sheets: `Executive_Summary`, `Baseline_and_Gaps`, and `Scenario_Comparison`.
- For financial mapping, explicitly write logic: `if val is None: cell.value = "Vendor Quote Required"`.

**`backend/templates/report_template.html`**:
- A clean Jinja2 template structured similarly to the frontend.
- Must include the text: *"System Disclaimer: Financial projections for some technologies have been blocked (Vendor Quote Required) as per the No-Invention Rule."*

## 3. Files to Edit

**`backend/apis/report_api.py`**:
```python
from fastapi.responses import Response
from services.pdf_service import generate_pdf
from services.excel_service import generate_excel

@router.get("/{id}/pdf")
def get_report_pdf(id: str, current_user: str = Depends(get_current_user)):
    # 1. Fetch raw OptimizeResponse from DB using id
    data = db.get_optimization_result(id)
    # 2. Generate bytes
    pdf_bytes = generate_pdf(data)
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=urjiva_report_{id}.pdf"}
    )
```
*(Replicate endpoint signature for `/{id}/excel` using `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)*

## 4. Frontend Data Mapping & Wiring

**`frontend/app/reports/page.tsx`**:
- Remove the disabled state from the PDF and Excel buttons.
- Wire the buttons to use native anchor downloads pointing directly to the backend authenticated endpoints: 
  `<a href={`${process.env.NEXT_PUBLIC_API_URL}/reports/${result.id}/pdf`} download>`
