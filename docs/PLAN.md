# Plan: Turn the RAG app into a measured project

Source: advice from a senior AI engineer. Core idea: **nobody hires on a demo; they hire on evidence you can make a system measurably better.**

**Deliverable:** this repo with an eval table in the README, plus a short write-up on what worked and what didn't. Then send him the repo.

**Rules while working**
1. Change **one thing at a time**. Re-run the eval. Record the result. Commit.
2. Never trust an output you haven't checked. Assume something is wrong (this is the skill he says gets screened for).
3. Every number in the README must be reproducible with one command.

---

## Where the code is today (what the eval has to deal with)

| Knob | Currently | Location |
|---|---|---|
| Chunking | 500 chars, 100 overlap, `RecursiveCharacterTextSplitter` | `backend/app/upload.py` |
| Embedding | `all-MiniLM-L6-v2` | `backend/app/embedding_model.py` |
| Retrieval | top-5 cosine similarity, no rerank | `backend/app/vector_store.py` |
| Prompt | single template, no "answer only from context / say you don't know" rule | `backend/app/main.py` |
| LLM | `qwen3:4b` via Ollama | `backend/app/main.py` |
| Timing | `print()` only, not recorded | `backend/app/main.py` |

**Blocker to fix first:** the pipeline is welded into the HTTP handlers (`/upload`, `/chat`), with a single global collection and hardcoded settings. An eval script can't vary chunk size or prompt without editing code. Step 0 fixes that.

---

## Phase 0: Make the pipeline testable (1-2 days)

Goal: call RAG from Python without HTTP, with every knob as a parameter.

- [x] Create `backend/app/rag.py` with plain functions:
  - `ingest(pdf_path, chunk_size=500, overlap=100, collection_name="eval") -> n_chunks`
  - `retrieve(question, k=5, collection_name=...) -> chunks + ids`
  - `answer(question, chunks, prompt_version="v1", model="qwen3:4b") -> text + token counts`
  - `ask(question, **config) -> {answer, chunks, latency_ms: {embed, retrieve, llm}, tokens}`
- [x] Make `main.py` and `upload.py` thin wrappers that call `rag.py`.
- [x] Return timings and token counts from `ollama.chat` (`eval_count`, `prompt_eval_count`, `total_duration`) instead of `print()`.
- [x] Stable chunk ids that include the document name, so a gold chunk can be identified across re-chunking (see Phase 1).
- [x] Smoke test: ingest one PDF, ask one question, get an answer from a Python REPL.

**Done when:** `python -c "from app.rag import ask; print(ask('...'))"` works with no server running.

---

## Phase 1: Build the eval set (2-4 days, the most important part)

Goal: 100 real questions with gold answers. Quality here decides whether the whole project is credible.

- [x] Pick **3-5 documents** you can legally publish in the repo (public papers, government reports, open docs). Put them in `eval/docs/`. Mix: one dense technical paper, one with tables, one long report.
- [ ] Write **~100 questions** by hand (LLM-drafted questions are OK as a starting point but you must read and fix each). Mix on purpose:
  - ~50 factual lookup ("What is the learning rate used?")
  - ~20 multi-chunk / synthesis ("Compare method A and B")
  - ~15 numeric / table questions
  - ~15 **unanswerable** questions (the doc does not say). The correct answer is "not in the document". This tests hallucination.
- [ ] Store as `eval/questions.jsonl`, one per line:
  ```json
  {"id": "q001", "doc": "paper1.pdf", "question": "...", "gold_answer": "...", "gold_evidence": "exact quote from the doc", "type": "factual"}
  ```
- [ ] **Retrieval gold = the evidence quote, not a chunk id.** Count a retrieval "hit" if any retrieved chunk contains the quote (normalized whitespace, or fuzzy ratio > 0.9). This survives changing the chunk size. Chunk ids would not.
- [ ] Split: ~70 dev questions (tune against these) and ~30 **held-out test** questions (only run at the very end). Otherwise you overfit to your own eval.

**Done when:** `eval/questions.jsonl` has 100 rows, you've re-read every gold answer, and the dev/test split is committed.

---

## Phase 2: Eval harness + baseline (2-3 days)

Goal: one command prints a metrics table.

- [ ] `eval/run_eval.py --config configs/baseline.yaml` runs all questions through `rag.ask()` and writes `eval/results/<config>-<timestamp>.json` (per-question detail) and a summary row.
- [ ] **Retrieval metrics** (cheap, no LLM needed):
  - Hit rate @ k (`k = 1, 3, 5`)
  - MRR
- [ ] **Answer metrics**:
  - Start with **LLM-as-judge** (correct / partially / wrong / hallucinated) using a *different, stronger* model than the one answering, with the gold answer in the judge prompt. Anthropic API or a larger local model both work.
  - **Hand-check 20 of the judge's verdicts.** Report judge-vs-you agreement in the README. If agreement is poor, the judge is the bug.
  - For unanswerable questions: refusal rate (did it correctly say "not in the document"?).
- [ ] **Latency + cost per query:** p50 / p95 of total, retrieval, and LLM ms. Cost: local = tokens/sec and GPU/CPU time (say so honestly); also compute "what this would cost on a hosted API" from token counts so the number is comparable.
- [ ] Config file holds every knob: `chunk_size`, `overlap`, `k`, `embedding_model`, `reranker`, `prompt_version`, `llm`.
- [ ] Run the **baseline** (current app settings) on the dev set 3 times. Note run-to-run variance. Any improvement smaller than that noise is not real.

