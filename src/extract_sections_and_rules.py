# src/extract_sections_and_rules.py
"""
Improved extractor and rule-checker for NIYAMR-AI-Agent.

Reads:
  - outputs/extracted_sections.json

Writes:
  - outputs/report.json         (concise rule_checks + provenance)
  - outputs/report_debug.json   (detailed per-field examples & sections for debugging)

Behavior:
  - searches each section for extended keywords
  - attaches section title + contextual snippet for evidence
  - converts presence/absence to pass/fail for the six assignment rules
"""
import json
import re
from pathlib import Path

SECTIONS_FILE = Path("outputs/extracted_sections.json")
OUT_REPORT = Path("outputs/report.json")
OUT_DEBUG = Path("outputs/report_debug.json")

# Extended keywords per field (aggressive list)
keywords = {
    "definitions": ["definition", "interpretation", "means", "defined", "definition:"],
    "eligibility": ["entitled", "eligible", "eligibility", "claimant", "entitlement", "entitlements"],
    "obligations": ["obligation", "duty", "must", "required to", "shall", "required"],
    "responsibilities": ["Secretary of State", "Department", "responsible for", "administer", "administrator", "authority"],
    "payments": ["amount", "allowance", "LCWRA", "standard allowance", "£", "amounts", "element"],
    "penalties": ["penalty", "penalties", "offence", "offences", "sanction", "fine", "liable", "enforce", "enforcement", "criminal", "punish"],
    "record_keeping": ["record", "report", "reporting", "keep a record", "retain", "returns", "register", "accounts", "audit", "retention", "submit"]
}

def find_contexts_in_section(text, kw):
    """
    Return list of context snippets for occurrences of kw in text.
    Each snippet is up to ~400 chars centered on the match (bounded).
    """
    res = []
    for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 200)
        snippet = text[start:end].replace("\n", " ").strip()
        res.append(snippet)
    return res

def find_evidence_all_sections(sections, kw_list, max_examples=2):
    """
    For a list of keywords, search all sections.
    Return a list of matches: {section_title, keyword, contexts:[...]}
    """
    found = []
    for s in sections:
        t = s.get('text', '') or ''
        for kw in kw_list:
            contexts = find_contexts_in_section(t, kw)
            if contexts:
                found.append({
                    "section_title": s.get('title', '')[:200],
                    "keyword": kw,
                    "contexts": contexts[:max_examples]
                })
    return found

def main():
    if not SECTIONS_FILE.exists():
        raise SystemExit(f"Missing input file: {SECTIONS_FILE}. Run extractor first.")

    data = json.loads(SECTIONS_FILE.read_text(encoding="utf-8"))
    sections = data.get('sections', [])

    report_fields = {}
    debug = {}

    # Search each keyword group and record results
    for field, kw_list in keywords.items():
        hits = find_evidence_all_sections(sections, kw_list, max_examples=3)
        if hits:
            report_fields[field] = {
                "status": "present",
                "num_hits": len(hits),
                "examples": hits[:5]
            }
        else:
            report_fields[field] = {
                "status": "missing",
                "num_hits": 0,
                "examples": []
            }
        debug[field] = report_fields[field]

    # Now build rule checks expected by the assignment (6 rules)
    rule_texts = [
        ("Act must define key terms", "definitions"),
        ("Act must specify eligibility criteria", "eligibility"),
        ("Act must specify responsibilities of the administering authority", "responsibilities"),
        ("Act must include enforcement or penalties", "penalties"),
        ("Act must include payment calculation or entitlement structure", "payments"),
        ("Act must include record-keeping or reporting requirements", "record_keeping"),
    ]

    rules = []
    for rule, key in rule_texts:
        present = (report_fields.get(key, {}).get("status") == "present")
        status = "pass" if present else "fail"
        confidence = 90 if present else 30
        evidence = []
        if present and report_fields[key].get("examples"):
            ex = report_fields[key]["examples"][0]
            # include section title + first context snippet (trimmed)
            ctx = ex.get("contexts", [])
            evidence_text = (ex.get("section_title", "") + " — " + (ctx[0][:300] if ctx else ""))
            evidence = [evidence_text]
            confidence = 95
        else:
            evidence = []
        rules.append({
            "rule": rule,
            "status": status,
            "evidence": evidence,
            "confidence": confidence
        })

    # Write final report and debug file
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(json.dumps({
        "report_fields": report_fields,
        "rule_checks": rules,
        "provenance": {"source_file": "data/ukpga_20250022_en.pdf"}
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    OUT_DEBUG.parent.mkdir(parents=True, exist_ok=True)
    OUT_DEBUG.write_text(json.dumps({"debug": debug}, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Wrote", OUT_REPORT, "and", OUT_DEBUG)
    print("Summary:") 
    for r in rules:
        print(f" - {r['rule']}: {r['status']} (confidence {r['confidence']})")

if __name__ == '__main__':
    main()

