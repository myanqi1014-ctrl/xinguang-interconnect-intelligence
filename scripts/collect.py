import json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin,urlparse
import requests,feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dp
R=Path(__file__).resolve().parents[1]; D=R/"data"; S=json.loads((R/"config/sources.json").read_text(encoding="utf-8"))
K={"AI算力":["AI infrastructure","AI data center","accelerated computing","GPU cluster","AI算力"],"光模块":["optical transceiver","800G","1.6T","400G","光模块","高速光互联","高速光互连"],"硅光":["silicon photonics","硅光"],"NPO":["NPO","near-packaged optics","近封装"],"CPO":["co-packaged optics","CPO","共封装光学"],"光芯片/器件":["optical engine","laser","photonic integrated circuit","optical component","光芯片","光器件"],"数据中心互联":["data center interconnect","DCI","optical interconnect","interconnect","光互联"],"网络与交换":["Ethernet switch","switch ASIC","networking","SerDes","交换芯片"]}
H={"User-Agent":"Mozilla/5.0 XinguangIntelBot/1.0"}
def tags(s):
 l=s.lower();return [k for k,v in K.items() if any((re.search(r"(?<![a-z0-9])"+re.escape(w.lower())+r"(?![a-z0-9])",l) if w.isascii() else w in l) for w in v)]
def dt(s):
 try:
  x=dp.parse(s);return (x if x.tzinfo else x.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()
 except:return ""
def item(src,title,url,pub="",summary=""):
 return {"id":hashlib.sha256(url.encode()).hexdigest()[:16],"source_id":src["id"],"source_name":src["name"],"source_type":"企业官方发布","title":title,"url":url,"published_at":dt(pub),"summary":BeautifulSoup(summary,"html.parser").get_text(" ",strip=True)[:600],"tags":tags(title+" "+summary),"collected_at":datetime.now(timezone.utc).isoformat()}
def main():
 old=json.loads((D/"news.json").read_text()) if (D/"news.json").exists() else []; db={x["url"]:x for x in old}; logs=[]
 for src in S:
  found=[]; errors=[]
  try:
   r=requests.get(src["url"],headers=H,timeout=25);r.raise_for_status(); r.encoding=r.apparent_encoding; soup=BeautifulSoup(r.text,"html.parser")
   if re.search(r"slot88|slot thailand|casino",soup.title.get_text() if soup.title else "",re.I):raise ValueError("来源返回异常内容，已停止采集，请人工核验官网")
   if len(r.content)<1000 or soup.select_one('iframe[src*="captcha"],script[src*="challenge"]'):raise ValueError("页面受访问保护或未返回新闻正文")
   feeds=[urljoin(r.url,x.get("href")) for x in soup.select('link[rel~="alternate"][href]') if "rss" in (x.get("type") or "").lower() or "atom" in (x.get("type") or "").lower()]
   for feed in feeds[:4]:
    fr=requests.get(feed,headers=H,timeout=20);fr.raise_for_status();f=feedparser.parse(fr.content)
    for e in f.entries[:80]:
     title=e.get("title","").strip();url=e.get("link","");summary=e.get("summary","")
     if title and url and tags(title+" "+summary):found.append(item(src,title,url,e.get("published") or e.get("updated",""),summary))
   if not found:
    seen=set()
    for a in soup.select("a[href]"):
     title=" ".join(a.get_text(" ",strip=True).split());url=urljoin(r.url,a["href"])
     if 12<=len(title)<=250 and urlparse(url).netloc.split(".")[-2:]==urlparse(r.url).netloc.split(".")[-2:] and url!=r.url and re.search(r"/news/|/news-|/newsroom/|/newsinfo/|/press|/release|/article|/detail|/xinwen|/lighting_your_dreams/\d+\.html",url,re.I) and tags(title):
      if url in seen:continue
      seen.add(url)
      pub=""; summary=""
      listed=re.search(r"20[12]\d[-年/.]\d{1,2}[-月/.]\d{1,2}",title)
      if listed:pub=re.sub(r"[年月/.]","-",listed.group()).strip("-")
      if not pub:
       container=a
       for level in range(3):
        container=container.parent
        if not container:break
        text=container.get_text(" ",strip=True)
        candidate=re.search(r"20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\b\d{1,2}/\d{1,2}/\d{2,4}\b|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+20\d{2}",text,re.I)
        if candidate:pub=candidate.group();break
      try:
       detail=requests.get(url,headers=H,timeout=8);detail.raise_for_status();detail.encoding=detail.apparent_encoding; page=BeautifulSoup(detail.text,"html.parser")
       meta=page.select_one('meta[property="article:published_time"],meta[name="date"],meta[name="pubdate"]');time=page.select_one("time")
       if meta:pub=meta.get("content","")
       elif time:pub=time.get("datetime") or time.get_text(" ",strip=True)
       else:
        body=(page.select_one("article") or page.select_one("main") or page).get_text(" ",strip=True)
        m=re.search(r"20[12]\d[-年/.]\d{1,2}[-月/.]\d{1,2}",body)
        if not m:m=re.search(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}",body,re.I)
        if m:pub=re.sub(r"[年月/.]","-",m.group()).strip("-")
       desc=page.select_one('meta[name="description"],meta[property="og:description"]')
       if desc:summary=desc.get("content","")[:500]

      except Exception:pass
      found.append(item(src,title,url,pub,summary))
     if len(found)>=12:break
  except Exception as e:errors.append(str(e)[:250])
  for x in found:
   previous=db.get(x["url"],{})
   for key in ("published_at","summary"):
    if not x.get(key):x[key]=previous.get(key,"")
   x["collected_at"]=previous.get("collected_at",x["collected_at"])
   db[x["url"]]=x
  logs.append({"source":src["name"],"found":len(found),"errors":errors,"status":"error" if errors else ("ok" if found else "empty"),"url":src["url"]})
 D.mkdir(exist_ok=True);items=sorted(db.values(),key=lambda x:x.get("published_at") or x.get("collected_at",""),reverse=True)
 (D/"news.json").write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8")
 (D/"collection_log.json").write_text(json.dumps({"run_at":datetime.now(timezone.utc).isoformat(),"timezone_note":"04:00 UTC = 12:00 Asia/Shanghai","source_results":logs,"total_stored":len(items)},ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps(logs,ensure_ascii=False))
if __name__=="__main__":main()