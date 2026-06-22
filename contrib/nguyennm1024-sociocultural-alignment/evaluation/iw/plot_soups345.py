#!/usr/bin/env python
"""IW map: base + soups 0.3/0.4/0.5 + Tao GPT models + Vietnam. Dashed distance lines. No title; 'vs' axes."""
import json, csv, sys
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
IW="/workspace/eval/iw"; sys.path.insert(0, IW)
ANS="/workspace/results/iw/answers"; FIG="/workspace/results/iw/figures"
from iw_project import project, ITEMS
coords=json.load(open(f"{IW}/country_coords.json"))
zones={r["country.territory"]:r["Category"] for r in csv.DictReader(open(f"{IW}/s003.csv"))}
ZC={"Catholic Europe":"#9467bd","Protestant Europe":"#1f77b4","English-Speaking":"#2ca02c",
    "Latin America":"#ff7f0e","African-Islamic":"#8c564b","West & South Asia":"#e377c2",
    "Confucian":"#d62728","Orthodox Europe":"#17becf"}
LABEL={"Vietnam","United States","Japan","Sweden","Czechia","China","Germany","Great Britain","Spain",
 "Netherlands","South Korea","Thailand","Indonesia","Australia","France","Italy","Norway","Russia","Canada",
 "Finland","Poland","Greece","Turkey","India","Mexico","Brazil","Argentina","Ukraine","Romania","Hungary",
 "Taiwan ROC","Hong Kong SAR","Slovenia","Estonia","Bulgaria","Serbia","New Zealand","Ireland","Nigeria","Pakistan"}
VN=tuple(coords["Vietnam"]); d=lambda p:((p[0]-VN[0])**2+(p[1]-VN[1])**2)**.5
def proj(tag):
    rows=list(csv.DictReader(open(f"{ANS}/answers_{tag}_tao.csv")))
    pts=[project([float(r[it]) for it in ITEMS]) for r in rows if all(r[it] not in("","None") for it in ITEMS)]
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
def proj_gpt(fn):
    rows=list(csv.DictReader(open(f"{IW}/tao_osf/{fn}")))
    pts=[project([float(r[it]) for it in ITEMS]) for r in rows]
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
BASE=proj("base")
SOUPS=[("soup α=0.3","sw03","#0a7d0a",(-70,16)),("soup α=0.4","sw04","#d95f02",(14,18)),("soup α=0.5","sw05","#7570b3",(14,-20))]
SP={lab:proj(tag) for lab,tag,_,_ in SOUPS}
GPT=[("GPT-3.5","gpt_S1_gpt35.csv"),("GPT-4","gpt_S2_gpt4.csv"),("GPT-4-turbo","gpt_S3_gpt4turbo.csv"),("GPT-4o","gpt_S4_gpt4o.csv")]
GPTP={n:proj_gpt(f) for n,f in GPT}

fig,ax=plt.subplots(figsize=(15,10.5))
ax.axhline(0,color="#ddd",lw=.9,zorder=0); ax.axvline(0,color="#ddd",lw=.9,zorder=0)
for c,(x,y) in coords.items():
    star=(c=="Vietnam")
    ax.scatter(x,y,s=(250 if star else 32),c=("red" if star else ZC.get(zones.get(c,""),"#ccc")),
               marker=("*" if star else "o"),edgecolors="k" if star else "none",lw=.6,alpha=(1 if star else .45),zorder=(6 if star else 2))
    if c in LABEL: ax.annotate(c,(x,y),fontsize=(12 if star else 7.5),fontweight=("bold" if star else "normal"),
                    color=("red" if star else "#555"),xytext=(5,3),textcoords="offset points",zorder=7)
for n,_ in GPT:
    x,y=GPTP[n]; ax.scatter(x,y,s=150,c="#333",marker="s",edgecolors="white",lw=1.2,zorder=8)
    ax.annotate(n,(x,y),fontsize=10,fontweight="bold",color="#333",xytext=(7,5),textcoords="offset points",zorder=9)
ax.scatter(*BASE,s=420,c="black",marker="D",edgecolors="white",lw=2,zorder=10)
ax.annotate("base (Llama-3.2-3B)",BASE,fontsize=13,fontweight="bold",color="black",xytext=(10,8),textcoords="offset points",zorder=11)
for lab,tag,col,off in SOUPS:
    p=SP[lab]
    ax.plot([p[0],VN[0]],[p[1],VN[1]],ls="--",c=col,lw=1.4,alpha=.6,zorder=5)
    ax.scatter(*p,s=300,c=col,marker="D",edgecolors="white",lw=1.8,zorder=12)
    ax.annotate(f"{lab} (d={d(p):.2f})",p,fontsize=11,fontweight="bold",color=col,xytext=off,textcoords="offset points",ha="center",zorder=13)
ax.set_xlabel("Survival  vs  Self-Expression",fontsize=14)
ax.set_ylabel("Traditional  vs  Secular-Rational",fontsize=14)
from matplotlib.lines import Line2D
leg=[Line2D([0],[0],marker='o',color='w',markerfacecolor=v,markersize=8,label=k) for k,v in ZC.items()]
leg+=[Line2D([0],[0],marker='*',color='w',markerfacecolor='red',markersize=13,label='Vietnam'),
      Line2D([0],[0],marker='D',color='w',markerfacecolor='#0a7d0a',markersize=10,label='soups 0.3/0.4/0.5'),
      Line2D([0],[0],marker='s',color='w',markerfacecolor='#333',markersize=9,label='base / GPT models')]
ax.legend(handles=leg,fontsize=9,loc="lower left",framealpha=.92)
ax.grid(True,alpha=.13); fig.tight_layout(); fig.savefig(f"{FIG}/iw_soups345.png",dpi=145)
for lab in SP: print(f"{lab} {tuple(round(v,2) for v in SP[lab])} d={d(SP[lab]):.2f}")
print("WROTE iw_soups345.png")
