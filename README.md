# 芯光互联 · 算力互联情报中心

43个来源入口（38个网站、5个公众号）追踪，32个来源尝试公开自动采集、11个入口待专用接入，按企业、技术方向、近1/3/10天筛选。保留原文、归档及逐来源状态。发布日期无法核实时单独归档，不以采集时间冒充发布时间。英文保留原文，尚未启用自动翻译。

## 自动运行
GitHub Actions 每天 `04:00 UTC`（北京时间12:00）触发，也支持 Actions → Daily intelligence collection → Run workflow。GitHub 调度可能延迟；公共仓库长期无活动时定时工作流可能被暂停。

## 首次启用
仓库 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**。随后运行工作流。站点预期地址为 https://myanqi1014-ctrl.github.io/xinguang-interconnect-intelligence/ ，须以部署成功结果为准。

## 本地
`pip install -r requirements.txt`，`python scripts/collect.py`，`python -m http.server 8000`。

## 来源状态
来源配置见 config/sources.json。仅收集官方域名新闻链接，不引入第三方新闻。列表只扫描最新一页，首次并非完整历史回填。异常页面、访问限制、无匹配内容分别记录。新易盛官网出现异常内容时停止收录并报错，需人工核验。

## 扩展来源
来源完整映射自用户新闻导航站，见 config/sources.json。证券披露平台需配置股票代码；IEEE/Optica需限定检索范围；5个微信公众号为单篇文章入口，暂不能作为持续订阅源。这11项在页面标注为待专用接入。其余32项逐站尝试公开RSS和新闻列表，实际成功情况以每次采集日志为准。付费研究仅收公开摘要，不采付费全文。来源并发6路、每站至多扫描8条列表候选，不等于完整历史覆盖。

## 公众号选题规则
config/editorial_rules.json 为可编辑规则，scripts/editorial.py 执行标题核心词、条件背景、排除词筛选及四栏目候选归类。不会仅因泛AI/GPU/算力命中而自动入选。材料、器件、封装测试须具有互联应用背景。历史记录重新判定并保留 accepted 标记，页面只展示符合规则的内容。栏目判断是选题提示，不是事实核验、真实热度判断或自动成稿。
