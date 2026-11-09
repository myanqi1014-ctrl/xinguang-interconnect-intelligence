"""Apply persistent Chinese headline translations; preserve original text for comparison."""
import json,re,time,html
import requests
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_cache():
 p=ROOT/'config/title_translations.json'
 return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
def translate_new(title):
 # Protect technical tokens and numeric specifications from machine translation.
 tokens={}
 def protect(m):
  key='ZXQ'+str(len(tokens))+'QXZ';tokens[key]=m.group();return key
 query=re.sub(r'\b(?:[A-Z][A-Z0-9/.-]*|\d+(?:\.\d+)?(?:%|[A-Za-z]+)?)\b',protect,title)
 if len(query.encode('utf-8'))>500:return ''
 for attempt in range(3):
  try:
   response=requests.get('https://api.mymemory.translated.net/get',params={'q':query,'langpair':'en|zh-CN'},timeout=15)
   response.raise_for_status();data=response.json()
   if int(data.get('responseStatus',0))!=200:raise ValueError('translation unavailable')
   zh=html.unescape(data['responseData']['translatedText'])
   for key,value in tokens.items():
    if key not in zh:raise ValueError('protected token missing')
    zh=zh.replace(key,value)
   if not re.search(r'[\u4e00-\u9fff]',zh):raise ValueError('no Chinese translation')
   return zh
  except (requests.RequestException,ValueError,KeyError,TypeError):
   if attempt<2:time.sleep(2**attempt)
 return ''

def apply_translations(items):
 cache=load_cache();pending=0
 changed=False;budget=0
 for item in items:
  title=item.get('title','')
  if not item.get('accepted') or cache.get(title) or re.search(r'[\u4e00-\u9fff\uac00-\ud7af\u3040-\u30ff]',title):continue
  if budget+len(title)>4500:break
  budget+=len(title)
  zh=translate_new(title)
  if zh:cache[title]=zh;changed=True
 if changed:
  (ROOT/'config/title_translations.json').write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for x in items:
  title=x.get('title','');zh=cache.get(title,'')
  # Chinese headlines retain technical abbreviations and company names.
  chinese=len(re.findall(r'[\u4e00-\u9fff]',title))
  if not zh and chinese>=3 and not re.search(r'[\uac00-\ud7af\u3040-\u30ff]',title):zh=title
  x['title_zh']=zh;x['translation_status']='ready' if zh else 'pending'
  if x.get('accepted') and not zh:pending+=1
 return pending
if __name__=='__main__':
 p=ROOT/'data/news.json';items=json.loads(p.read_text(encoding='utf-8'));pending=apply_translations(items);p.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
 logpath=ROOT/'data/collection_log.json'
 if logpath.exists():
  log=json.loads(logpath.read_text(encoding='utf-8'));log['pending_title_translations']=pending;logpath.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Titles awaiting Chinese translation:',pending)
