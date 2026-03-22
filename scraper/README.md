# Scraper Package

This package extracts deposit, credit, and branch data for three Armenian banks:

- Ameriabank
- Ardshinbank
- Mellat Bank

## Output

The compiler normalizes everything into the same schema:

- `deposits`
- `credits`
- `branches`

Each category may contain:

- source URLs
- page records
- text chunks
- tables
- extracted PDF content

The final artifacts are written to:

- `knowledge_base.json`
- `knowledge_base.md`

## Run

From the project root:

```powershell
python -m scraper.compiler --strict
```

You can also compile a single bank:

```powershell
python -m scraper.compiler --bank ameriabank
python -m scraper.compiler --bank ardshinbank
python -m scraper.compiler --bank mellatbank
```

## Notes

- The scraper removes fragments and non-Armenian variants from source URLs.
- The compiler is designed to keep page-level records, not just flattened text.
- The markdown output is compact enough for prompt injection into the voice agent.
