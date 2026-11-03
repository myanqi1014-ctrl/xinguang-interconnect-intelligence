"""Merge reviewed public procurement leads without misrepresenting direct-crawl success."""
import json,hashlib
from pathlib import Path
from urllib.parse import urlparse,urldefrag
from datetime import datetime,timezone
from editorial import decorate
R=Path(__file__).resolve().parents[1]
def main():
 path=R/'config/procurement_import.json'
 if not path.exists():return
 sources={s['id']:s for s in json.loads((R/'config/sources.json').read_text(encoding='utf-8'))};data=R/'data/news.json';news=json.loads(data.read_text(encoding='utf-8'));db={x['url']:x for x in news};added=0
 for record in json.loads(path.read_text(encoding='utf-8')):
  src=sources.get(record.get('source_id'),{})
  if src.get('kind')!='tender':continue
  url=urldefrag(record.get('url',''))[0];u=urlparse(url);root=(urlparse(src.get('homepage') or src['url']).hostname or '').removeprefix('www.')
  if u.scheme not in ('http','https') or not ((u.hostname or '')==root or (u.hostname or '').endswith('.'+root)):continue
  if not record.get('title') or not record.get('verification_note'):continue
  x=dict(record,id=hashlib.sha256(url.encode()).hexdigest()[:16],url=url,source_name=src['name'],source_type='招标采购',content_type='招标采购',collected_at=db.get(url,{}).get('collected_at',datetime.now(timezone.utc).isoformat()),ingestion_method='公开检索补充',title_zh=record['title'])
  x=decorate(x)
  if not x['accepted']:continue
  added+=int(url not in db);db[url]=x
 for x in db.values():
  x['company_scope']=sources.get(x.get('source_id'),{}).get('company_scope',x.get('company_scope',''));decorate(x)
 news=sorted(db.values(),key=lambda x:x.get('published_at') or '',reverse=True);data.write_text(json.dumps(news,ensure_ascii=False,indent=2),encoding='utf-8')
 logpath=R/'data/collection_log.json';log=json.loads(logpath.read_text(encoding='utf-8'));log.update(total_stored=len(news),editorial_selected=sum(bool(x.get('accepted')) for x in news),procurement_imported=sum(x.get('ingestion_method')=='公开检索补充' for x in news));logpath.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Procurement leads added:',added)
if __name__=='__main__':main()
