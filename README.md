# vn-tax-rag

Production-oriented CLI for Vietnamese tax-law research using **ChromaDB** (retrieval) and a local or remote **LLM** (generation).

Crawl official public gazette pages, chunk by article (`Điều`), index embeddings, then ask grounded questions from the terminal with step-by-step logs.

> Disclaimer: this tool is for research and learning. It is **not** legal advice. Always verify answers against the official legal text.

## Features

- Seed-driven crawler (`config/seeds.yaml`) for core tax laws (TNCN, GTGT, TNDN, Tax Administration)
- HTML + PDF extraction with rate limiting and retry
- Article-aware chunking and ChromaDB ingest
- RAG Q&A via OpenAI-compatible APIs (Ollama by default)
- Structured step logs: `STEP crawl.*`, `STEP ingest.*`, `STEP rag.*`

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) (recommended for local answers) **or** any OpenAI-compatible LLM endpoint
- Network access for the first `vn-tax crawl`

## Quick start

```bash
git clone <this-repo>
cd chromadb-vn-law

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e .
cp .env.example .env        # edit paths / model if needed

# Pull a local model (example)
ollama pull qwen2.5:3b

# 1) Crawl official gazette PDFs into data/processed
vn-tax crawl

# 2) Chunk + index into ChromaDB
vn-tax ingest

# 3) Ask a question
vn-tax ask "Giảm trừ gia cảnh khi tính thuế thu nhập cá nhân?"
vn-tax ask "VAT tax rates" --tax-type GTGT --show-context
```

Check system state:

```bash
vn-tax status
```

Verbose logs / log file:

```bash
vn-tax --verbose crawl
vn-tax --log-file logs/run.log ingest
vn-tax --verbose ask "Who is a personal income taxpayer?" -t TNCN
```

## Configuration

Copy `.env.example` to `.env`:

| Variable | Purpose |
|----------|---------|
| `CHROMA_PATH` | Persistent Chroma directory |
| `DATA_DIR` | Root for `raw/` and `processed/` |
| `SEEDS_PATH` | Seed YAML path |
| `COLLECTION_NAME` | Chroma collection name |
| `CRAWL_DELAY_SECONDS` | Delay between seed fetches |
| `EMBEDDING_MODEL` | SentenceTransformer model for Chroma (`paraphrase-multilingual-MiniLM-L12-v2`) |
| `LLM_BASE_URL` | OpenAI-compatible base URL (`http://localhost:11434/v1` for Ollama) |
| `LLM_API_KEY` | API key (`ollama` placeholder is fine for local) |
| `LLM_MODEL` | Model name (`qwen2.5:3b`, `qwen2.5:7b`, …) |

Seeds live in [`config/seeds.yaml`](config/seeds.yaml). Add more official Cong Bao / public PDF pages there to expand the corpus.

## CLI reference

| Command | Description |
|---------|-------------|
| `vn-tax crawl` | Fetch seeds, store raw HTML/PDF under `data/raw`, write cleaned text to `data/processed` |
| `vn-tax ingest` | Reset collection, chunk processed files, upsert embeddings |
| `vn-tax ask "…"` | Retrieve top-k passages and generate an answer |
| `vn-tax status` | Show paths, seed/file counts, collection size |

Useful `ask` flags:

- `-t / --tax-type TNCN|GTGT|TNDN|ADMIN`
- `-n / --n-results 4`
- `--show-context`

## Project layout

```
config/seeds.yaml          # Crawl targets
src/vn_tax_rag/
  cli.py                   # Typer entrypoint (vn-tax)
  config.py
  logging_setup.py
  crawl/                   # Fetch + extract
  ingest/                  # Chunk + upsert
  rag/                     # Retrieve + generate
data/
  raw/                     # Crawler cache (gitignored)
  processed/               # Clean UTF-8 law text (txt gitignored; run vn-tax crawl)
tests/                     # Unit tests
```

## Development

```bash
pip install -e ".[dev]"
pytest -q
python -m vn_tax_rag status
```

## Notes on crawling

- Official Cong Bao pages are preferred because attached PDFs are usually text-extractable.
- Some portal “signed” PDFs are scanned images; the crawler skips empty extractions and retries.
- SSL verification is relaxed for certain government CDN certificate chains; traffic is still HTTPS.
- Be respectful: default delay is configured via `CRAWL_DELAY_SECONDS`.

## License

MIT
