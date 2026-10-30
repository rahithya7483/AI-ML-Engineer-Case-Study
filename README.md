# Scheme Field Extraction with Evidence (Case Study A1)

Haqdarshak AI/ML Engineer case study. Problem chosen: A1, field extraction with evidence.

## What this project does

It reads a government scheme document and pulls out 10 fields: scheme name, department, benefit type, benefit amount, benefit frequency, eligibility, documents required, how to apply, deadline and official link.

Every value comes with the exact text it was taken from, the page, the source file name and the date it was captured. If the source does not say something, the field is left empty and marked "not found". If two sources disagree, both values are kept and the field is marked "conflict".

Everything the AI produces is only a draft. A person has to check it before it is used.

## How to run
-> 0. Install the library: `pip install -r requirements.txt`
1. Install the library: `pip install groq`
2. Set your Groq key in PowerShell (do not write it inside any file):
   `$env:GROQ_API_KEY="your_key_here"`
3. Run these from the main folder, in this order:
   - `python src/extract.py` (asks the model, saves `outputs/raw_extractions.json`)
   - `python src/verify.py` (checks the evidence, finds conflicts, saves `outputs/records.json`)
   - `python src/evaluate.py` (compares with `gold/gold.json` and prints the scores)

## Folder

- `docs/` : 4 synthetic sample documents
- `gold/gold.json` : answer key for checking accuracy
- `src/` : the three scripts
- `outputs/` : created when the scripts run

## Sample documents (all synthetic)

- S1: English state circular (`s1_circular_en.txt`) and a made-up MyScheme listing (`s1_myscheme_listing.txt`). The two disagree on the amount (Rs. 25,000 vs Rs. 30,000) and the deadline (31 March 2027 vs 31 December 2026).
- S2: Hindi circular (`s2_circular_hi.txt`).
- S3: a text file made to look like bad OCR output (`s3_scanned_ocr.txt`), with errors like "1,O00" and "Scho1arship". It has no deadline and no link on purpose.

No real government documents or real URLs are used.

## How it works

1. **extract.py** sends each document to the model and asks for each field with its value, exact evidence text and page. The prompt tells the model not to guess and to leave a field empty if the document does not say it. If the model returns an empty answer, the script retries up to 3 times.
2. **verify.py** checks whether the evidence text really exists in the source document (ignoring line breaks and extra spaces). If it does not, the value is thrown away and the field becomes "not found" with a note. It then compares sources of the same scheme. If benefit amount, deadline or official link differ, the status becomes "conflict" and every value is kept with its own source.
3. **evaluate.py** compares the final records with the answer key.

Output format for each field: scheme_ref, field, value, evidence (text, location, source, captured_on), confidence, status, note.

Confidence is not taken from the model. It is "high" when the evidence was found in the document and "low" when there is a conflict. I did this because a model can say it is sure even when it is wrong.

## Model and cost

Model: `openai/gpt-oss-20b` on Groq. I first tried `llama-3.3-70b-versatile` in the code, then changed to this model.

I did not measure the cost. Each scheme is one call per source document, so the cost depends on document length and the current Groq price. I have not calculated a number, so I am not giving one.

## Results

On the 4 sample documents (3 schemes, 30 fields):

- Status (found / not found / conflict): 30 out of 30 correct
- Benefit amount value: 3 out of 3 correct
- Deadline value: 2 out of 2 correct (S3 has no deadline)
- No value was rejected by the evidence check

**This score is weak and I do not trust it fully.** The status check only asks whether the AI said found / not found / conflict. It does not check if the text is right. When I read the text fields myself I found these mistakes:

- S3 benefit_type: the model returned the whole amount sentence instead of "scholarship".
- S3 scheme_name and department: the OCR mistakes ("Scho1arship", "Schoo1") were copied into the value. They should be cleaned in the value and only kept in the evidence.
- S2 benefit_frequency: it says only "yearly" and loses "in two installments".
- S1 benefit_type: it says "grant", which is less specific than my answer key ("one-time cash grant").

A reviewer would notice these only by reading the text fields. The accuracy number would not show them.

## Assumptions

- The documents are synthetic, so real documents will be messier (tables, stamps, many schemes in one PDF).
- The scanned document is simulated as OCR text. I did not run real OCR on an image.
- The answer key was drafted with help from Claude and then checked by me against the documents. It is only 3 schemes, so it is a very small test.
- I compare only benefit amount, deadline and official link across sources. Comparing free text like eligibility would give many false conflicts because the same thing can be worded differently.
- A missing page marker (like in the MyScheme listing) is noted instead of guessed.

## What I left out on purpose

- Real OCR on scanned images or PDFs
- Documents that contain several schemes
- Scoring text fields by code (wording differs too much, and Hindi vs English makes it harder). They are printed for a person to read.
- Checking Hindi answer quality properly (I only checked the evidence text matches the source)
- Cleaning OCR errors in values
- A review screen for researchers
- Cost tracking
- Deciding the quality bar for running on 5,000 schemes (see below)

## When is it good enough for 5,000 schemes?

My suggestion, not something I have tested:

1. A researcher checks a random sample of about 200 schemes by hand, covering different document types, languages and states.
2. Measure accuracy for each field separately, not one overall number.
3. Set a higher bar for risky fields. Amount, deadline and eligibility should be nearly always right, because a wrong value can reach a citizen. Less risky fields can have a lower bar.
4. Fields that fail the bar go to a person for checking on every scheme.
5. Keep sampling after launch to see if quality drops.

## What "field-level accuracy" means

It means we mark each field separately, like marking each question on a form, instead of giving one score to a whole scheme. For example, for 100 schemes we count how many had the benefit amount right, how many had the deadline right, and so on. This tells the team which fields can be trusted and which need a person to check.

## Where AI tools were used

I used Claude to help plan the steps, write the code and draft the answer key and this README structure. I ran the code myself, checked the outputs and checked the answer key against the documents.
