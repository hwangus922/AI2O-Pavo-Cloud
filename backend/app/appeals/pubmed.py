"""PubMed E-utilities client.

Searches PubMed for clinical evidence supporting a procedure and diagnosis,
then fetches the top abstracts. The public E-utilities endpoints need no API
key for this volume.

A failed lookup is never fatal: the appeal proceeds with no citations rather
than not being written at all, and the caller can see that the list is empty.
"""
from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from typing import Any, Optional

import httpx

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# NCBI asks that clients identify themselves.
TOOL_NAME = "pavo-cloud"
DEFAULT_TIMEOUT = 15.0
DEFAULT_MAX_RESULTS = 3


class PubMedError(RuntimeError):
    """Raised when PubMed cannot be reached or returns something unusable."""


def build_query(procedure_name: str, diagnosis_name: str) -> str:
    """Build a PubMed query from the procedure and diagnosis."""
    terms = [term.strip() for term in (procedure_name, diagnosis_name) if term and term.strip()]
    if not terms:
        return ""
    return " AND ".join(f"({term})" for term in terms)


def search_ids(
    query: str,
    *,
    max_results: int = DEFAULT_MAX_RESULTS,
    client: Optional[httpx.Client] = None,
) -> list[str]:
    """Return the top PubMed IDs for a query."""
    if not query:
        return []

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
        "tool": TOOL_NAME,
    }

    owns_client = client is None
    http = client or httpx.Client(timeout=DEFAULT_TIMEOUT)
    try:
        response = http.get(ESEARCH_URL, params=params)
        response.raise_for_status()
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise PubMedError(f"PubMed search failed: {exc}") from exc
    finally:
        if owns_client:
            http.close()

    return list(body.get("esearchresult", {}).get("idlist", []))[:max_results]


def _text_of(node: Optional[ElementTree.Element]) -> Optional[str]:
    """Flatten an element's text, including any nested markup."""
    if node is None:
        return None
    text = "".join(node.itertext()).strip()
    return text or None


def _parse_article(article: ElementTree.Element) -> dict[str, Any]:
    """Pull the citation fields out of one PubmedArticle element."""
    pmid = _text_of(article.find(".//MedlineCitation/PMID"))

    authors: list[str] = []
    for author in article.findall(".//AuthorList/Author"):
        last = _text_of(author.find("LastName"))
        initials = _text_of(author.find("Initials"))
        collective = _text_of(author.find("CollectiveName"))

        if last:
            authors.append(f"{last} {initials}" if initials else last)
        elif collective:
            authors.append(collective)

    # An abstract may arrive in labelled sections.
    sections: list[str] = []
    for chunk in article.findall(".//Abstract/AbstractText"):
        body = _text_of(chunk)
        if not body:
            continue
        label = chunk.get("Label")
        sections.append(f"{label}: {body}" if label else body)

    year = _text_of(article.find(".//Journal/JournalIssue/PubDate/Year"))
    if not year:
        # Some records carry only a MedlineDate such as "2019 Jul-Aug".
        medline_date = _text_of(article.find(".//Journal/JournalIssue/PubDate/MedlineDate"))
        year = medline_date.split(" ")[0] if medline_date else None

    return {
        "pmid": pmid,
        "title": _text_of(article.find(".//Article/ArticleTitle")),
        "authors": authors,
        "journal": _text_of(article.find(".//Journal/Title")),
        "year": year,
        "abstract": "\n\n".join(sections) if sections else None,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
    }


def parse_articles(xml_text: str) -> list[dict[str, Any]]:
    """Parse an efetch PubmedArticleSet response into citations."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise PubMedError(f"Could not parse the PubMed response: {exc}") from exc

    return [_parse_article(article) for article in root.findall(".//PubmedArticle")]


def fetch_articles(
    pmids: list[str],
    *,
    client: Optional[httpx.Client] = None,
) -> list[dict[str, Any]]:
    """Fetch and parse abstracts for a list of PubMed IDs."""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": TOOL_NAME,
    }

    owns_client = client is None
    http = client or httpx.Client(timeout=DEFAULT_TIMEOUT)
    try:
        response = http.get(EFETCH_URL, params=params)
        response.raise_for_status()
        xml_text = response.text
    except httpx.HTTPError as exc:
        raise PubMedError(f"PubMed fetch failed: {exc}") from exc
    finally:
        if owns_client:
            http.close()

    return parse_articles(xml_text)


def find_supporting_evidence(
    procedure_name: str,
    diagnosis_name: str,
    *,
    max_results: int = DEFAULT_MAX_RESULTS,
    client: Optional[httpx.Client] = None,
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """Search PubMed and return (citations, error).

    error is None on success, or a short explanation when the lookup failed —
    the appeal continues either way.
    """
    query = build_query(procedure_name, diagnosis_name)
    if not query:
        return [], "No procedure or diagnosis text to search on."

    try:
        pmids = search_ids(query, max_results=max_results, client=client)
        return fetch_articles(pmids, client=client), None
    except PubMedError as exc:
        return [], str(exc)


def format_citations(citations: list[dict[str, Any]]) -> str:
    """Render citations for the appeal-letter prompt."""
    if not citations:
        return "No supporting literature was retrieved."

    blocks: list[str] = []
    for citation in citations:
        authors = ", ".join(citation.get("authors") or []) or "Unknown authors"
        blocks.append(
            "\n".join(
                [
                    f"PMID {citation.get('pmid') or 'unknown'}",
                    f"Title: {citation.get('title') or 'Untitled'}",
                    f"Authors: {authors}",
                    f"Journal: {citation.get('journal') or 'Unknown'}"
                    f" ({citation.get('year') or 'n.d.'})",
                    f"Abstract: {citation.get('abstract') or 'No abstract available.'}",
                ]
            )
        )

    return "\n\n".join(blocks)
