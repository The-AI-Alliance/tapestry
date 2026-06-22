#!/usr/bin/env python
"""Visualize the v3 alpha sweep on the IW map, highlighting soup 0.8. All projected from
their answer CSVs via the bit-exact iw_project. x=Survival<->Self-Expression, y=Trad<->Secular."""
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
LABEL={"Vietnam","United States","Japan","Sweden","Czechia","China","Germany","Great Britain",
       "Spain","Netherlands","South Korea","Thailand","Indonesia","Australia","France","Italy","Slovenia"}
VN=tuple(coords["Vietnam"]); d=lambda p:((p[0]-VN[0])**2+(p[1]-VN[1])**2)**.5
def proj_csv(tag):
    rows=list(csv.DictReader(open(f"{ANS}/answers_{tag}_tao.csv")))
    pts=[project([float(r[it]) for it in ITEMS]) for r in rows if all(r[it] not in("","None") for it in ITEMS)]
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
# (label, tag, alpha, color, marker, size, highlight)
PTS=[("base", "base", 0.0, "#888", "D", 230, False),
     ("soup α=0.3","sw03",0.3,"#1f77b4","s",230,False),
     ("soup α=0.5","sw05",0.5,"#ff7f0e","s",230,False),
     ("soup α=0.8","sw08",0.8,"magenta","D",430,True),
     ("pure IW (α=1.0)","iwv3",1.0,"black","D",260,False)]
P={lab:proj_csv(tag) for lab,tag,*_ in PTS}

fig,ax=plt.subplots(figsize=(14,10))
ax.axhline(0,color="#ddd",lw=.9,zorder=0); ax.axvline(0,color="#ddd",lw=.9,zorder=0)
for c,(x,y) in coords.items():
    star=(c=="Vietnam")
    ax.scatter(x,y,s=(240 if star else 32),c=("red" if star else ZC.get(zones.get(c,""),"#ccc")),
               marker=("*" if star else "o"),edgecolors="k" if star else "none",lw=.6,alpha=(1 if star else .42),zorder=(6 if star else 2))
    if c in LABEL: ax.annotate(c,(x,y),fontsize=(11 if star else 8),fontweight=("bold" if star else "normal"),
                    color=("red" if star else "#555"),xytext=(5,3),textcoords="offset points",zorder=7)
# trajectory line across the alpha sweep (1.0 -> 0.8 -> 0.5 -> 0.3)
traj=[P["pure IW (α=1.0)"],P["soup α=0.8"],P["soup α=0.5"],P["soup α=0.3"]]
ax.plot([p[0] for p in traj],[p[1] for p in traj],color="gray",ls="--",lw=1.2,alpha=.6,zorder=4)
for lab,tag,alpha,col,mk,sz,hi in PTS:
    p=P[lab]
    ax.scatter(*p,s=sz,c=col,marker=mk,edgecolors="white",lw=(2.2 if hi else 1.5),zorder=(10 if hi else 9))
    ax.annotate(f"{lab}  (d={d(p):.2f})",p,fontsize=(12 if hi else 10),fontweight="bold",color=col,
                xytext=(9,6 if not hi else -16),textcoords="offset points",zorder=11)
# distance line for 0.8
p8=P["soup α=0.8"]; ax.plot([p8[0],VN[0]],[p8[1],VN[1]],ls=":",c="magenta",lw=1.6,alpha=.7,zorder=5)
ax.set_xlabel("Survival  ←————→  Self-Expression       (PC1)",fontsize=13)
ax.set_ylabel("Traditional  ←————→  Secular-Rational       (PC2)",fontsize=13)
ax.set_title("v3 soup alpha sweep on the IW map — soup α=0.8 highlighted (closest to Vietnam, d=1.25; God held at 6)\n"
             "dashed = alpha trajectory (pure IW → 0.8 → 0.5 → 0.3). ★=Vietnam",fontsize=10.5)
from matplotlib.lines import Line2D
leg=[Line2D([0],[0],marker='o',color='w',markerfacecolor=v,markersize=8,label=k) for k,v in ZC.items()]
leg+=[Line2D([0],[0],marker='*',color='w',markerfacecolor='red',markersize=13,label='Vietnam (target)')]
ax.legend(handles=leg,fontsize=8.5,loc="lower left",framealpha=.92)
ax.grid(True,alpha=.13); fig.tight_layout(); fig.savefig(f"{FIG}/iw_v3_sweep.png",dpi=145)
for lab in P: print(f"{lab:18s} ({P[lab][0]:+.2f},{P[lab][1]:+.2f}) d={d(P[lab]):.2f}")
print("WROTE iw_v3_sweep.png")
