import json
import os
import time
from pathlib import Path
from openai import OpenAI
from httpx import ReadTimeout, HTTPError

SECTIONS_FILE = Path("outputs/extracted_sections.json")
OUT_SUMMARY = Path("outputs/summary.json")
OUT_INTERMEDIATE = Path("outputs/summary_intermediate.json")

CHUNK_MAX_CHARS = 1200
MAX_TOKENS_PER_CALL = 400
RETRIES = 3
RETRY_BACKOFF = 2.0

def chunk_text(t, max_chars=CHUNK_MAX_CHARS):
    return [t[i:i+max_chars] for i in range(0, len(t), max_chars)]

def call_openai_with_retries(prompt, client, max_tokens=MAX_TOKENS_PER_CALL):
    last_exc = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content
        except (ReadTimeout, HTTPError, ConnectionError) as e:
            last_exc = e
            wait = RETRY_BACKOFF ** (attempt - 1)
            print(f"[WARN] OpenAI call failed (attempt {attempt}/{RETRIES}): {e}. Backing off {wait:.1f}s")
            time.sleep(wait)
        except Exception as e:
            last_exc = e
            print(f"[ERR] Unexpected OpenAI error: {e}")
            time.sleep(RETRY_BACKOFF)
    raise SystemExit(f"OpenAI calls failed after {RETRIES} attempts. Last error: {last_exc}")

def save_intermediate(intermediate_list):
    OUT_INTERMEDIATE.parent.mkdir(parents=True, exist_ok=True)
    OUT_INTERMEDIATE.write_text(json.dumps({"intermediate": intermediate_list}, indent=2, ensure_ascii=False), encoding="utf-8")

def main():
    if not SECTIONS_FILE.exists():
        raise SystemExit(f"Missing input file: {SECTIONS_FILE}. Run extractor first.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY not set in environment.")
    client = OpenAI(api_key=api_key)
    data = json.loads(SECTIONS_FILE.read_text(encoding="utf-8"))
    whole = "\n\n".join(s.get("text","") for s in data.get("sections", []))
    if not whole.strip():
        raise SystemExit("Extracted sections appear empty.")
    chunks = chunk_text(whole)
    print(f"[INFO] Total chunks: {len(chunks)} (chunk size ~{CHUNK_MAX_CHARS} chars)")
    intermediate = []
    if OUT_INTERMEDIATE.exists():
        try:
            d = json.loads(OUT_INTERMEDIATE.read_text(encoding="utf-8"))
            intermediate = d.get("intermediate", [])
            print(f"[INFO] Loaded {len(intermediate)} intermediate results (resume).")
        except Exception:
            intermediate = []
    start_chunk = len(intermediate)
    for i in range(start_chunk, len(chunks)):
        c = chunks[i]
        print(f"[INFO] Summarising chunk {i+1}/{len(chunks)} ...")
        prompt = (
            "You are summarising a chunk of the Universal Credit Act 2025. "
            "Produce 3-5 concise bullets focusing on: PURPOSE, KEY DEFINITIONS, ELIGIBILITY, "
            "OBLIGATIONS, and ENFORCEMENT. Label bullets. Output only bullets.\n\n"
            f"CHUNK {i+1}/{len(chunks)}:\n\n{c}"
        )
        try:
            ans = call_openai_with_retries(prompt, client, max_tokens=MAX_TOKENS_PER_CALL)
        except SystemExit as e:
            print(f"[FATAL] Summariser failed on chunk {i+1}: {e}")
            save_intermediate(intermediate)
            raise
        intermediate.append(ans)
        save_intermediate(intermediate)
        time.sleep(0.5)
    print("[INFO] Combining intermediate bullets into final 5-10 bullets.")
    final_prompt = (
        "Combine the intermediate bullets below into 5-10 final bullets covering: "
        "Purpose, Key definitions, Eligibility, Obligations, Enforcement. Be concise and factual.\n\n"
        + "\n\n".join(intermediate)
    )
    try:
        final = call_openai_with_retries(final_prompt, client, max_tokens=800)
    except SystemExit as e:
        print(f"[FATAL] Reduction step failed: {e}")
        save_intermediate(intermediate)
        raise
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps({"summary_text": final}, indent=2, ensure_ascii=False), encoding="utf-8")
    if OUT_INTERMEDIATE.exists():
        try:
            OUT_INTERMEDIATE.unlink()
        except Exception:
            pass
    print("[OK] Summary written to", OUT_SUMMARY)

if __name__ == "__main__":
    main()

