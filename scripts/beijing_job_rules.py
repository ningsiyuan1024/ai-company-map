# Beijing job snapshot rules, shared by collection and chart validation.
import re
import unicodedata
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

def normtitle(t):
    t=unicodedata.normalize('NFKC',t).casefold()
    t=re.sub(r'\s*[-（(【]\s*(?:北京|上海|杭州|深圳)(?:[/、, ]+(?:北京|上海|杭州|深圳|广州))*[市）)】 ]*$','',t)
    return re.sub(r'[^\w+#]','',t)
def canonical(u):
    x=urlsplit(u)
    q=[(k,v) for k,v in parse_qsl(x.query) if not k.lower().startswith(('utm','track','refer','spread'))]
    return urlunsplit((x.scheme,x.netloc,x.path,urlencode(q),x.fragment))
def keyurl(u):
    m=re.search(r'/position/(\d{12,})|/(?:job|jobs)/([0-9a-f-]{32,})',u,re.I)
    return next(i for i in m.groups() if i) if m else canonical(u)
ai=re.compile(r'(?<![a-z])ai(?![a-z])|人工智能|大模型|大语言模型|机器学习|深度学习|具身|智能体|多模态|自动驾驶|算法|神经网络|计算机视觉|机器视觉|机器人|强化学习|推理引擎|推理加速|模型推理|模型训[练推]|后训练|机器翻译|语音识别|machine learning|generative ai|deep learning|\b(?:llm|vla|agent(?:ic)?|nlp|rag|aigc|rlhf|cuda)\b',re.I)
def role(t,b):
    if not t:return ''
    b=unescape(re.sub(r'<[^>]+>', ' ', b))
    duty=re.split('任职要求|任职资格|职位要求|岗位要求|优先条件',b,1)[0][:1100]
    duty=re.sub(r'[^。；;\n]{0,90}(?:AI工具|AI 工具|AI 辅助工具|AI办公)[^。；;\n]{0,90}','',duty,flags=re.I)
    if not ai.search(t):
        # Require a concrete AI deliverable for ordinary product, engineering or operations titles.
        action=r'研发|开发|设计|优化|构建|搭建|迭代|部署|训练|评测|标注|运营|负责|落地|集成|测试|推进|交付'
        topic=r'大模型|语言模型|模型推理|机器学习|深度学习|具身|智能体|多模态|自动驾驶|机器人|人工智能|AI\s*(?:平台|产品|功能|应用|系统|能力|模型|服务|助手|引擎|数据|基础设施)|Agent|LLM'
        if not re.search(f'(?:{action})[^。；;，,\n]{{0,16}}(?:{topic})|(?:{topic})[^。；;，,\n]{{0,16}}(?:{action})',duty,re.I):return ''
    primary = re.split(r'\s*[-–—|]\s*', t, maxsplit=1)[0]
    excluded = (r'HRBP|全球人才与组织架构师|研发招聘经理|商业分析师|'
                r'采购(?:寻源)?工程师|采购经理|工程采购|PMO|TPM|'
                r'项目经理|项目管理(?:专家)?')
    if re.search(excluded, t, re.I) and not re.search(r'项目管理运营|运营负责人兼项目经理', t):
        return ''
    engineering = r'后端开发|前端开发|全栈开发|研发工程师|开发工程师|安全检测工程师|运营开发|软件工程师'
    if re.search(engineering, primary) or re.search(r'平台研发工程师', t):
        if not re.search(r'算法', primary):
            return '工程'
    if re.search(r'算法(?:负责人|工程师|研究员|专家|实习生)|运营算法',t):return '算法'
    if re.search(r'产品运营|策略运营|用户运营|社区运营|内容运营',t) and not re.search('运营.{0,4}产品经理',t):return '运营'
    if re.search(r'人力资源|招聘运营|销售运营|财务运营|行政运营|运营商客户|销售经理|招聘实习生',t):return ''
    for k,pat in [('产品',r'产品经理|产品负责人|产品专家|产品设计|策略产品|产品策划|产品实习|product (manager|designer|lead)'),('运营',r'运营(?!商)|community manager|product operations'),('工程',r'推理引擎|推理加速|AI\s*infra|算子|编译器|部署工程|训练框架'),('算法',r'算法|研究员|研究实习|科学家|研究科学|博士后|research( intern| scientist|er)|applied scientist|后训练|post.training|强化学习|模型预训练'),('工程',r'工程|研发|开发|架构师|架构专家|运维|engineer|developer|architect|全栈|前端|后端'),('算法',r'模型训练|机器学习|算法实习')]:
        if re.search(pat,t,re.I):return k
    return ''
