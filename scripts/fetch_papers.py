import requests
import json
from pathlib import Path

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/"

FIELDS = "title,authors,year,venue,url,externalIds"

def fetch_from_semantic_scholar(paper_id):
    url = f"{SEMANTIC_SCHOLAR_API}{paper_id}?fields={FIELDS}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

def fetch_from_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()["message"]
    return None

def format_entry(data):
    title = data.get("title", "Untitled")
    year = data.get("year") or data.get("issued", {}).get("date-parts", [[None]])[0][0]
    authors = data.get("authors") or data.get("author", [])
    if isinstance(authors, list):
        authors_str = ", ".join(
            a.get("name") if isinstance(a, dict) else f"{a.get('given', '')} {a.get('family', '')}"
            for a in authors
        )
    else:
        authors_str = ""

    url = data.get("url") or data.get("URL", "")
    venue = data.get("venue") or data.get("container-title", [""])[0]

    return f"- **{title}** ({year})  \n  {authors_str}  \n  [{venue}]({url})\n"

def main():
    ids = Path("paper_ids.txt").read_text().strip().splitlines()
    entries = []

    for pid in ids:
        # Try Semantic Scholar first
        ss = fetch_from_semantic_scholar(pid)
        if ss:
            entries.append(format_entry(ss))
            continue

        # Fallback to Crossref (DOI only)
        if "/" in pid:
            cr = fetch_from_crossref(pid)
            if cr:
                entries.append(format_entry(cr))
                continue

        entries.append(f"- **{pid}** — metadata not found\n")

    md = "# Publications\n\n" + "\n".join(entries)
    Path("index.md").write_text(md)

if __name__ == "__main__":
    main()