**Done when:** a baseline row exists, e.g. `baseline | hit@5 0.xx | MRR 0.xx | acc 0.xx | p50 x.xs | p95 x.xs`.

---

## Phase 3: Experiments, one change at a time (1-2 weeks)

Each experiment: write a hypothesis first, change one knob, run the dev set, record, commit. Keep failures in the table. They are part of the story.

| # | Change | Hypothesis | Likely effect |
|---|---|---|---|
| E1 | Chunk size 250 / 500 / 1000, overlap 0 / 100 / 200 | Bigger chunks keep context but dilute the match | hit rate, latency |
| E2 | `k` = 3 / 5 / 10 | More context raises recall, may hurt answer quality | hit@k vs accuracy |
| E3 | Better embedding model (`bge-small/base`, `e5`, `nomic-embed`) | MiniLM is weak on technical text | hit rate |
| E4 | **Reranker** (`bge-reranker-base` cross-encoder): retrieve 20, rerank to 5 | Biggest typical win | hit@5, +latency |
| E5 | **Prompt v2**: "Answer only from the context. If it isn't there, say 'Not in the document.' Quote the passage." | Fewer hallucinations on unanswerable questions | accuracy, refusal rate |
| E6 | Qwen3 **thinking off** vs on | Thinking costs lots of tokens/latency; may not help | accuracy vs latency |
| E7 | Model swap: `qwen3:4b` vs `qwen3:8b` vs `llama3.1:8b` | Quality vs speed tradeoff | accuracy, latency |
| E8 | Hybrid search (BM25 + vector) | Helps exact terms / numbers / names | hit rate on numeric questions |
| E9 (stretch) | Better PDF parsing (`pymupdf` / `pdfplumber`) for tables | Table questions are failing at extraction, not retrieval | numeric question accuracy |

Order: E1, E2, E4, E5 first. Those will teach you the most for the least work. Don't start E3/E7/E8 until those four are logged.

**For every experiment, also do error analysis.** Pull the 10 worst questions and classify each failure: *retrieval miss*, *retrieved but LLM ignored it*, *bad PDF extraction*, *bad gold answer*, *judge error*. The failure bucket tells you what to fix next. Don't guess.

**Done when:** `eval/EXPERIMENTS.md` has a table with every run, plus a final combined config evaluated **once** on the held-out test set.

---

## Phase 4: Package it (3-4 days)

- [ ] README gets a **Results** section near the top: baseline vs best config table (hit@5, MRR, accuracy, refusal rate, p50/p95 latency, tokens/query, equivalent API cost), plus one chart if cheap.
- [ ] "Reproduce" section: exact commands to run the eval.
- [ ] Short write-up (`docs/WRITEUP.md`, then post on LinkedIn / dev.to / Medium):
  - What I measured and how (the eval set, the judge, the agreement check)
  - What moved the number, what didn't, and what surprised me
  - What was wrong with my own eval and how I found out
  - Latency/cost tradeoffs
- [ ] Clean the repo: remove or move `test_*.py` scratch files into a real `tests/`, add `.env.example`, pin `requirements.txt`.
- [ ] Message the senior engineer with the repo link. He asked for this explicitly.

---

## Phase 5: Second project, fine-tune something small (after Phase 4)

Do not start this until the RAG project is published. One project finished beats two half-done.

- [ ] Pick **one narrow task** that is checkable. Ideas that connect to this repo:
  - Query rewriting for retrieval (turn a chat follow-up into a standalone question)
  - Judge model for answer correctness (distill your LLM-judge)
  - Classifier: answerable vs unanswerable given context
- [ ] Open model, small: Qwen3 0.6B-1.7B or Llama 3.2 1B/3B. LoRA/QLoRA with `peft` + `trl` (Unsloth for speed). Free Colab/Kaggle GPU is enough.
- [ ] Build train / **held-out** sets. Show fine-tuned beats base model on the held-out set, with a table.
- [ ] Publish on Hugging Face: model card, dataset, eval results, usage snippet. Link it from the RAG README.

---

## Phase 6: Job search in parallel (start once Phase 4 is up)

His list, in order of practicality:
1. **Contract / lab work:** Turing, Mercor (hourly, South Asia OK). Your eval-writing and judging experience is exactly their kind of work.
2. **First proper role:** Wellfound, Cutshort, Instahyre.
3. **Small Upwork contracts** to build a paid track record.
4. **Remote EU/US roles** come after one or two of the above plus public work.

Skills he says are screened for: Python, evals, RAG, agents + tool calling, one cloud, and checking your own output. After Phase 4, consider a small agent/tool-calling add-on to this app and deploying it on one cloud (AWS, GCP, or Azure) to tick the last boxes.

---

## Suggested timeline

| Week | Work |
|---|---|
| 1 | Phase 0 + start writing questions |
| 2 | Finish Phase 1 (100 Qs), Phase 2 harness + baseline |
| 3-4 | Phase 3 experiments E1, E2, E4, E5, error analysis |
| 5 | Remaining experiments, held-out run, Phase 4 packaging, write-up, send repo |
| 6+ | Phase 5 fine-tune, Phase 6 applications |

## How we'll work together

You drive; I help build, break and debug. Good places to bring me in: Phase 0 refactor, the harness, reviewing your gold answers for ambiguity, reading failure buckets, and sanity-checking that a "win" isn't just noise. Start by telling me **"start Phase 0"**.
