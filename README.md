# 北京 AI 公司地图

在地图上找北京的 AI 公司，查看公司位置、业务方向和招聘入口。

**[打开地图](https://ningsiyuan1024.github.io/ai-company-map/)** · **[下载求职 Skill](https://github.com/ningsiyuan1024/ai-company-map/raw/refs/heads/main/skills/ai-company-match.zip)** · [北京 AI 岗位](docs/JOBS.md) · [欢迎补充](https://github.com/ningsiyuan1024/ai-company-map/issues)

[![北京 AI 公司地图预览](docs/images/01-beijing-map.png)](https://ningsiyuan1024.github.io/ai-company-map/)

收录 **307 家北京公司与团队**，另支持上海、深圳、杭州和广州。目前主要维护北京，数据更新于 2026 年 11 月 14 日。

## 用 Agent 找岗位

根据你的过往工作、项目记录或简历推荐北京岗位，逐条说明哪段经历对应哪项职责，并给出能力差距和岗位链接。

**[下载 Skill 完整包](https://github.com/ningsiyuan1024/ai-company-map/raw/refs/heads/main/skills/ai-company-match.zip)**，解压后交给支持读取本地文件的 Agent。复制下面这段话即可开始。

```text
请使用附件中的 ai-company-match Skill，根据你能读取到的我的过往工作和项目记录，推荐几个适合我的北京 AI 岗位。每个岗位说明我哪段经历对应哪条职责、还缺什么，并核对官网岗位链接。资料不足时再问我。
```

也可以附上简历或工作经历。支持读取仓库的 Agent 可直接使用 [Skill 目录](skills/ai-company-match)。

<details>
<summary>数据与文件</summary>

[使用说明](skills/ai-company-match/SKILL.md) · [岗位数据](skills/ai-company-match/references/jobs.jsonl) · [公司目录](skills/ai-company-match/references/companies.json) · [字段索引](skills/ai-company-match/references/manifest.json)

</details>

## 统计图

[查看六合一](docs/images/beijing-company-atlas.jpg) · [下载统计图](docs/images/beijing-company-charts.zip) · [雇主名单](docs/EMPLOYERS.md)

![岗位方向占比](docs/images/beijing-job-directions.png)

![主营赛道分布](docs/images/beijing-directory-sectors.png)

![雇主类型](docs/images/beijing-company-overview.png)

![AI 公司地址分布](docs/images/beijing-directory-districts.png)

![北京 AI 岗位常见加分项](docs/images/beijing-job-preferences.png)

![创业公司融资阶段](docs/images/stage-overview-2026.png)

## 使用

搜索公司或方向，按区域、融资阶段、投资机构筛选；点击公司查看详情和招聘入口。复制浏览器地址即可分享当前结果。

## 信息源

| 信息源 | 信息内容 |
| --- | --- |
| [胡润研究院](https://www.hurun.net/) | AI 企业榜单、独角兽身份 |
| [香港交易所披露易](https://www.hkexnews.hk/) | 上市公告、公司定期披露 |
| [巨潮资讯](https://www.cninfo.com.cn/) | 上市公告书、财务报告 |
| [Nasdaq Trader](https://www.nasdaqtrader.com/) | 美国上市主体与证券代码 |
| [泛欧交易所 Euronext](https://www.euronext.com/) | 欧洲上市主体与证券信息 |
| [清科投资界](https://www.pedaily.cn/) | 融资轮次、投资方、披露日期 |
| [国金证券](https://www.gjzq.com.cn/) | 企业融资阶段研究资料 |
| [启明创投](https://www.qimingvc.com/) | 被投企业融资与发展动态 |
| [普华永道](https://www.pwccn.com/) | 行业投融资报告 |
| [投中网](https://www.chinaventure.com.cn/) | 创业公司融资报道 |
| [36氪](https://www.36kr.com/) | 创业公司融资与业务报道 |
| [OFweek](https://www.ofweek.com/) | 机器人产业年度报告 |
| [企业官方公告（如 PixVerse）](https://pixverse.ai/) | 企业直接披露的融资与上市信息 |

<details>
<summary>本地运行</summary>

需要 Python 3。在终端运行以下命令后，打开 <http://127.0.0.1:8766/>。

```bash
git clone https://github.com/ningsiyuan1024/ai-company-map.git
cd ai-company-map
python -m http.server 8766 --bind 127.0.0.1
```

</details>

## 许可

代码采用 [MIT License](LICENSE)，北京底图采用 [ODbL 1.0](MAP-DATA-LICENSE.md)。[Leaflet](vendor/leaflet/LICENSE) 和[坐标转换库](COORDTRANSFORM-LICENSE) 保留各自许可。公司、招聘及融资资料归原权利人所有，再分发时请保留来源并遵守原使用条件。
