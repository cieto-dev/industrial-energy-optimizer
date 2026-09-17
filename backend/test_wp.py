from weasyprint import HTML
HTML(string="<h1>Test</h1>").write_pdf("test.pdf")
print("WeasyPrint works")
