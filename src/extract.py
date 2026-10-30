import json
import os
from datetime import date
from groq import Groq

MODEL = "openai/gpt-oss-20b"

# which file belongs to which scheme
SOURCES = [
    {"scheme_ref": "S1", "file": "s1_circular_en.txt"},
    {"scheme_ref": "S1", "file": "s1_myscheme_listing.txt"},
    {"scheme_ref": "S2", "file": "s2_circular_hi.txt"},
    {"scheme_ref": "S3", "file": "s3_scanned_ocr.txt"},
]

FIELDS = [
    "scheme_name", "department", "benefit_type", "benefit_amount",
    "benefit_frequency", "eligibility", "documents_required",
    "how_to_apply", "deadline", "official_link",
]

PROMPT = """You are helping a researcher fill a government scheme record.
Read the document below and extract these fields: {fields}

Rules:
1. For every field give: "value", "evidence", "page".
2. "evidence" must be copied EXACTLY, character by character, from the document. Do not fix spelling or OCR mistakes in the evidence.
3. "page" is the number from the nearest [Page N] marker above the evidence. If there is no page marker, use null.
4. If the document does not say it, set value, evidence and page to null. Never guess or fill from your own knowledge.
5. For eligibility and documents_required, "value" is a list of short items.
6. If the text has OCR errors (for example 1,O00), write the clean value in "value" but keep the original text in "evidence".
7. Return only a JSON object with the field names as keys.

DOCUMENT:
{document}
"""


def extract(client, text, tries=3):
    prompt = PROMPT.format(fields=", ".join(FIELDS), document=text)
    last_error = None
    for attempt in range(1, tries + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_completion_tokens=4000,
                reasoning_effort="low",
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            last_error = e
            print("  attempt", attempt, "failed")
    raise last_error


def main():
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    os.makedirs("outputs", exist_ok=True)
    results = []

    for s in SOURCES:
        path = os.path.join("docs", s["file"])
        with open(path, encoding="utf-8") as f:
            text = f.read()
        print("Reading", s["file"])
        try:
            fields = extract(client, text)
        except Exception as e:
            print("  failed:", e)
            fields = {}
        results.append({
            "scheme_ref": s["scheme_ref"],
            "source_name": s["file"],
            "captured_on": str(date.today()),
            "model": MODEL,
            "fields": fields,
        })

    with open("outputs/raw_extractions.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Saved outputs/raw_extractions.json")


if __name__ == "__main__":
    main()