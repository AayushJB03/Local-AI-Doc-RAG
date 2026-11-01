# Progress log

Newest first. Each entry: what changed, what was checked, what is not working and why.

## Phase 0: pipeline callable without HTTP
Done: `backend/app/rag.py` (`ingest`, `retrieve`, `answer`, `ask`); `/upload` and `/chat` are thin wrappers; timings and Ollama token counts are returned instead of `print()`ed; chunk ids are `<filename>::<i>`.
Checked: ingest, retrieve, ask from Python with no server; `/upload` + `/chat` via FastAPI TestClient.

Not working / caveats found:
- **Ollama was not running** at start (`ollama serve` needed); `ask()` fails until it is.
- **First `ask()` embed time is ~5 s**: that is SentenceTransformer lazy warm-up, not retrieval. The eval must run one warm-up query and exclude it from p50/p95.
- **qwen3:4b "thinks"**: a one-line answer used 209-356 completion tokens, so latency is dominated by thinking. This is what E6 tests.
- **Chroma uses L2 distance, not cosine** (its default), though the plan and README say cosine. Left unchanged to keep the baseline honest; becomes its own experiment.
- **Page text is joined with no separator** (`text += extracted`), so words can fuse across page breaks. Kept as-is for the baseline; fix is a candidate E9 item.
- `answer()` token counts come from `ollama.chat`; `total_duration` is not captured yet (wall time is).
- No real PDFs and no eval set exist yet (Phase 1). Smoke test used a one-sentence generated PDF.

## Phase 2 (partial): retrieval metrics
Done: `eval/metrics.py` (evidence-quote hit, hit@k, MRR, percentiles) with a self-check (`python eval/metrics.py`).
Bug caught by the self-check: fuzzy matching (ratio > 0.9) scored "0.004" as a hit for "0.003". Fixed by requiring numbers to match exactly. Without this, numeric questions would have inflated hit rate.
Not done: harness (`run_eval.py`), LLM judge, and the questions themselves. Blocked on Phase 1: need 3-5 publishable documents from you.
From the reference PDFs, added to the plan: report TTFT (needs streaming), faithfulness separately from correctness, judge biases (verbosity/self-preference; the answerer and judge must be different models).
