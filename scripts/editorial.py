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
def decorate(x):
 result=classify(x.get('title',''),x.get('summary',''));x.update(result);return x
