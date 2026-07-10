# UrbanRoof AI DDR Generator

>Developed an AI-powered Detailed Diagnosis Report (DDR) Generator inspired by UrbanRoof's reporting workflow.
>The system parses inspection and thermal PDFs, extracts observations and evidence images, semantically links related findings using sentence embeddings,
>applies LLM-based reasoning to determine root causes, severity, and recommended repairs, and automatically generates a comprehensive, professionally formatted DDR with associated visual evidence.

---

## Overview

The UrbanRoof AI DDR Generator automates the process of creating engineering inspection reports by combining information from:

* Inspection Reports (Visual Inspection)
* Thermal Reports (Infrared Analysis)

The system extracts observations, associates evidence images, semantically matches related findings, enriches them using an LLM, and produces a structured Microsoft Word DDR report.

---

## Features

* Automatic PDF Parsing
* Evidence Image Association
* Property Area Detection
* Observation Extraction
* Semantic Matching between Inspection & Thermal Reports
* AI-based Reasoning using LLM
* Knowledge Base Generation
* Professional DDR Report Generation
* Simple Streamlit UI
* Download Generated Reports and JSON Files

---

# Project Workflow

```
Inspection PDF
        │
        ▼
PDF Parser
        │
        ▼
Inspection Observations
        │

Thermal PDF
        │
        ▼
PDF Parser
        │
        ▼
Thermal Observations
        │
        ▼
Knowledge Base
        │
        ▼
Semantic Matcher
        │
        ▼
LLM Reasoner
        │
        ▼
DDR Report Generator
        │
        ▼
Final DDR Report (.docx)
```

---

# Project Structure

```
UrbanRoof-AI-DDR/

│
├── app.py
├── ui.py
├── config.py
├── requirements.txt
│
├── data/
│   ├── inspection.pdf
│   └── thermal.pdf
│
├── extracted/
│   ├── inspection.json
│   ├── thermal.json
│   ├── inspection_photos/
│   └── thermal/
│
├── output/
│   └── DDR_Report.docx
│
├── modules/
│   ├── pdf_parser.py
│   ├── knowledge_base.py
│   ├── semantic_matcher.py
│   ├── llm_reasoner.py
│   ├── report_generator.py
│   └── prompt.py
│
└── README.md
```

---

## Technologies Used

- Python 3.11+
- PyMuPDF (fitz)
- SentenceTransformers
- FAISS
- Streamlit (optional UI)
- python-docx
- NumPy
- Groq (LLM API)

---

# Installation

Prerequisites:

- Python 3.11 or later
- pip

Clone the repository

```bash
git clone https://github.com/yourusername/UrbanRoof-AI-DDR.git
cd UrbanRoof-AI-DDR
```

Install dependencies (recommended using the current Python interpreter)

```bash
python -m pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file (or set environment variables) for any API keys required
by the project. Example:

```env
GROQ_API_KEY=your_api_key_here
```

Also verify any values in `config.py` (paths, output folders) before running.

---

# Running from Terminal

Place the following files inside the **data** folder.

```
inspection.pdf

thermal.pdf
```

Run

```bash
python app.py
```

The generated files will be available in:

```
output/
```

---

# Running the Streamlit UI

Start the application

```bash
streamlit run ui.py
```

---

# Using the UI

1. Upload the Inspection PDF.
2. Upload the Thermal PDF.
3. Click **Generate DDR**.
4. Wait for the processing to complete.
5. Download:

   * DDR Report
   * Inspection JSON
   * Thermal JSON
   * Knowledge Base JSON

---

# Processing Pipeline

## 1. PDF Parsing

* Extract text blocks
* Detect report sections
* Identify property areas
* Extract observations
* Associate evidence images

---

## 2. Knowledge Base

Creates structured Observation objects containing:

* Source
* Area
* Issue
* Description
* Evidence
* Page Number
* Images
* Confidence

---

## 3. Semantic Matching

Uses sentence embeddings to match:

```
Inspection Observation
           ⇅
Thermal Observation
```

based on semantic similarity.

---

## 4. AI Reasoning

The LLM analyzes matched observations and generates:

* Severity
* Root Cause
* Recommendations
* Executive Summary

---

## 5. DDR Generation

Produces a professional Microsoft Word report including:

* Cover Page
* Executive Summary
* Property Summary
* Area-wise Findings
* Thermal Findings
* Severity Assessment
* Recommendations
* Associated Evidence Images

---

# Outputs

```
inspection.json

thermal.json

knowledge_base.json

DDR_Report.docx
```

---

# Example Workflow

```
Upload PDFs

        │

        ▼

Parse PDFs

        │

        ▼

Extract Observations

        │

        ▼

Build Knowledge Base

        │

        ▼

Semantic Matching

        │

        ▼

LLM Reasoning

        │

        ▼

Generate DDR

        │

        ▼

Download Report
```

---

# Future Improvements

* Multi-property batch processing
* Interactive dashboard
* Confidence visualization
* Automatic image-caption generation
* Cloud deployment
* OCR support for scanned PDFs
* Export to PDF and HTML
* Advanced filtering and search

---

# Author

**Adithya Ashok Sapalya**

Bachelor of Engineering in Artificial Intelligence & Machine Learning

Project developed as part of the **UrbanRoof AI/ML Assessment**.

---

# License

This project is intended for educational and assessment purposes. All rights belong to their respective owners where applicable.
