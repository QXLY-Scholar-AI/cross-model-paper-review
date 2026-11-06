"""OpenAI-compatible transport for agent-coordinated cross-review; never stores keys."""
import argparse, concurrent.futures, difflib, json, re, sys, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['probe','review','cross','draft','recheck']);p.add_argument('--config',required=True);p.add_argument('--paper',required=True);p.add_argument('--out',required=True);p.add_argument('--revision');a=p.parse_args()
 cfg=json.loads(Path(a.config).read_text(encoding='utf-8-sig'));out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 models=cfg['models'];assert len(models)==2 and len({x['name'] for x in models})==2
 paper=Path(a.paper).read_text(encoding='utf-8-sig');snapshot=out/'00_原稿.md'
 if snapshot.exists() and snapshot.read_text(encoding='utf-8')!=paper:raise ValueError('稿件与已有工作目录不一致，请使用新目录')
 snapshot.write_text(paper,encoding='utf-8')
 def saved(stage,name):
  f=out/f'{stage}_{name}.md'
  if not f.is_file():raise ValueError(f'缺少有效上一步输出 {f.name}')
  return f.read_text(encoding='utf-8')
 def request(m,prompt):
  text=Path(m['key_file']).read_text(encoding='utf-8-sig').strip();match=re.search(r'sk-[A-Za-z0-9_-]{12,}',text)
  if not match:raise ValueError(f"{m['name']}密钥未识别")
  key=match.group();body={'model':m['model'],'messages':[{'role':'user','content':prompt}],'reasoning_effort':m.get('effort','low'),'max_tokens':int(cfg.get('max_tokens',5000))}
  for attempt in range(1,3):
   record={'stage':a.stage,'attempt':attempt,'requested_model':m['model'],'requested_effort':body['reasoning_effort'],'at':datetime.now(timezone.utc).isoformat()}
   try:
    req=urllib.request.Request(m['url'],data=json.dumps(body,ensure_ascii=False).encode('utf-8'),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'});res=urllib.request.urlopen(req,timeout=180);data=json.loads(res.read());record['http_status']=res.status;record['returned_model']=data.get('model');record['usage']=data.get('usage');choice=(data.get('choices') or [{}])[0];record['finish_reason']=choice.get('finish_reason');answer=choice.get('message',{}).get('content') or '';record['chars']=len(answer)
    valid=bool(answer.strip()) and record['finish_reason']=='stop'
    if valid:(out/f"{a.stage}_{m['name']}.md").write_text(answer,encoding='utf-8')
    elif answer:(out/f"{a.stage}_{m['name']}_attempt{attempt}_partial.md").write_text(answer,encoding='utf-8')
   except urllib.error.HTTPError as ex:
    record['http_status']=ex.code;valid=False
    try:
     data=json.loads(ex.read());msg=str(data.get('error',{}).get('message',''));record['error']=msg.replace(key,'[REDACTED]')[:300]
    except Exception:record['error']='HTTP error'
   except Exception as ex:record['error_type']=type(ex).__name__;valid=False
   (out/f"{a.stage}_{m['name']}_attempt{attempt}.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
   print(a.stage,m['name'],'http',record.get('http_status'),'finish',record.get('finish_reason'),'chars',record.get('chars',0),flush=True)
   if valid:return True
   if record.get('finish_reason')=='length' or (record.get('http_status')==200 and not record.get('chars')):body['max_tokens']*=2
   else:return False
  return False
 names=[m['name'] for m in models];prompts={}
 for m in models:
  name=m['name'];other=next(x for x in names if x!=name)
  if a.stage=='probe':prompt='请只回复：连接成功。'
  elif a.stage=='review':prompt='独立审阅以下研究短文，按原句或位置、问题及理由、严重程度、所需证据、具体修改建议给出意见。不虚构数据或文献。\n【原稿】\n'+paper
  elif a.stage=='cross':prompt='对照原稿，逐项评价对方意见：认同、部分认同或不认同并说明理由。指出需要复查的分歧，不虚构证据。\n【原稿】\n'+paper+'\n【自己的首审】\n'+saved('review',name)+'\n【对方首审】\n'+saved('review',other)
  elif a.stage=='draft':prompt='根据原稿、两位首审和互评，给出完整候选修订稿。保留原研究目的；新增方法建议须标明为建议；不添加虚构事实或文献。只输出修改稿。\n【原稿】\n'+paper+'\n【自己的首审】\n'+saved('review',name)+'\n【对方首审】\n'+saved('review',other)+'\n【自己的互评】\n'+saved('cross',name)+'\n【对方互评】\n'+saved('cross',other)
  else:
   if not a.revision:raise ValueError('复审需提供协调者核对后的统一稿件')
   revision=Path(a.revision).read_text(encoding='utf-8-sig');prompt='对照原稿和你的首轮意见复审修改稿，逐项标记已解决、部分解决、未解决或待证据；检查是否改变原意、数据、引用或加入虚构内容。指出具体句子。\n【原稿】\n'+paper+'\n【你的首审】\n'+saved('review',name)+'\n【统一修订稿】\n'+revision
  prompts[name]=prompt
  (out/f'{a.stage}_{name}_输入.md').write_text(prompt,encoding='utf-8')
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  jobs=[pool.submit(request,m,prompts[m['name']]) for m in models];ok=[j.result() for j in jobs]
 if not all(ok):print('阶段未完成；保留结果，停止后续环节。');return 2
 return 0
if __name__=='__main__':sys.exit(main())
