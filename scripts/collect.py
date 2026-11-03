import json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin,urlparse
import requests,feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dp
R=Path(__file__).resolve().parents[1]; D=R/"data"; S=json.loads((R/"config/sources.json").read_text(encoding="utf-8"))
K={"AI算力":["AI infrastructure","AI data center","accelerated computing","GPU cluster","AI算力"],"光模块":["optical transceiver","800G","1.6T","400G","光模块"],"硅光":["silicon photonics","硅光"],"CPO":["co-packaged optics","CPO","共封装光学"],"光芯片/器件":["optical engine","laser","photonic integrated circuit","optical component","光芯片","光器件"],"数据中心互联":["data center interconnect","DCI","optical interconnect","interconnect","光互联"],"网络与交换":["Ethernet switch","switch ASIC","networking","SerDes","交换芯片"]}
H={"User-Agent":"Mozilla/5.0 XinguangIntelBot/1.0"}
def tags(s):
 l=s.lower();return [k for k,v in K.items() if any(w.lower() in l for w in v)]
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
   r=requests.get(src["url"],headers=H,timeout=25);r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
   feeds=[urljoin(r.url,x.get("href")) for x in soup.select('link[rel~="alternate"][href]') if "rss" in (x.get("type") or "").lower() or "atom" in (x.get("type") or "").lower()]
   for feed in feeds[:4]:
    f=feedparser.parse(feed)
    for e in f.entries[:80]:
     title=e.get("title","").strip();url=e.get("link","");summary=e.get("summary","")
     if title and url and tags(title+" "+summary):found.append(item(src,title,url,e.get("published") or e.get("updated",""),summary))
   if not found:
    for a in soup.select("a[href]"):
     title=" ".join(a.get_text(" ",strip=True).split());url=urljoin(r.url,a["href"])
     if len(title)>=12 and len(title)<=250 and urlparse(url).netloc==urlparse(r.url).netloc and tags(title):
      found.append(item(src,title,url))
     if len(found)>=40:break
  except Exception as e:errors.append(str(e)[:250])
  for x in found:
   if x["url"] not in db:db[x["url"]]=x
  logs.append({"source":src["name"],"found":len(found),"errors":errors})
 D.mkdir(exist_ok=True);items=sorted(db.values(),key=lambda x:x.get("published_at") or x.get("collected_at",""),reverse=True)[:3000]
 (D/"news.json").write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8")
 (D/"collection_log.json").write_text(json.dumps({"run_at":datetime.now(timezone.utc).isoformat(),"timezone_note":"04:00 UTC = 12:00 Asia/Shanghai","source_results":logs,"total_stored":len(items)},ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps(logs,ensure_ascii=False))
if __name__=="__main__":main()