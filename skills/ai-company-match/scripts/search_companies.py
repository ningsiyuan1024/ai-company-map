#!/usr/bin/env python3
"""Search the bundled company snapshot locally; no network or resume upload."""
import argparse
from collections import defaultdict
import json
import re
import sys
from pathlib import Path


def contains(text, term):
    if re.fullmatch(r'[a-z0-9][a-z0-9 +#./-]*', term):
        return bool(re.search(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', text))
    return term in text


def search(data, terms, limit, jobs=(), role=None, toward=(), avoid_title=()):
    terms = list(dict.fromkeys(t.strip().casefold() for t in terms if t.strip()))
    toward = list(dict.fromkeys(t.strip().casefold() for t in toward if t.strip()))
    avoid_title = [t.strip().casefold() for t in avoid_title if t.strip()]
    matches = defaultdict(list)
    for job in jobs:
        if role and job['role'] != role:
            continue
        title = job['title'].casefold()
        if any(contains(title, t) for t in avoid_title):
            continue
        title_hits = [t for t in terms if contains(title, t)]
        tags = set(job['jdTerms'].casefold().split('|'))
        duty = (job.get('dutyExcerpt') or '').casefold()
        duty_hits = [t for t in terms if contains(duty, t)]
        body_hits = [t for t in terms if t in tags and t not in title_hits and t not in duty_hits]
        if not (title_hits or duty_hits or body_hits):
            continue
        desired_title = [t for t in toward if contains(title, t)]
        desired_body = [t for t in toward if (t in tags or contains(duty, t)) and t not in desired_title]
        score = (bool(desired_title or desired_body), bool(desired_title),
                 len(set(title_hits + duty_hits + body_hits)), len(set(title_hits + duty_hits)), job['source'] == '企业官网')
        evidence = {k: job[k] for k in ('title', 'role', 'url', 'source', 'asOf')}
        evidence.update({k: job[k] for k in ('city', 'sourceUrl', 'id', 'dutyExcerpt') if k in job})
        evidence.update(titleMatches=title_hits, dutyMatches=duty_hits, jdMatches=body_hits)
        if toward:
            evidence.update(towardTitle=desired_title, towardJD=desired_body)
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
            hits.update(j['titleMatches'] + j['dutyMatches'] + j['jdMatches'])
        best = postings[0][0] if postings else (False, False, 0, 0, False)
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
    parser.add_argument('--toward', nargs='+', default=[], help='Work the candidate wants to do next')
    parser.add_argument('--avoid-title', nargs='+', default=[], help='Explicitly unwanted terms in a job title')
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error('--limit must be between 1 and 50')
    if not any(term.strip() for term in args.terms):
        parser.error('Provide at least one non-empty term')
    path = Path(__file__).resolve().parents[1] / 'references' / 'companies.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        jobs = []
        with path.with_name('jobs.jsonl').open(encoding='utf8') as source:
            for line in source:
                record = json.loads(line)
                origin = record['source']
                jobs.append(dict(id=record['id'], company=record['companyId'], title=record['title'],
                                 role=record['role'], city=record['location']['includesCity'],
                                 dutyExcerpt=record['work']['dutyExcerpt'],
                                 jdTerms='|'.join(record['work']['mentionedTerms']),
                                 source=origin['name'], url=origin['detailUrl'],
                                 sourceUrl=origin['listingUrl'], asOf=origin['checkedOn']))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot read company snapshot: {error}\n')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(search(data, args.terms, args.limit, jobs, args.role, args.toward, args.avoid_title), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
