#!/usr/bin/env python3
"""Search the bundled company snapshot locally; no network or resume upload."""
import argparse
import csv
from collections import defaultdict
import json
import re
import sys
from pathlib import Path


def contains(text, term):
    if re.fullmatch(r'[a-z0-9][a-z0-9 +#./-]*', term):
        return bool(re.search(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', text))
    return term in text


def search(data, terms, limit, jobs=(), role=None):
    terms = list(dict.fromkeys(t.strip().casefold() for t in terms if t.strip()))
    matches = defaultdict(list)
    for job in jobs:
        if role and job['role'] != role:
            continue
        title_hits = [t for t in terms if contains(job['title'].casefold(), t)]
        tags = set(job['jdTerms'].casefold().split('|'))
        body_hits = [t for t in terms if t in tags and t not in title_hits]
        if not (title_hits or body_hits):
            continue
        score = (len(title_hits) + len(body_hits), len(title_hits), job['source'] == '企业官网')
        evidence = {k: job[k] for k in ('title', 'role', 'url', 'source', 'asOf')}
        evidence.update(titleMatches=title_hits, jdMatches=body_hits)
        matches[job['company']].append((score, evidence))

    candidates = []
    for company in data['companies']:
        fields = [company['name'], company.get('category', ''), *company.get('aliases', []), *company.get('tags', [])]
        text = ' '.join(fields).casefold()
        company_hits = [term for term in terms if contains(text, term)]
        postings = sorted(matches[company['id']], key=lambda item: item[0], reverse=True)
        if not postings and not company_hits:
            continue
        evidence = [j for _, j in postings[:3]]
        hits = set(company_hits)
        for j in evidence:
            hits.update(j['titleMatches'] + j['jdMatches'])
        best = postings[0][0] if postings else (0, 0, False)
        rank = (bool(postings), *best, len(company_hits))
        row = dict(company, matchedTerms=[t for t in terms if t in hits], jobs=evidence,
                   evidenceType='jobSnapshot' if postings else 'companyOnly')
        candidates.append((rank, row))
    candidates.sort(key=lambda item: item[1]['id'])
    candidates.sort(key=lambda item: item[0], reverse=True)
    return {
        'asOf': data['asOf'], 'city': data['city'], 'directoryTotal': data['total'],
        'matchingCompanies': len(candidates), 'companiesWithJobEvidence': sum(bool(r['jobs']) for _, r in candidates),
        'method': 'Keyword recall from dated postings and company tags; verify current openings.',
        'companies': [r for _, r in candidates[:limit]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terms', nargs='+', required=True, help='Anonymized skills or business keywords')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--role', choices=('算法', '工程', '产品', '运营'), help='Filter job evidence by role')
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error('--limit must be between 1 and 50')
    if not any(term.strip() for term in args.terms):
        parser.error('Provide at least one non-empty term')
    path = Path(__file__).resolve().parents[1] / 'references' / 'companies.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        with path.with_name('jobs.csv').open(encoding='utf-8-sig', newline='') as source:
            jobs = list(csv.DictReader(source))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot read company snapshot: {error}\n')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(search(data, args.terms, args.limit, jobs, args.role), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
