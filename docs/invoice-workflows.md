# PDF invoice workflow

The Invoice Processing page accepts bounded PDF uploads, extracts selectable text
with PyMuPDF, and presents candidate header fields and line items for human review.
The user must confirm the reviewed values before they are saved. The source PDF
and extracted full text are processed in memory and are not persisted by this
workflow; only the filename, page count, confirmed fields and reviewed line items
are stored. Upload only documents you are authorised to process.

## Supported fields

Supplier, invoice number, invoice date, due date, currency, subtotal, tax, total,
and simple line rows with description, quantity, unit price and amount. Extraction
is heuristic because invoice layouts differ. Values are candidates, not verified
facts. Missing fields can be entered manually. Duplicate invoices are checked by
business workspace, supplier and invoice number.

## Limitations

- Selectable-text PDFs only; scanned/image-only PDFs are detected and rejected.
- OCR is intentionally deferred to a later phase.
- Password-protected PDFs are not supported.
- Upload size follows BUSINESSFLOW_MAX_UPLOAD_MB; PDFs are limited to 100 pages.
- Complex tables, multiple currencies, credit notes and locale-specific number/date
  conventions may require manual correction.
- Invoice records are retained in the configured database. Retention, access
  controls and deletion workflows will be expanded in later security work.
- The first configured business workspace is used, matching the current app UI.
