#!/usr/bin/env python
"""IW map: base + Tapestry(soup0.8, GREEN) + Tao's 4 GPT models. Dashed distance lines base->VN
and Tapestry->VN. No title. Axes use 'vs'. Many country labels."""
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
# many country labels
LABEL={"Vietnam","United States","Japan","Sweden","Czechia","China","Germany","Great Britain","Spain",
 "Netherlands","South Korea","Thailand","Indonesia","Australia","France","Italy","Norway","Russia","Canada",
 "Finland","Denmark","Switzerland","Poland","Greece","Turkey","Iran","Egypt","Nigeria","Pakistan","India",
 "Mexico","Brazil","Argentina","Chile","Ukraine","Romania","Hungary","Taiwan ROC","Hong Kong SAR","Malaysia",
 "Philippines","Bangladesh","Morocco","Jordan","Iraq","Kenya","Ethiopia","New Zealand","Ireland","Slovenia",
 "Estonia","Bulgaria","Serbia","Andorra","Singapore","Zimbabwe","Tunisia","Colombia","Peru","Kazakhstan"}
VN=tuple(coords["Vietnam"]); d=lambda p:((p[0]-VN[0])**2+(p[1]-VN[1])**2)**.5
def proj(tag):
    rows=list(csv.DictReader(open(f"{ANS}/answers_{tag}_tao.csv")))
    pts=[project([float(r[it]) for it in ITEMS]) for r in rows if all(r[it] not in("","None") for it in ITEMS)]
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
def proj_gpt(fn):
    rows=list(csv.DictReader(open(f"{IW}/tao_osf/{fn}")))
    pts=[project([float(r[it]) for it in ITEMS]) for r in rows]
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
BASE=proj("base"); TAP=proj("sw05")
GPT=[("GPT-3.5","gpt_S1_gpt35.csv"),("GPT-4","gpt_S2_gpt4.csv"),
     ("GPT-4-turbo","gpt_S3_gpt4turbo.csv"),("GPT-4o","gpt_S4_gpt4o.csv")]
GPTP={n:proj_gpt(f) for n,f in GPT}

fig,ax=plt.subplots(figsize=(15,10.5))
ax.axhline(0,color="#ddd",lw=.9,zorder=0); ax.axvline(0,color="#ddd",lw=.9,zorder=0)
for c,(x,y) in coords.items():
    star=(c=="Vietnam")
    ax.scatter(x,y,s=(250 if star else 32),c=("red" if star else ZC.get(zones.get(c,""),"#ccc")),
               marker=("*" if star else "o"),edgecolors="k" if star else "none",lw=.6,alpha=(1 if star else .5),zorder=(6 if star else 2))
    if c in LABEL: ax.annotate(c,(x,y),fontsize=(12 if star else 7.5),fontweight=("bold" if star else "normal"),
                    color=("red" if star else "#555"),xytext=(5,3),textcoords="offset points",zorder=7)
# dashed distance lines to Vietnam (label near each model end so they don't collide)
for p,col,t in [(BASE,"black",0.30),(TAP,"#0a7d0a",0.30)]:
    ax.plot([p[0],VN[0]],[p[1],VN[1]],ls="--",c=col,lw=1.8,alpha=.8,zorder=5)
    lx,ly=p[0]+t*(VN[0]-p[0]), p[1]+t*(VN[1]-p[1])
    ax.annotate(f"{d(p):.2f}",(lx,ly),fontsize=12,color=col,fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15",fc="white",ec=col,alpha=.92),zorder=9)
# Tao GPT models (black squares)
for n,_ in GPT:
    x,y=GPTP[n]; ax.scatter(x,y,s=150,c="#333",marker="s",edgecolors="white",lw=1.2,zorder=8)
    ax.annotate(n,(x,y),fontsize=10,fontweight="bold",color="#333",xytext=(7,5),textcoords="offset points",zorder=9)
# base (black diamond)
ax.scatter(*BASE,s=420,c="black",marker="D",edgecolors="white",lw=2,zorder=10)
ax.annotate("base (Llama-3.2-3B)",BASE,fontsize=13,fontweight="bold",color="black",xytext=(10,8),textcoords="offset points",zorder=11)
# Tapestry (green diamond) — label moved up-left, clear of the base->VN dashed line
ax.scatter(*TAP,s=470,c="#0a7d0a",marker="D",edgecolors="white",lw=2,zorder=12)
ax.annotate("Tapestry-Vietnamese",TAP,fontsize=14,fontweight="bold",color="#0a7d0a",xytext=(-78,26),textcoords="offset points",ha="center",zorder=13)
ax.set_xlabel("Survival  vs  Self-Expression Values",fontsize=14)
ax.set_ylabel("Traditional  vs  Secular Values",fontsize=14)
from matplotlib.lines import Line2D
leg=[Line2D([0],[0],marker='o',color='w',markerfacecolor=v,markersize=8,label=k) for k,v in ZC.items()]
leg+=[Line2D([0],[0],marker='*',color='w',markerfacecolor='red',markersize=13,label='Vietnam'),
      Line2D([0],[0],marker='D',color='w',markerfacecolor='#0a7d0a',markersize=11,label='Tapestry-Vietnamese (ours)'),
      Line2D([0],[0],marker='s',color='w',markerfacecolor='#333',markersize=9,label='base / GPT models')]
ax.legend(handles=leg,fontsize=9,loc="lower left",framealpha=.92)
ax.grid(True,alpha=.13); fig.tight_layout(); fig.savefig(f"{FIG}/iw_tapestry_05.png",dpi=145)
print(f"base={tuple(round(v,2) for v in BASE)} d={d(BASE):.2f}; Tapestry={tuple(round(v,2) for v in TAP)} d={d(TAP):.2f}")
for n in GPTP: print(f"  {n}={tuple(round(v,2) for v in GPTP[n])} d={d(GPTP[n]):.2f}")
print("WROTE iw_tapestry_05.png")
