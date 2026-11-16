"""Build the disclosed-round startup cohort used by publication charts."""
import collections
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(path): return json.loads((ROOT/path).read_text(encoding='utf8'))


def round_group(round_name):
    if round_name.startswith(('种子','天使')): return '种子 / 天使轮'
    if round_name.startswith('Pre-A'): return 'Pre-A'
    if round_name.startswith('Pre-IPO'): return 'Pre-IPO'
    if len(round_name)>1 and round_name[0] in 'ABCDEF': return round_name[0]+' 轮'
    return None


def build():
    directory=load('skills/ai-company-match/references/companies.json')
    finance=load('docs/finance-2026.json')['records']
    supplement=load('docs/startup-stage-sources-2026.json')
    extra={row['id']:row for row in supplement['records']}
    companies={};excluded=[]
    for company in directory['companies']:
        id=company['id'];record=finance[id]
        if record['listing'] or record.get('otc'):
            excluded.append({'id':id,'name':company['name'],'reason':'上市公司、上市集团团队或新三板挂牌企业'})
            continue
        event=extra.get(id) or record['financing']
        group=round_group(event['round']) if event else None
        if not group:
            excluded.append({'id':id,'name':company['name'],'reason':'无可用于本图的具名融资轮次；不据此判断是否为创业公司'})
            continue
        assert event['sourcePublished'].startswith('2026'), (id,event)
        entity=event.get('entityId',id)
        tags={'Agent' if tag in {'Agent','AI Agent'} else 'AI for Science' if tag in {'AI4Science','AI for Science'} else tag for tag in company['tags']}
        if entity in companies:
            row=companies[entity]
            assert row['stage']==group, entity
            row['directoryIds'].append(id)
            row['tags']=sorted(set(row['tags'])|tags)
            continue
        companies[entity]={
            'id':entity,'name':'演语科技（Liblib / Lovart）' if entity=='evoken' else company['name'],
            'directoryIds':[id],'stage':group,'round':event['round'],'eventDate':event['date'],
            'publisher':event['publisher'],'sourcePublished':event['sourcePublished'],'source':event['url'],
            'note':event.get('note',''),'tags':sorted(tags),
        }
    rows=list(companies.values());stages=collections.Counter(row['stage'] for row in rows)
    tags=collections.Counter(tag for row in rows for tag in row['tags'] if tag!='外企')
    data={
        'asOf':supplement['asOf'],'directoryTotal':directory['total'],'total':len(rows),
        'scope':'北京目录中具有明确融资轮次、未确认上市或挂牌的创业公司；同一公司旗下产品合并计数。',
        'notIncluded':'上市与挂牌主体及其团队；科研机构、成熟集团与未取得具名轮次的记录。未纳入不等于没有融资。',
        'note':'这是已披露轮次样本，不是北京全部创业公司的市场分布；后续战略融资未具名时保留已有具名轮次。',
        'stage':dict(stages),'tags':dict(tags.most_common()),'companies':rows,'excludedDirectoryRecords':excluded,
    }
    assert sum(stages.values())==len(rows)
    assert sum(len(row['directoryIds']) for row in rows)+len(excluded)==directory['total']
    (ROOT/'docs/startup-statistics-2026.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    with (ROOT/'docs/startup-stages-2026.csv').open('w',encoding='utf-8-sig',newline='') as file:
        keys=['公司','轮次分类','披露轮次','融资时间','资料发布日期','信息源','来源链接']
        writer=csv.DictWriter(file,fieldnames=keys);writer.writeheader()
        for row in rows:
            writer.writerow(dict(zip(keys,[row['name'],row['stage'],row['round'],row['eventDate'],row['sourcePublished'],row['publisher'],row['source']])))
    return data


if __name__=='__main__':
    data=build()
    print(json.dumps({'total':data['total'],'stage':data['stage'],'excludedRecords':len(data['excludedDirectoryRecords'])},ensure_ascii=False))
