"""Explainable topic screening, not an assertion of factual accuracy or popularity."""
import json,re
from pathlib import Path
RULES=json.loads((Path(__file__).resolve().parents[1]/'config/editorial_rules.json').read_text(encoding='utf-8'))
def has(text,word):
 if word.isascii() and len(word)<=6 and word.isalnum():return bool(re.search(r'(?<![a-z0-9])'+re.escape(word.lower())+r'(?![a-z0-9])',text.lower()))
 return word.lower() in text.lower()
def hits(text,words):return [w for w in words if has(text,w)]
def classify(title,summary=''):
 title=title or '';text=title+' '+(summary or '')
 direct=hits(title,RULES['direct']);conditional=hits(title,RULES['conditional']);context=hits(text,RULES['context']);excluded=hits(title,RULES['exclude_title'])
 # Reject general topics and boilerplate descriptions: a specific signal must occur in the title.
 accepted=bool(direct or (conditional and context)) and not excluded
 columns=[]
 if accepted:
  columns=[c for c,words in RULES['columns'].items() if hits(title,words)]
  if not columns:columns=['最新资讯']
 score=min(100,40+len(direct)*8+len(hits(title,RULES['priority_signals']))*20) if accepted else 0
 return {'accepted':accepted,'columns':columns,'priority':'优先选题' if score>=66 else '常规跟踪','relevance_score':score,'matched_terms':list(dict.fromkeys(direct+conditional)),'selection_reason':'标题命中核心互联主题' if direct else ('材料或器件主题同时具有互联应用背景' if accepted else '缺少明确互联主题或命中排除规则'),'rules_version':RULES['version']}

BUSINESS_SIGNALS=['发布','推出','量产','扩产','投产','研发','创新','收购','并购','融资','合作','签约','订单','交付','业绩','财报','launch','unveil','acquir','funding','financing','partner','collaborat','shipment','production','sampling','earnings']
NONBUSINESS=['招聘','党建','团建','妇女节','运动会','员工活动','股东大会通知','recruitment','career fair']
TENDER_TOPICS=['光模块','光收发','光通信','光通讯','光互联','光互连','光开关','光纤连接','光纤耦合','硅光','误码仪','光谱分析仪','高速互联','800G','1.6T','400G','optical transceiver','optical interconnect']
HIGH_SPEED=['400G','800G','1.6T','3.2T','6.4T','12.8T','CPO','NPO','硅光','高速互联','高速光','光互联','光互连']
def tender_stage(title):
 for terms,label in [(['终止','废标','流标'],'终止/废标'),(['更正','变更','澄清'],'变更/澄清'),(['候选人','预中标'],'中标候选'),(['中标','成交','结果公告'],'中标/成交'),(['询价','询比','比选','竞价'],'询价/比选'),(['预告','采购意向'],'采购意向')]:
  if hits(title,terms):return label
 return '招标/采购公告'
def assess(src,title,summary=''):
 result=classify(title,summary)
 kind='招标采购' if src.get('kind')=='tender' or src.get('content_type')=='招标采购' else '新闻资讯'
 result['content_type']=kind
 if kind=='招标采购':
  related=bool(hits(title,TENDER_TOPICS) or (hits(title,['数据中心','智算中心','算力中心']) and hits(title,['交换机','网络','互联'])))
  if hits(title,['激光模块','激光美容','激光焊接','激光切割']) and not hits(title,['光通信','光互联','光互连','硅光','CPO','800G','1.6T']):related=False
  result.update(accepted=related,columns=['招标采购'] if related else [],tender_stage=tender_stage(title),procurement_level='高速互联相关' if hits(title,HIGH_SPEED) else '一般光通信采购',selection_reason='采购公告标题命中光通信或算力互联设备',priority='优先选题' if hits(title,HIGH_SPEED) else '常规跟踪')
 elif not result['accepted'] and src.get('company_scope')=='optical' and hits(title,BUSINESS_SIGNALS) and not hits(title,NONBUSINESS+RULES['exclude_title']):
  result.update(accepted=True,columns=['最新资讯'],priority='常规跟踪',relevance_score=40,selection_reason='光通信专业企业的产品、合作或经营动态')
 return result

def decorate(x):
 x.update(assess(x,x.get('title',''),x.get('summary','')))
 return x
