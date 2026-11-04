# BusinessFlow Automation Suite — Fiverr Portfolio Notes

## Project summary

BusinessFlow Automation Suite is a Python and Streamlit application demonstrating
practical automation workflows for small-business operations. It brings
spreadsheet processing, invoice review, order tracking, inventory control,
reporting and processing history into one local workspace.

## Capabilities demonstrated

- CSV/XLSX cleaning, validation, duplicate detection, consolidation and export.
- Selectable-text PDF invoice extraction with human review before saving.
- Customer order creation, editing and controlled status transitions.
- Product catalogue, stock movement ledger and physical stocktake reconciliation.
- Database-backed dashboard with monthly order-value trends, currency-specific order values, fulfilment rate, supplier invoice liabilities, overdue invoice alerts and reorder attention.
- Downloadable reports and processing history.
- Separate fictional Demo workspace for safe product walkthroughs.

## Suggested demonstration sequence

1. Open the Demo workspace from the sidebar.
2. Review the dashboard and note that its figures come from the demo database.
3. Open Data Workbench and upload a small CSV/XLSX file to clean or combine.
4. Open Invoice Processing and extract a selectable-text PDF; review fields before confirmation.
5. Open Orders to inspect the example order and demonstrate status management.
6. Open Inventory to review the sample catalogue, stock warning and movement ledger.
7. Open Reports & Exports and download a report.
8. Open Processing History to inspect recorded workflow activity.

Use only files prepared for demonstration. Never upload client-confidential
documents or personal data into a public portfolio recording.

## Suggested Fiverr positioning

**Headline:** Python business workflow automation with Excel, PDF and inventory tools

**Short description:** I build practical Python automations that reduce repetitive
business work. This project demonstrates spreadsheet cleaning and consolidation,
PDF invoice extraction with human review, order workflows, inventory tracking
and downloadable reports.

## Technical stack

Python 3.11+, Streamlit, Pandas, SQLAlchemy, SQLite, Plotly, OpenPyXL,
PyMuPDF and Pytest.

## Honest scope and limitations

- Invoice extraction currently reads selectable PDF text; scanned PDFs and OCR
  are not supported.
- Spreadsheet validation is generic; client-specific business rules need to be
  agreed and configured for each engagement.
- External API integrations are not included in this demonstration.
- Authentication and role-based access are not implemented.
- The demo dataset is fictional and is not evidence of client outcomes,
  savings, or production deployment.

## Screenshot checklist

Capture screenshots from the running application, not from concept mockups:

- Business overview in Demo workspace.
- Data Workbench with a clearly fictional sample file loaded and results visible.
- Invoice review screen with a purpose-made fictional selectable-text PDF.
- Orders and inventory pages showing the demo records.
- Reports export and processing history.

Add a visible "Demo workspace — fictional data" label to any screenshot that
contains seeded example records.

## Visual capture guidance

Use the Business overview in Demo workspace as the primary portfolio image.
The dashboard calculates these indicators from saved workspace records. The Demo workspace uses fictional, versioned sample records; the Live workspace reads the selected business database. Order value is not collected revenue because payment tracking is not currently implemented.

Capture the running application at a desktop viewport (ideally 16:9, around
1440 × 900 pixels) with the sidebar visible, browser zoom at 100%, and no
developer tools, notifications or personal browser information in view. Keep
the workspace selector and fictional-demo notice visible where practical.
Capture the Data Workbench, invoice review, inventory and report pages as
supporting images. Use consistent viewport dimensions and avoid cropping
tables, warnings or confirmation controls in a way that changes their meaning.
Only use genuine application screenshots and fictional demonstration records;
do not use generated mockups or imply that screenshots show customer data.
