# 🔬 PubMed AI Research Assistant

### A 5-Agent Pipeline for Expert-Quality Medical Literature Search

---

## What This Is

Most people cannot search PubMed effectively. The search syntax is complex, the medical vocabulary is specialized, and finding the right papers requires expertise that takes years to develop.

This system solves that. You type a plain English question. Five AI agents work in sequence to understand your question, translate it into expert medical vocabulary, build a professional search query, retrieve and rank papers from PubMed's 30 million articles, and highlight the exact sentences that answer what you asked.

**Before this system:**

> Search "exercise depression teens" → 4,847 unsorted results → 45 minutes of reading

**After this system:**

> Type "Does exercise help depressed teenagers?" → 10 ranked papers with key sentences highlighted → 45 seconds

---

## Architecture

```
User Question (plain English)
         │
         ▼
┌─────────────────────┐
│  Agent 1            │  Extracts WHO, WHAT, COMPARED TO, OUTCOME
│  PICO Extractor     │  "teenagers with depression" / "exercise" / "mood improvement"
└────────┬────────────┘
         │  PICOResult
         ▼
┌─────────────────────┐
│  Agent 2            │  Converts plain words → official MeSH terms
│  MeSH Translator    │  "kids" → "Adolescent" | "heart attack" → "Myocardial Infarction"
└────────┬────────────┘
         │  MeSHResult
         ▼
┌─────────────────────┐
│  Agent 3            │  Builds expert PubMed boolean query
│  Query Builder      │  ("Adolescent"[MeSH]) AND ("Exercise"[MeSH]) AND ("Depression"[MeSH])
└────────┬────────────┘
         │  QueryResult
         ▼
┌─────────────────────┐
│  Agent 4            │  Fetches 50 papers → ChromaDB ranks top 10
│  PubMed Finder      │  Highlights 1-3 sentences per paper that answer your question
└────────┬────────────┘
         │  list[PaperResult]
         ▼
┌─────────────────────┐
│  Agent 5            │  Learns from your clicks over time
│  Feedback Learner   │  Improves future queries based on what you found relevant
└────────┬────────────┘
         │
         ▼
  Streamlit UI — ranked papers, highlighted sentences, relevance scores
```

---

## Tech Stack

| Component        | Technology                             | Cost                    |
| ---------------- | -------------------------------------- | ----------------------- |
| LLM              | Groq API — Llama 3.3 70B               | Free tier               |
| Medical Search   | NCBI E-utilities API                   | Free, no key needed     |
| Vector Search    | ChromaDB (local)                       | Free, open source       |
| Embeddings       | sentence-transformers all-MiniLM-L6-v2 | Free, runs locally      |
| Feedback Storage | SQLite                                 | Free, built into Python |
| Frontend         | Streamlit                              | Free                    |
| Backend          | Python 3.11+                           | Free                    |

**Total infrastructure cost: $0**

---

## Project Structure

```
pubmed-multi-agent/
│
├── agents/
│   ├── __init__.py
│   ├── agent1_interpreter.py       # PICO extraction from plain English
│   ├── agent2_mesh_suggester.py    # MeSH term translation
│   ├── agent3_query_builder.py     # PubMed boolean query construction
│   ├── agent4_finder.py            # PubMed search + RAG ranking + highlighting
│   └── agent5_feedback_learner.py  # Interaction tracking + query improvement
│
├── core/
│   ├── __init__.py
│   ├── llm_client.py               # Shared LLM wrapper — all agents use this
│   ├── pubmed_client.py            # NCBI E-utilities API calls + MeSH cache
│   └── pipeline.py                 # Orchestrates all 5 agents end-to-end
│
├── storage/
│   ├── chroma_store.py             # ChromaDB vector store wrapper
│   ├── feedback_store.py           # SQLite read/write for interactions
│   └── feedback.db                 # Auto-created on first run
│
├── frontend/
│   └── app.py                      # Streamlit UI
│
├── tests/
│   ├── test_agent1.py
│   ├── test_agent2.py
│   ├── test_agent3.py
│   ├── test_agent4.py
│   └── test_agent5.py
│
├── data/
│   └── mesh_terms.json             # Cached MeSH lookups — grows over time
│
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
│
├── .env                            # API keys — never commit this
├── .gitignore
├── config.py                       # Global constants loaded from .env
├── requirements.txt
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.11 or higher
- A free Groq API key from [console.groq.com](https://console.groq.com)
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/yourusername/pubmed-multi-agent.git
cd pubmed-multi-agent
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> **Note for Windows users:** If `sentence-transformers` fails, install PyTorch first:
>
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install sentence-transformers
> ```

