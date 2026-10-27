"""Build a reproducible, synthetic sales analytics portfolio project."""
from pathlib import Path
import csv, json, random, datetime as dt, sqlite3, base64, zipfile
from collections import defaultdict
ROOT=Path(__file__).resolve().parent; ROOT.mkdir(exist_ok=True)
def write(path,text):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
def dump(path,obj):write(path,json.dumps(obj,indent=2))
def csvout(path,rows):
 with (ROOT/path).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rng=random.Random(42)
products=[('Laptop stand','Technology',22000,14000),('Wireless mouse','Technology',14000,8500),('Keyboard','Technology',25000,16000),('Desk lamp','Home & Office',18000,10000),('Office chair','Home & Office',95000,65000),('Storage box','Home & Office',11000,6000),('Backpack','Accessories',28000,16000),('Water bottle','Accessories',9500,4500),('USB hub','Technology',19000,12000)]
states=['Lagos','Abuja','Oyo','Rivers','Ogun','Kano'];channels=['Online','Retail','Wholesale'];raw=[]
for order in range(1,1801):
 day=dt.date(2025,1,1)+dt.timedelta(days=rng.randrange(638))
 state=rng.choices(states,[40,20,12,10,10,8])[0];channel=rng.choices(channels,[45,35,20])[0];cancel=rng.random()<.05
 for line in range(1,rng.randint(1,3)+1):
  product,category,price,cost=rng.choice(products);qty=rng.randint(1,5);discount=rng.choice([0,0,0,5,10,15]);returns=0 if cancel else (rng.randint(1,qty) if rng.random()<.07 else 0)
  raw.append(dict(line_id=f'L{order:04d}-{line}',order_id=f'O{order:04d}',order_date=day.isoformat(),state=state,channel=channel,product=product,category=category,quantity=qty,returned_units=returns,unit_price_ngn=price,unit_cost_ngn=cost,discount_pct=discount,status='Cancelled' if cancel else 'Completed'))
raw.extend([dict(x) for x in raw[:20]])
for i in range(5):
 bad=dict(raw[i]);bad['line_id']=f'BAD-{i}';bad['quantity']=-1;raw.append(bad)
raw[30]['state']=' lagos ';raw[31]['channel']='ONLINE'
csvout('sales_raw.csv',raw)
clean=[];seen=set();rejected=[];duplicates=0
for row in raw:
 if row['line_id'] in seen: duplicates+=1;continue
 seen.add(row['line_id']);row=dict(row);row['state']=row['state'].strip().title();row['channel']=row['channel'].strip().title()
 if row['quantity']<1 or row['returned_units']>row['quantity']:rejected.append(row);continue
 if row['status']=='Cancelled':gross=discount=refund=net=netcost=0
 else:
  gross=row['quantity']*row['unit_price_ngn'];discount=gross*row['discount_pct']//100;refund=row['returned_units']*row['unit_price_ngn']*(100-row['discount_pct'])//100
  net=gross-discount-refund;netcost=(row['quantity']-row['returned_units'])*row['unit_cost_ngn']
 row.update(month=row['order_date'][:7],gross_sales_ngn=gross,discount_ngn=discount,refund_ngn=refund,net_revenue_ngn=net,cost_ngn=netcost,gross_profit_ngn=net-netcost)
 clean.append(row)
