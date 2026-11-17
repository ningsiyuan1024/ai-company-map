"""Match previously collected public job descriptions to the Beijing directory.

Historical 11–13 November sample. Usage: python scripts/import_beijing_jds.py OFFICIAL_SNAPSHOT_FOLDER PLATFORM_JD30_JSON OUTPUT_CSV
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
directory = json.loads((ROOT/"skills/ai-company-match/references/companies.json").read_text(encoding="utf8"))["companies"]
names = defaultdict(set)
for row in directory:
    for name in [row["name"],row["name"].split(" / ")[0],*row["aliases"]]:
        names[name.casefold()].add(row["id"])
overrides = {"腾讯 WorkBuddy":"tencent","人形机器人创新中心":"xhumanoid","BOSS直聘":"kanzhun_nanbeige",
             "演语科技／LiblibAI":"liblib","深度求索（DeepSeek）":"deepseek","阶跃星辰":"stepfun",
             "小红书":"xiaohongshu","字节跳动":"bytedance","苹果":"apple","亚马逊":"amazon",
             "英伟达":"nvidia","百度":"baidu","美团":"meituan","阿里巴巴":"alibaba","谷歌":"google"}
ids = {r["id"] for r in directory}
assert set(overrides.values()) <= ids
def employer(name):
    matches = names[name.casefold()]
    return overrides.get(name) or (next(iter(matches)) if len(matches)==1 else None)

AI = re.compile(r"(?<![a-z])ai(?![a-z])|人工智能|大模型|机器学习|深度学习|具身智能|智能体|多模态|自动驾驶|算法|神经网络|计算机视觉|机器视觉|机器人|强化学习|推理加速|machine learning|deep learning|generative ai|\b(?:llm|agent|nlp|rag|aigc)\b",re.I)
# Job family comes from the title; responsibilities establish AI relevance.
def classify(title,body):
    t=title.lower()
    explicit_task = re.search(r"(训练|微调|部署|优化|研发|构建|搭建|设计|评测|运营).{0,10}(大模型|机器学习平台|推理引擎|智能体系统|模型训练平台)",body[:450])
    if not (AI.search(t) or explicit_task):return None
    if re.search(r'运营|operations manager|community manager',t):
        return ("运营","数据与评测运营" if re.search("数据|标注|评测|评估|训练",t) else "用户、内容与生态运营")
    if re.search(r'产品经理|产品策划|产品设计|产品专家|策略产品|产品实习|产品负责人|product manager|product designer',t):
        return ("产品","平台与工具产品" if re.search("平台|工具|开发者|coding|infra|to ?b|b端",t) else "应用与策略产品")
    if re.search(r'推理.*(?:研发|工程|加速|优化)|(?:部署|加速).*工程|infra|基础设施|训练框架|推理引擎|编译器|算子',t):
        return ("工程","训练与推理基础设施")
    if re.search('算法|研究员|科学家|研究实习|research scientist|applied scientist|machine learning scientist',t):
        if re.search("机器人|具身|自动驾驶|运动控制|感知|规控",t):return ("算法","机器人与自动驾驶算法")
        if re.search("推荐|搜索|排序|广告|检索|风控",t):return ("算法","搜索、推荐与决策")
        return ("算法","模型研究与应用算法")
    if re.search("工程师|开发|研发|架构师|engineer|architect|developer",t):
        return ("工程","智能体与应用开发" if re.search("agent|智能体|应用|全栈|客户端|前端|后端",t) else "系统与工程实现")
    return None

def canonical(url):
    u=urlsplit(url)
    q=[(k,v) for k,v in parse_qsl(u.query) if not k.lower().startswith(("utm_","track","referer","spread","securityid")) and k not in {"src","lid","ka","sessionId"}]
    return urlunsplit(("https",u.netloc,u.path,urlencode(q),u.fragment))

if len(sys.argv) != 4:
    raise SystemExit(__doc__)

candidates=[]
def add(name,title,city,body,url,source,day,jid=""):
    key=employer(name)
    if not key or not re.search("北京|beijing",str(city),re.I) or "青岛；卡片北京" in str(city):return
    if not title or not url.startswith(("http://","https://")) or len(body)<25:return
    group=classify(title,body)
    if group:
        candidates.append((key,title.strip(),*group,canonical(url),source,str(day)[:10],str(jid)))

for path in sorted(Path(sys.argv[1]).glob("*完整JD.jsonl")):
    for line in path.open(encoding="utf-8-sig"):
        if not line.strip():continue
        r=json.loads(line)
        if "关闭" in str(r.get("status","")) or r.get("status") in ("closed","expired"):continue
        if "PostURL" in r:
            add("腾讯",r["RecruitPostName"],r["LocationName"],r["Responsibility"],r["PostURL"],"企业官网","2026-11-11",r["PostId"])
        elif "job_path" in r:
            add("亚马逊",r["title"],r["city"],r["description"],"https://www.amazon.jobs"+r["job_path"],"企业官网","2026-11-11",r["id_icims"])
        else:
            body=r.get("body") or []
            text=" ".join(str(x[-1]) for x in body if isinstance(x,list) and x) if isinstance(body,list) else str(body)
            add(r["company"],r["title"],r.get("city"),text,r.get("url") or "","企业官网",r.get("observed_at") or r.get("fetched_at") or "2026-11-11",r.get("id",""))
for job in json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig"))["jobs"]:
    if job["platform"]=="企业官网":continue
    title=job["title"]
    if title.startswith("查看 ") and " 的 " in title:title=title.split(" 的 ",1)[1].removesuffix(" 职位")
    add(job["company"],title,job["location"],job["jd"],job["url"],job["platform"],"2026-11-13")
# Preserve the eight individually reviewed links, preferring these newer records.
for r in csv.DictReader((ROOT/"docs/beijing-job-links.csv").open(encoding="utf-8-sig")):
    group=classify(r["职位"],"训练大模型 "+r["主要职责"]) or {"算法":("算法","模型研究与应用算法")}[r["方向"]]
    candidates.insert(0,(employer(r["公司"]),r["职位"],*group,canonical(r["官网"]),"企业官网","2026-11-17",""))

# Shared landing pages cannot identify individual postings. Discard those collisions.
titles=defaultdict(set)
for key,title,_,_,url,_,day,_ in candidates:
    if day!="2026-11-17":titles[url].add(title)
seen_urls=set();seen_ids=set();seen_titles=set();result=[]
for key,title,role,cluster,url,source,date,jid in candidates:
    normalized=re.sub(r'\s+','',title).casefold()
    if len(titles[url])>1 or url in seen_urls or (jid and (key,jid) in seen_ids) or (key,normalized) in seen_titles:continue
    result.append((key,title,role,cluster,url,source,date))
    seen_urls.add(url);seen_titles.add((key,normalized));seen_ids.add((key,jid))
with Path(sys.argv[3]).open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f);w.writerow(["目录ID","岗位","方向","职责组","详情","来源","资料日期"]);w.writerows(result)
print(len(result),len({r[0] for r in result}),Counter(r[5] for r in result),Counter(r[3] for r in result))
