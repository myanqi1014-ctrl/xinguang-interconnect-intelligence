# 芯光互联 · 算力互联情报中心

8家企业官方发布追踪，按企业、技术方向、近1/3/10天筛选。保留原文、归档及逐来源状态。发布日期无法核实时单独归档，不以采集时间冒充发布时间。英文保留原文，尚未启用自动翻译。

## 自动运行
GitHub Actions 每天 `04:00 UTC`（北京时间12:00）触发，也支持 Actions → Daily intelligence collection → Run workflow。GitHub 调度可能延迟；公共仓库长期无活动时定时工作流可能被暂停。

## 首次启用
仓库 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**。随后运行工作流。站点预期地址为 https://myanqi1014-ctrl.github.io/xinguang-interconnect-intelligence/ ，须以部署成功结果为准。

## 本地
`pip install -r requirements.txt`，`python scripts/collect.py`，`python -m http.server 8000`。

## 来源状态
来源配置见 config/sources.json。仅收集官方域名新闻链接，不引入第三方新闻。列表只扫描最新一页，首次并非完整历史回填。异常页面、访问限制、无匹配内容分别记录。新易盛官网出现异常内容时停止收录并报错，需人工核验。
