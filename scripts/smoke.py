#!/usr/bin/env python3
"""Posta stored-template/name migration + renderer; never sends external mail.
The 0.18 migration changes old labels to display_name and derives name. We retain
and verify the same template ID, description and label across that migration.
"""
import hashlib,json,os,pathlib,re,secrets,urllib.request,urllib.error
b=(os.environ.get('BASE_URL_POSTA') or os.environ['BASE_URL']).rstrip('/');phase=os.environ['SMOKE_PHASE']
assert phase in ('boot','upgrade','redeploy')
p=pathlib.Path(__file__).with_name('state-'+hashlib.sha256(b.encode()).hexdigest()[:20]+'.json')
def api(path,method='GET',body=None,headers=None,expected=(200,)):
 h={'Accept':'application/json','Content-Type':'application/json'};h.update(headers or {})
 req=urllib.request.Request(b+path,method=method,headers=h,data=None if body is None else json.dumps(body).encode())
 try:r=urllib.request.urlopen(req,timeout=60)
 except urllib.error.HTTPError as e:r=e
 with r:
  assert r.code in expected,f'{method} {path} status {r.code}'
  raw=r.read()
  return json.loads(raw) if raw else None
def data(x):
 assert isinstance(x,dict) and 'data' in x,'API data shape'
 return x['data']
def rows(x):
 x=data(x)
 if isinstance(x,list):return x
 for key in ('items','workspaces','data'):
  if isinstance(x,dict) and isinstance(x.get(key),list):return x[key]
 raise AssertionError('workspace list shape')
creds={'email':os.environ['ADMIN_EMAIL'],'password':os.environ['ADMIN_PASSWORD']}
auth=data(api('/api/v1/auth/login','POST',creds));token=auth.get('token') or auth.get('access_token');assert isinstance(token,str) and token,'no login token'
h={'Authorization':'Bearer '+token}
api('/api/v1/auth/login','POST',{**creds,'password':'wrong-'+creds['password']},expected=(400,401,403))
workspaces=rows(api('/api/v1/workspaces',headers=h));assert workspaces,'bootstrap workspace absent'
if p.exists():
 s=json.loads(p.read_text());assert any(str(w['id'])==str(s['workspace']) for w in workspaces),'seed workspace absent'
else:
 assert phase=='boot','missing boot seed; refusing to recreate migrated template'
 s={'workspace':workspaces[0]['id'],'label':'Railway Validation '+secrets.token_hex(5)}
h['X-Posta-Workspace-Id']=str(s['workspace'])
base='/api/v1/workspaces/current/templates'
if 'template' not in s:
 assert phase=='boot','seed template ID missing'
 template=data(api(base,'POST',{'name':s['label'],'description':'durable Railway template','sample_data':'{}','default_language':'en'},h,expected=(200,201)))
 s['template']=template['id']
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(s));tmp.chmod(0o600);tmp.replace(p)
template=data(api(base+'/'+str(s['template']),headers=h))
assert str(template['id'])==str(s['template']) and template['description']=='durable Railway template','template identity/content lost'
if 'display_name' in template:
 assert template['display_name']==s['label'],'migration lost original display label'
 assert template['name']==re.sub('[^a-z0-9]+','-',s['label'].lower()).strip('-'),'migration derived wrong stable name'
else:assert template['name']==s['label'],'old template label changed'
preview=data(api(base+'/preview','POST',{'subject_template':'Hello {{name}}','html_template':'<p>Hello {{name}}</p>','text_template':'Hello {{name}}','template_data':{'name':'Railway'}},h))
assert preview['subject']=='Hello Railway' and 'Hello Railway' in preview['html'],'renderer result'
api(base,headers={'Authorization':'Bearer invalid-'+token},expected=(401,403))
print(json.dumps({'ok':True,'phase':phase,'stored_template':True,'name_migration_verified':'display_name' in template,'renderer':True,'external_delivery_tested':False}))
