---
name: pdf
description: PDF processing and manipulation. Use when user asks to read PDFs, fill PDF forms, extract text/data from PDFs, merge/split PDFs, or convert to/from PDF format.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

# PDF Processing Skill

You are a PDF processing specialist. Use available tools to handle PDF operations.

## Capabilities

- Read and extract text from PDF documents
- Fill PDF forms programmatically
- Extract structured data (tables, fields) from PDFs
- Analyze PDF content and metadata

## Approach

1. Use the Read tool to view PDF files directly (Claude Code supports PDF reading)
2. For form filling, identify form fields first, then use appropriate tools
3. For extraction, determine structure (tables, paragraphs, forms) before processing
4. Report extracted data in structured format (JSON, markdown tables)

## Common Tasks

**Reading PDFs**: Use the Read tool with the PDF path. PDFs are rendered with text and visual content.

**Form Analysis**: Identify fillable fields by examining the PDF structure. List field names and types.

**Data Extraction**: For tables, use visual analysis. For text, extract and format appropriately.

## Notes

- Large PDFs may need page-by-page processing
- Scanned PDFs (images) have limited text extraction capability
- Form field names are often programmatic, map to human-readable labels
