"""Static preview from synthetic data; not a Power BI screenshot."""
from pathlib import Path
import csv, json
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
ROOT=Path(__file__).resolve().parent
rows=list(csv.DictReader((ROOT/'sales_clean.csv').open()))
m=json.loads((ROOT/'metrics.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#DDE5EC','axes.labelcolor':'#5D7184','xtick.color':'#5D7184','ytick.color':'#5D7184'})
fig=plt.figure(figsize=(16,10),facecolor='#F3F6FA')
fig.text(.045,.947,'RETAIL INTELLIGENCE',fontsize=11,weight='bold',color='#167D8D')
fig.text(.045,.904,'Sales performance overview',fontsize=28,weight='bold',color='#17334A')
fig.text(.045,.873,'JAN 2025 - SEP 2026   /   NGN   /   Synthetic portfolio demonstration',fontsize=10,color='#64788A')
cards=[('NET REVENUE',f"NGN {m['net_revenue_ngn']/1e6:,.2f}m"),('GROSS PROFIT',f"NGN {m['gross_profit_ngn']/1e6:,.2f}m"),('GROSS MARGIN',f"{m['gross_margin']:.1%}"),('COMPLETED ORDERS',f"{m['completed_orders']:,}"),('AVG. ORDER VALUE',f"NGN {m['average_order_value_ngn']/1000:.1f}k"),('RETURNED UNITS',f"{m['returned_unit_rate']:.1%}")]
for i,(label,value) in enumerate(cards):
 ax=fig.add_axes([.045+i*.155,.735,.143,.1],facecolor='white');ax.set_xticks([]);ax.set_yticks([])
 for spine in ax.spines.values():spine.set_visible(False)
 ax.text(.08,.73,label,transform=ax.transAxes,fontsize=9,color='#64788A');ax.text(.08,.25,value,transform=ax.transAxes,fontsize=17,weight='bold',color='#17334A')
def group(key):
 d=defaultdict(int)
 for r in rows:d[r[key]]+=int(r['net_revenue_ngn'])
 return d
def panel(rect,title):
 ax=fig.add_axes(rect,facecolor='white');ax.set_title(title,loc='left',pad=18,fontsize=12,weight='bold',color='#17334A');return ax
d=group('month');months=sorted(d);ax=panel([.065,.425,.535,.235],'Monthly net revenue')
ax.plot(range(len(months)),[d[k]/1e6 for k in months],color='#167D8D',lw=2.8,marker='o',ms=3);ax.fill_between(range(len(months)),[d[k]/1e6 for k in months],alpha=.07,color='#167D8D');ax.set_xticks(list(range(0,len(months),3)));ax.set_xticklabels([months[i] for i in range(0,len(months),3)]);ax.set_ylabel('NGN million');ax.grid(axis='y',alpha=.15)
for key,rect,title in [('category',[.685,.425,.265,.235],'Revenue by category'),('state',[.065,.105,.535,.23],'Revenue by state'),('channel',[.685,.105,.265,.23],'Revenue by channel')]:
 d=group(key);keys=sorted(d,key=d.get);ax=panel(rect,title);ax.barh(keys,[d[k]/1e6 for k in keys],height=.55,color='#167D8D');ax.set_xlabel('NGN million');ax.grid(axis='x',alpha=.12)
 ax.tick_params(axis='y',labelsize=9)
fig.text(.045,.035,'DOLAPO ADENIYI   |   Python + SQL + Power BI project',color='#64788A',fontsize=9)
fig.text(.62,.035,'Static data preview; Power BI Desktop validation pending',color='#64788A',fontsize=9)
fig.savefig(ROOT/'dashboard_preview.png',dpi=140,facecolor=fig.get_facecolor());plt.close(fig)
