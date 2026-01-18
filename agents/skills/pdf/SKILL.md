---
name: pdf
description: PDF processing and manipulation. Use when user asks to read PDFs, fill PDF forms, extract text/data from PDFs, merge/split PDFs, or convert to/from PDF format.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<capabilities>
Read and extract text from PDF documents, fill PDF forms programmatically, extract structured data (tables, fields), analyze content and metadata.
</capabilities>

<approach>
Use Read tool to view PDFs directly (Claude Code supports PDF reading). For form filling: identify fields first, then use appropriate tools. For extraction: determine structure (tables, paragraphs, forms) before processing. Report extracted data in structured format (JSON, markdown tables).
</approach>

<tasks>
Reading: Use Read tool with PDF path. PDFs render with text and visual content.
Form analysis: Identify fillable fields by examining structure. List field names and types.
Data extraction: For tables use visual analysis. For text extract and format appropriately.
</tasks>

<notes>
Large PDFs may need page-by-page processing. Scanned PDFs (images) have limited text extraction. Form field names are often programmatic - map to human-readable labels.
</notes>
