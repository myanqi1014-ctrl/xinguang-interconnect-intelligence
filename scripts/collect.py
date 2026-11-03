"""Collect public headlines and short descriptions; keep source failures visible."""
import concurrent.futures,json,re,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin,urlparse,urldefrag
import requests,feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dp
R=Path(__file__).resolve().parents[1];D=R/'data'
S=json.loads((R/'config/sources.json').read_text(encoding='utf-8'))
K=json.loads((R/'config/keywords.json').read_text(encoding='utf-8'))
H={'User-Agent':'Mozilla/5.0 (compatible; XinguangNews/1.1; public news reader)'}
DATE=r'20\d{2}[-年/.]\d{1,2}[-月/.]\d{1,2}|\b\d{1,2}/\d{1,2}/\d{2,4}\b|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+20\d{2}'
def now():return datetime.now(timezone.utc).isoformat()
def tags(s):
 l=s.lower()
 return [k for k,v in K.items() if any(re.search(r'(?<![a-z0-9])'+re.escape(w.lower())+r'(?![a-z0-9])',l) if w.isascii() else w.lower() in l for w in v)]
def dt(s):
 try:
  s=re.sub('[年月日]','-',str(s)).strip('-');x=dp.parse(s)
  if not 2000<=x.year<=datetime.now().year+1:return ''
  return (x if x.tzinfo else x.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()
 except (ValueError,TypeError,OverflowError):return ''
def same_site(a,b):
 a=urlparse(a).hostname or '';b=urlparse(b).hostname or ''
 return a.split('.')[-2:]==b.split('.')[-2:] and urlparse(a if '://' in a else 'https://'+a).scheme in ('http','https')
def get(url):
 r=requests.get(url,headers=H,timeout=(6,12));r.raise_for_status();r.encoding=r.apparent_encoding or 'utf-8';return r

def clean(s):return ' '.join(BeautifulSoup(s or '', 'html.parser').get_text(' ',strip=True).split())
def item(src,title,url,pub='',summary=''):
 return {'id':hashlib.sha256(url.encode()).hexdigest()[:16],'source_id':src['id'],'source_name':src['name'],'source_type':src.get('group','企业官方新闻中心'),'title':clean(title),'url':url,'published_at':dt(pub),'summary':clean(summary)[:500],'tags':tags(title+' '+summary),'collected_at':now()}
def listed_date(a):
 node=a
 for _ in range(3):
  if node is None:break
  m=re.search(DATE,node.get_text(' ',strip=True),re.I)
  if m:return m.group()
  node=node.parent
 return ''
def article(src,title,url,pub):
 summary='';warning=''
 try:
  r=get(url);page=BeautifulSoup(r.text,'html.parser')
  meta=page.select_one('meta[property="article:published_time"],meta[name="date"],meta[name="pubdate"]');tm=page.select_one('time')
  if meta and dt(meta.get('content')):pub=meta['content']
  elif tm and dt(tm.get('datetime') or tm.get_text(' ',strip=True)):pub=tm.get('datetime') or tm.get_text(' ',strip=True)
  elif not pub:
   body=(page.select_one('article') or page.select_one('main') or page).get_text(' ',strip=True);m=re.search(DATE,body,re.I)
   if m:pub=m.group()
  desc=page.select_one('meta[name="description"],meta[property="og:description"]')
  if desc:summary=desc.get('content','')
 except Exception as e:warning='部分详情页无法读取，保留列表标题与原文入口'
 return item(src,title,url,pub,summary),warning

def collect(src):
 log={'source':src['name'],'source_id':src['id'],'url':src['url'],'group':src.get('group',''),'found':0,'errors':[],'warnings':[],'status':'empty'};found=[]
 if src.get('mode')=='manual':
  log.update(status='manual',note=src.get('note','需专用接口'));return found,log
 try:
  r=get(src['url']);soup=BeautifulSoup(r.text,'html.parser');title=soup.title.get_text() if soup.title else ''
  if re.search(r'slot88|slot thailand|casino',title,re.I):raise ValueError('来源返回异常内容，已停止采集，请人工核验官网')
  if len(r.content)<1000:raise ValueError('页面未返回可解析的新闻列表')
  feeds=[]
  for x in soup.select('link[rel~="alternate"][href]'):
   if any(k in x.get('type','').lower() for k in ('rss','atom')):
    u=urljoin(r.url,x['href'])
    if same_site(u,r.url):feeds.append(u)
  for feed in feeds[:2]:
   try:
    f=feedparser.parse(get(feed).content)
    for e in f.entries[:60]:
     u=urldefrag(e.get('link',''))[0];t=e.get('title','');summary=e.get('summary','')
     if u.startswith(('http://','https://')) and same_site(u,r.url) and tags(t+' '+summary):found.append(item(src,t,u,e.get('published') or e.get('updated',''),summary))
   except Exception:log['warnings'].append('RSS不可用，尝试页面新闻列表')
  seen={x['url'] for x in found};candidates=[]
  # A news-like URL plus a meaningful title avoids products, menus, category pages.
  for a in soup.select('a[href]'):
   title=clean(a.get_text(' ',strip=True));u=urldefrag(urljoin(r.url,a['href']))[0]
   if not u.startswith(('http://','https://')) or not same_site(u,r.url) or u==r.url or u in seen:continue
   path=urlparse(u).path
   news=bool(re.search(r'/news(?:/|-|_|room/|info/)|/press|/release|/article|/detail|/lighting_your_dreams/\d+\.html|/20\d{2}[-/]|/\d{4,}(?:/|\.|$)|/p/\d+',path,re.I))
   news=news or bool(a.find(["h2","h3"]) or a.find_parent(["h2","h3"]))
   if not news or not 14<=len(title)<=300 or not tags(title):continue
   if re.search(r'/category/|/tag/|/products?/|/knowledge_centers/',path,re.I):continue
   seen.add(u);candidates.append((title,u,listed_date(a)))
   if len(candidates)>=8:break
  for title,u,pub in candidates:
   x,w=article(src,title,u,pub);found.append(x)
   if w:log['warnings'].append(w)
  found=list({x['url']:x for x in found}.values());log['found']=len(found)
  log['status']='ok' if found else 'empty'
  if not found:log['note']='列表已访问，未匹配到相关新闻；可能需专用接口或栏目适配，不代表该媒体没有报道。'
 except Exception as e:log.update(status='error',errors=[str(e)[:250]])
 log['warnings']=list(dict.fromkeys(log['warnings']));print(src['name'],log['status'],len(found),flush=True)
 return found,log

def main():
 D.mkdir(exist_ok=True);old=json.loads((D/'news.json').read_text(encoding='utf-8')) if (D/'news.json').exists() else [];db={x['url']:x for x in old};logs=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for found,log in pool.map(collect,S):
   logs.append(log)
   for x in found:
    prev=db.get(x['url'],{})
    for k in ('published_at','summary'):
     if not x.get(k):x[k]=prev.get(k,'')
    x['collected_at']=prev.get('collected_at',x['collected_at']);db[x['url']]=x
 items=sorted(db.values(),key=lambda x:x.get('published_at') or '',reverse=True)
 (D/'news.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
 report={'run_at':now(),'timezone_note':'04:00 UTC = 12:00 Asia/Shanghai','source_results':logs,'total_stored':len(items),'configured':len(S),'automatic':sum(x.get('mode')!='manual' for x in S)}
 (D/'collection_log.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Stored',len(items),'sources',len(logs),flush=True)
if __name__=='__main__':main()
