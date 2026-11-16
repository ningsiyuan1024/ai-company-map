#!/usr/bin/env python3
"""Search the bundled company snapshot locally; no network or resume upload."""
import argparse
import json
import re
import sys
from pathlib import Path


def contains(text, term):
    if re.fullmatch(r'[a-z0-9][a-z0-9 +#./-]*', term):
        return bool(re.search(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', text))
    return term in text


def search(data, terms, limit):
    results = []
    terms = list(dict.fromkeys(t.strip().casefold() for t in terms if t.strip()))
    for company in data['companies']:
        fields = [company['name'], company.get('category', ''), *company.get('aliases', []), *company.get('tags', [])]
        text = ' '.join(fields).casefold()
        hits = [term for term in terms if contains(text, term)]
        if hits:
            results.append({**company, 'matchedTerms': hits})
    results.sort(key=lambda row: (-len(row['matchedTerms']), row['id']))
    return {
        'asOf': data['asOf'], 'city': data['city'], 'directoryTotal': data['total'],
        'matchingCompanies': len(results),
        'method': 'Keyword recall only; not suitability scoring or live job verification.',
        'companies': results[:limit],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terms', nargs='+', required=True, help='Anonymized skills or business keywords')
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error('--limit must be between 1 and 50')
    if not any(term.strip() for term in args.terms):
        parser.error('Provide at least one non-empty term')
    path = Path(__file__).resolve().parents[1] / 'references' / 'companies.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot read company snapshot: {error}\n')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(search(data, args.terms, args.limit), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
