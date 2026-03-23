import html
import requests
from pathlib import Path

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/"

FIELDS = "title,authors,year,venue,url,externalIds"

START = "<!-- PUBLICATIONS_START -->"
END = "<!-- PUBLICATIONS_END -->"


def update_publications_section(new_md):
    text = Path("index.md").read_text() 
    if START not in text or END not in text: 
        raise RuntimeError("Markers not found in index.md")
    before = text.split(START)[0]
    after = text.split(END)[1]
    updated = before + START + "\n" + new_md + "\n" + END + after
    Path("index.md").write_text(updated)

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

    title_html = html.escape(title)
    year_html = html.escape(str(year)) if year is not None else ""
    authors_html = html.escape(authors_str)
    venue_html = html.escape(venue)
    url_html = html.escape(url, quote=True)

    year_suffix = f" <span>({year_html})</span>" if year_html else ""

    return (
        '<article class="publication-entry">\n'
        f"  <h4>{title_html}{year_suffix}</h4>\n"
        f"  <p>{authors_html}</p>\n"
        f'  <a href="{url_html}">{venue_html}</a>\n'
        "</article>\n"
    )

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

        pid_html = html.escape(pid)
        entries.append(
            '<article class="publication-entry publication-entry-missing">\n'
            f"  <h4>{pid_html}</h4>\n"
            "  <p>Metadata not found.</p>\n"
            "</article>\n"
        )

    html_block = "\n".join(entries)
    update_publications_section(html_block)

if __name__ == "__main__":
    main()
