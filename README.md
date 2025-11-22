# 🧠 UCA-NIYAMR-AI-Agent  
### Automated Legal PDF → Structured Summary → Compliance Report  

This project provides an end-to-end AI pipeline that extracts structured text from a legal PDF, summarises it intelligently using OpenAI models, and performs rule-based compliance checks. The entire system runs inside Docker for consistency, ease of execution, and zero dependency issues.

---

# 📂 Project Structure

```
NIYAMR-AI-Agent/
│
├── data/
│   └── ukpga_20250022_en.pdf
│
├── outputs/
│   ├── extracted_sections.json
│   ├── summary.json
│   └── report.json
│
├── src/
│   ├── extract_text.py
│   ├── summarize_act.py
│   └── extract_sections_and_rules.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 🚀 Features

### ✅ PDF Extraction
- Uses `pdfplumber`  
- Cleans and segments text into logical sections  
- Saves clean structured JSON: `outputs/extracted_sections.json`

### ✅ AI Summarisation (OpenAI)
- Uses `gpt-4o-mini` or any model via `OPENAI_API_KEY`  
- Produces a structured summary including:  
  - Purpose  
  - Definitions  
  - Eligibility  
  - Obligations  
  - Enforcement (if present)  
- Handles long PDFs using chunk-based summarisation  
- Output: `outputs/summary.json`

### ✅ Rule-Based Compliance Checker
Analyzes whether the Act contains:
- Key term definitions  
- Eligibility conditions  
- Government responsibilities  
- Payment calculation structure  
- Enforcement / penalties  
- Record-keeping or reporting duties  

Outputs `pass`/`fail` + evidence + confidence score.  
Result saved to: `outputs/report.json`

### ✅ Fully Dockerized
- Zero host dependency issues  
- Same behavior across all machines  
- Easy to run, clean to grade

---

# ⚙️ Setup

## 1️⃣ Clone Repo
```bash
git clone https://github.com/<your-username>/NIYAMR-AI-Agent.git
cd NIYAMR-AI-Agent
```

## 2️⃣ Add `.env` File
```
OPENAI_API_KEY=sk-your-key
```

## 3️⃣ Build Docker Image
```bash
docker compose build --no-cache
```

---

# 🏃 Running the Pipeline

## Step 1 — Extract Sections
```bash
docker compose run --rm app python src/extract_text.py
```

## Step 2 — Summarise Act
```bash
docker compose run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY app python src/summarize_act.py
```

## Step 3 — Rule Check
```bash
docker compose run --rm app python src/extract_sections_and_rules.py
```

---

# 🎯 Recommended — Full Pipeline in One Command
```bash
docker compose run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY \
    --user "$(id -u):$(id -g)" app bash -lc \
    "python src/extract_text.py && python src/summarize_act.py && python src/extract_sections_and_rules.py"
```

---

# 📦 Output Files (Final Deliverables)

| File | Description |
|------|-------------|
| `extracted_sections.json` | Clean, structured extraction of Act text |
| `summary.json` | AI-generated labelled summary |
| `report.json` | Rule-based compliance assessment |

---

# 🛠 Troubleshooting

### ❌ 401 Authentication Error  
Cause: Container cannot see the API key.  
Fix:
```bash
export OPENAI_API_KEY=$(sed -n 's/^OPENAI_API_KEY=//p' .env)
```
Then run with `-e OPENAI_API_KEY=$OPENAI_API_KEY`.

### ❌ PDF Not Found  
Place PDF here:
```
data/ukpga_20250022_en.pdf
```

### ❌ Permission Errors  
Fix output permissions:
```bash
sudo chown -R $(id -u):$(id -g) outputs
```

### ❌ Deleted extracted_sections.json  
Regenerate it:
```bash
docker compose run --rm app python src/extract_text.py
```

### ❌ jq Not Found  
Install on host:
```bash
sudo apt install jq
```

---


# 🎉 Finally

The NIYAMR-AI-Agent gives a clean, reproducible, automated pipeline for legal document analysis:
- Robust extraction  
- High-quality summarisation  
- Clear compliance assessment  

Ready for grading, or future extensions.