### Step 4 — Configure environment variables

Create a `.env` file in the project root:

```bash
# Windows
type nul > .env

# Mac / Linux
touch .env
```

Open `.env` and add:

```env
GROQ_API_KEY=your_groq_api_key_here
NCBI_EMAIL=your_email@example.com
```

Get your Groq API key at [console.groq.com](https://console.groq.com) → API Keys → Create API Key. It is free.

### Step 5 — Initialize the cache file

```bash
python -c "import json; open('data/mesh_terms.json', 'w', encoding='utf-8').write('{}')"
```

### Step 6 — Verify the installation

```bash
python -c "from core.llm_client import call_llm; print(call_llm('You are helpful.', 'Say hello.'))"
```

You should see a response from the LLM with no errors.

---

## Running the Application

### Launch the Streamlit UI

```bash
streamlit run frontend/app.py
```

Open your browser at `http://localhost:8501`.

### Using the UI

1. Type any medical question in plain English into the search box
2. Click **Search** or press Enter
3. Watch the pipeline tracker show each agent completing in real time
4. Read the ranked papers — highlighted sentences show exactly what answers your question
5. Click **✓ Relevant** or **✗ Not Relevant** on each paper to train the feedback learner
6. Open the **Pipeline Transparency** panel to see the PICO breakdown, MeSH terms, and generated query

### Example questions to try

```
Does exercise help depressed teenagers?
Is aspirin better than ibuprofen for headaches?
Does walking reduce lower back pain in adults?
Can meditation reduce anxiety in college students?
What is the effect of vitamin D on bone density in postmenopausal women?
```

---

## Running the Pipeline Programmatically

```python
from core.pipeline import run_pipeline

result = run_pipeline("Does exercise help depressed teenagers?")

print(result.pubmed_query.query_string)
# → ("Adolescent"[MeSH] OR "teenager"[tiab]) AND ("Exercise"[MeSH]) AND ("Depression"[MeSH])

print(f"Found {len(result.papers)} papers in {result.timing.total_seconds}s")

for paper in result.papers[:3]:
    print(f"\n{paper.title}")
    print(f"Score: {paper.relevance_score}")
    print(f"URL: {paper.pubmed_url}")
    for sentence in paper.highlighted_sentences:
        print(f"  → {sentence}")
```

---

## Running Tests

Run all unit tests:

```bash
pytest tests/ -v
```

Run tests for a specific agent:

```bash
pytest tests/test_agent1.py -v
pytest tests/test_agent2.py -v
pytest tests/test_agent3.py -v
pytest tests/test_agent4.py -v
pytest tests/test_agent5.py -v
```

### Expected test results

```
tests/test_agent1.py::test_exercise_depression_teens          PASSED
tests/test_agent1.py::test_aspirin_vs_ibuprofen               PASSED
tests/test_agent1.py::test_single_word_query                  PASSED

tests/test_agent2.py::test_heart_attack_maps_to_myocardial    PASSED
tests/test_agent2.py::test_kids_maps_to_child_or_adolescent   PASSED
tests/test_agent2.py::test_walking_maps_to_walking            PASSED
tests/test_agent2.py::test_cache_grows_after_lookup           PASSED
tests/test_agent2.py::test_full_pipeline_pico_to_mesh         PASSED
...
```

---

## How Each Agent Works

### Agent 1 — PICO Extractor (`agent1_interpreter.py`)

Takes a plain English question and extracts four structured components using the PICO framework — the gold standard for medical literature search:

| Component        | Meaning                  | Example                   |
| ---------------- | ------------------------ | ------------------------- |
| **P**opulation   | Who is being studied     | teenagers with depression |
| **I**ntervention | What treatment or action | exercise                  |
| **C**omparison   | What it is compared to   | no exercise               |
| **O**utcome      | What result is measured  | mood improvement          |

If the LLM returns malformed JSON, the agent automatically retries once with a stricter prompt before raising an error.

### Agent 2 — MeSH Translator (`agent2_mesh_suggester.py`)

Converts plain English terms into official MeSH (Medical Subject Headings) — the controlled vocabulary PubMed uses internally. This is critical because PubMed indexes papers by MeSH terms, not plain words.

- First tries the NCBI MeSH API directly for accurate, deterministic results
- Falls back to the LLM when NCBI returns nothing
- Caches every lookup in `data/mesh_terms.json` — NCBI is only called once per unique term

### Agent 3 — Query Builder (`agent3_query_builder.py`)

Constructs a valid PubMed boolean query following expert search conventions:

```
("Adolescent"[MeSH] OR "teenager"[tiab])
AND ("Exercise"[MeSH] OR "physical activity"[tiab])
AND ("Depression"[MeSH] OR "depressive disorder"[tiab])
```

Validates that every term has a field tag (`[MeSH]` or `[tiab]`), checks for balanced parentheses, removes duplicate blocks, and retries if the output is invalid.

### Agent 4 — PubMed Finder (`agent4_finder.py`)

Three-stage retrieval pipeline:

1. **Fetch** — Sends the query to PubMed via NCBI E-utilities, retrieves up to 50 PMIDs
2. **Rank** — Embeds all abstracts + the original question using `all-MiniLM-L6-v2`, stores in ChromaDB, retrieves the top 10 by cosine similarity
3. **Highlight** — For each of the top 10 papers, calls the LLM to identify 1–3 sentences that directly answer the original question

### Agent 5 — Feedback Learner (`agent5_feedback_learner.py`)

Stores every user interaction (relevant / not relevant clicks) in SQLite. After 10+ interactions on similar topics, it analyzes which MeSH terms and query patterns led to relevant results and passes those learnings as context to Agent 3 on future runs.

This is a cold-start system — it returns no suggestions for the first 10 interactions. That is correct behavior, not a bug.

---

## Performance Targets

| Metric                     | Target                | How to Measure                            |
| -------------------------- | --------------------- | ----------------------------------------- |
| Unit test pass rate        | 100%                  | `pytest tests/ -v`                        |
| MeSH translation accuracy  | ≥ 80%                 | Expected terms found in generated query   |
| PMID hit rate              | ≥ 70%                 | Known relevant papers appearing in top 10 |
| Pipeline speed (first run) | < 45 seconds          | `result.timing.total_seconds`             |
| Pipeline speed (cached)    | < 20 seconds          | Second run on same topic                  |
| UI stability               | No crashes in 10 runs | Manual browser testing                    |

---

## Data & Privacy

- **No data leaves your machine** except API calls to Groq (LLM) and NCBI (PubMed search)
- `mesh_terms.json` — cached MeSH lookups, stored locally
- `feedback.db` — SQLite database of your clicks, stored locally
- `chroma_db/` — vector embeddings of paper abstracts, stored locally
- `.env` — API keys, never committed to git (enforced by `.gitignore`)

---

## Troubleshooting

**`JSONDecodeError` on `mesh_terms.json`**

Windows wrote the file with the wrong encoding. Fix:

```bash
python -c "import json; open('data/mesh_terms.json', 'w', encoding='utf-8').write('{}')"
```

**`ModuleNotFoundError: No module named 'pkg_resources'`**

Upgrade setuptools first:

```bash
pip install --upgrade pip setuptools wheel
```

**Streamlit shows `ModuleNotFoundError` warnings in terminal**

Harmless — Streamlit's file watcher scanning the transformers library. Already suppressed by `.streamlit/config.toml`. The app works correctly regardless.

**LLM returns no response / rate limit error**

Groq free tier has rate limits. Wait 60 seconds and retry. For production use, consider adding `time.sleep(1)` between LLM calls.

**ChromaDB collection not found**

The `chroma_db/` directory may be corrupted. Delete it and rerun:

```bash
# Windows
rmdir /s /q chroma_db

# Mac / Linux
rm -rf chroma_db
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run the full test suite: `pytest tests/ -v`
5. Commit: `git commit -m "Add: your feature description"`
6. Push and open a pull request

All pull requests must pass the full test suite before merging.

---

## Roadmap

- [ ] Export results to PDF / CSV
- [ ] Full abstract expandable view in UI
- [ ] NCBI API key support (10 req/s instead of 3)
- [ ] User accounts with persistent feedback across sessions
- [ ] Support for clinical trial filters (RCT only, systematic reviews only)
- [ ] Multi-language query support
- [ ] End-to-end benchmark suite with 10 gold standard queries

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/) — free PubMed API
- [MeSH Browser](https://meshb.nlm.nih.gov/) — Medical Subject Headings vocabulary
- [Groq](https://console.groq.com) — free LLM inference
- [ChromaDB](https://www.trychroma.com) — open source vector database
- [sentence-transformers](https://www.sbert.net/) — free local embeddings
- [Streamlit](https://streamlit.io) — Python web UI framework

---

<div align="center">
  <sub>Built with Python · Powered by free APIs · No paid infrastructure required</sub>
</div>