csvout('sales_clean.csv',clean);csvout('rejected_rows.csv',rejected)
audit=dict(raw_rows=len(raw),duplicate_rows_removed=duplicates,rejected_rows=len(rejected),clean_rows=len(clean),normalized_labels=2)
dump('quality_report.json',audit)
db=sqlite3.connect(':memory:');cols=list(clean[0]);numeric={k for k,v in clean[0].items() if isinstance(v,int)}
db.execute('CREATE TABLE sales ('+','.join(k+(' INTEGER' if k in numeric else ' TEXT') for k in cols)+')')
db.executemany('INSERT INTO sales VALUES ('+','.join('?' for _ in cols)+')',[[row[k] for k in cols] for row in clean])
sql='''-- SQLite: import sales_clean.csv into a table named sales, or run build_sales.py.
-- Revenue is net of discounts/returns. Cancelled orders contribute zero.
SELECT substr(order_date,1,7) AS month, SUM(net_revenue_ngn) AS net_revenue_ngn,
       SUM(gross_profit_ngn) AS gross_profit_ngn,
       ROUND(100.0*SUM(gross_profit_ngn)/NULLIF(SUM(net_revenue_ngn),0),2) AS gross_margin_pct
FROM sales GROUP BY month ORDER BY month;

SELECT category,SUM(net_revenue_ngn) AS net_revenue_ngn,
       SUM(gross_profit_ngn) AS gross_profit_ngn
FROM sales GROUP BY category ORDER BY net_revenue_ngn DESC;

SELECT channel, COUNT(DISTINCT CASE WHEN status='Completed' THEN order_id END) AS completed_orders,
       SUM(net_revenue_ngn) AS net_revenue_ngn
FROM sales GROUP BY channel ORDER BY net_revenue_ngn DESC;
'''
write('analysis.sql',sql)
monthly=[dict(zip(['month','net_revenue_ngn','gross_profit_ngn','gross_margin_pct'],r)) for r in db.execute(sql.split(';')[0])];csvout('monthly_summary.csv',monthly)
revenue=sum(x['net_revenue_ngn'] for x in clean);profit=sum(x['gross_profit_ngn'] for x in clean);completed={x['order_id'] for x in clean if x['status']=='Completed'}
units=sum(x['quantity'] for x in clean if x['status']=='Completed');returned=sum(x['returned_units'] for x in clean if x['status']=='Completed')
metrics=dict(net_revenue_ngn=revenue,gross_profit_ngn=profit,gross_margin=profit/revenue,completed_orders=len(completed),average_order_value_ngn=revenue/len(completed),returned_unit_rate=returned/units)
dump('metrics.json',metrics)
assert len(raw)==duplicates+len(rejected)+len(clean)
assert len({x['line_id'] for x in clean})==len(clean)
assert all(x['net_revenue_ngn']==x['gross_sales_ngn']-x['discount_ngn']-x['refund_ngn'] for x in clean)
assert db.execute('SELECT SUM(net_revenue_ngn),SUM(gross_profit_ngn) FROM sales').fetchone()==(revenue,profit)
db.close()
measures={'Net Revenue':'SUM(Sales[net_revenue_ngn])','Gross Profit':'SUM(Sales[gross_profit_ngn])','Gross Margin %':'DIVIDE([Gross Profit], [Net Revenue])','Completed Orders':'CALCULATE(DISTINCTCOUNT(Sales[order_id]), Sales[status] = "Completed")','Average Order Value':'DIVIDE([Net Revenue], [Completed Orders])','Returned Unit Rate':'DIVIDE(CALCULATE(SUM(Sales[returned_units]), Sales[status] = "Completed"), CALCULATE(SUM(Sales[quantity]), Sales[status] = "Completed"))'}
write('measures.dax','\n\n'.join(k+' = '+v for k,v in measures.items())+'\n')
base='https://developer.microsoft.com/json-schemas/fabric/'
pb='powerbi/';report='RetailSales.Report';model='RetailSales.SemanticModel'
dump(pb+'RetailSales.pbip',{'$schema':base+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':report}}],'settings':{'enableAutoRecovery':True}})
dump(pb+model+'/definition.pbism',{'$schema':base+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
encoded=base64.b64encode((ROOT/'sales_clean.csv').read_bytes()).decode()
mexpr=['let',f'    Source = Csv.Document(Binary.FromText("{encoded}", BinaryEncoding.Base64), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','    Typed = Table.TransformColumnTypes(Headers, {'+', '.join('{"'+k+'", '+('Int64.Type' if k in numeric else 'type date' if k=='order_date' else 'type text')+'}' for k in cols)+'})','in','    Typed']
table={'name':'Sales','columns':[{'name':k,'dataType':'int64' if k in numeric else 'dateTime' if k=='order_date' else 'string','sourceColumn':k,'summarizeBy':'sum' if k in numeric else 'none'} for k in cols], 'partitions':[{'name':'Sales','mode':'import','source':{'type':'m','expression':mexpr}}], 'measures':[{'name':k,'expression':v,'formatString':'0.0%' if '%' in k or k=='Returned Unit Rate' else '#,0' if k=='Completed Orders' else '"NGN "#,0'} for k,v in measures.items()]}
dump(pb+model+'/model.bim',{'name':'RetailSales','compatibilityLevel':1600,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','tables':[table]}})
dump(pb+report+'/definition.pbir',{'$schema':base+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../'+model}}})
rd=pb+report+'/definition/'
dump(rd+'version.json',{'$schema':base+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'1.0.0'})
dump(rd+'report.json',{'$schema':base+'item/report/definition/report/1.0.0/schema.json','layoutOptimization':'None','themeCollection':{}})
dump(rd+'pages/pages.json',{'$schema':base+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':['overview'],'activePageName':'overview'})
dump(rd+'pages/overview/page.json',{'$schema':base+'item/report/definition/page/1.0.0/schema.json','name':'overview','displayName':'Sales overview | Synthetic data','displayOption':'FitToPage','height':800,'width':1280})
def projection(prop,measure=False):
 return {'field':{('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':'Sales'}},'Property':prop}},'queryRef':'Sales.'+prop}
visuals=[]
for i,name in enumerate(['Net Revenue','Gross Profit','Gross Margin %','Completed Orders','Average Order Value','Returned Unit Rate']):
 visuals.append((f'kpi{i}','card',{'Values':{'projections':[projection(name,True)]}},24+i*208,20,196,140))
for name,typ,col,x,y,w,h in [('monthly','lineChart','month',24,180,800,290),('category','barChart','category',844,180,410,290),('state','barChart','state',24,490,600,280),('channel','columnChart','channel',644,490,610,280)]:
 visuals.append((name,typ,{'Category':{'projections':[projection(col)]},'Y':{'projections':[projection('Net Revenue',True)]}},x,y,w,h))
for name,typ,query,x,y,w,h in visuals:
 dump(rd+f'pages/overview/visuals/{name}/visual.json',{'$schema':base+'item/report/definition/visualContainer/1.0.0/schema.json','name':name,'position':{'x':x,'y':y,'z':1,'width':w,'height':h,'tabOrder':1},'visual':{'visualType':typ,'query':{'queryState':query},'drillFilterOtherVisuals':True}})
dump('theme.json',{'name':'Retail Sales - Dolapo Adeniyi','dataColors':['#167D8D','#5A67D8','#F2A65A','#D1495B'],'background':'#F5F7FA','foreground':'#183349','tableAccent':'#167D8D'})
print(json.dumps({'quality':audit,'metrics':metrics},indent=2))
