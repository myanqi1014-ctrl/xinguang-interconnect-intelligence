"""Apply persistent Chinese headline translations; preserve original text for comparison."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_cache():
 p=ROOT/'config/title_translations.json'
 return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
def apply_translations(items):
 cache=load_cache();pending=0
 for x in items:
  title=x.get('title','');zh=cache.get(title,'')
  # Chinese headlines retain technical abbreviations and company names.
  chinese=len(re.findall(r'[\u4e00-\u9fff]',title))
  if not zh and chinese>=3 and not re.search(r'[\uac00-\ud7af\u3040-\u30ff]',title):zh=title
  x['title_zh']=zh;x['translation_status']='ready' if zh else 'pending'
  if x.get('accepted') and not zh:pending+=1
 return pending
if __name__=='__main__':
 p=ROOT/'data/news.json';items=json.loads(p.read_text(encoding='utf-8'));pending=apply_translations(items);p.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8');print('Titles awaiting Chinese translation:',pending)
