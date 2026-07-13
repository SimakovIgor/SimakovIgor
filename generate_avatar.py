from PIL import Image
import numpy as np, json, colorsys
W=64; L,T,R,B=0.05,0.02,0.95,0.9; CR=0.62; EDGE=4; SCALE=0.30; FLOOR=0.055; GAMMA=0.9  # CR=0.62 keeps the true egg/oval aspect (0.5 stretched it into a ball)
ramp="@%#*+=-:. "
im=Image.open("avatar.png").convert("RGB"); iw,ih=im.size
im=im.crop((int(L*iw),int(T*ih),int(R*iw),int(B*ih)))
cw,ch=im.size; H=max(1,int(W*(ch/cw)*CR))
rgb=np.asarray(im.resize((W,H),Image.LANCZOS),dtype=np.float32)/255.0
g=np.asarray(im.convert("L").resize((W,H),Image.LANCZOS),dtype=np.float32)/255.0
bg=np.concatenate([g[:,:EDGE],g[:,-EDGE:]],axis=1).mean(axis=1,keepdims=True)
d=np.clip((np.abs(g-bg)-FLOOR)/SCALE,0,1)**GAMMA
idx=np.clip(((1-d)*(len(ramp)-1)).round().astype(int),0,len(ramp)-1)

def boost(r,gg,b):
    h,s,v=colorsys.rgb_to_hsv(r,gg,b)
    s=min(1.0,s*1.18+0.05); v=min(1.0,v*1.05+0.02)   # vivid raw; theme tweaks brightness later
    r,gg,b=colorsys.hsv_to_rgb(h,s,v)
    return "#%02x%02x%02x"%(int(r*255),int(gg*255),int(b*255))

rows=[]
for y in range(H):
    row=[]
    for x in range(W):
        ch_=ramp[idx[y,x]]
        if ch_==" " or d[y,x]<0.06:
            row.append([" ",None]); continue
        r,gg,b=rgb[y,x]
        row.append([ch_,boost(float(r),float(gg),float(b))])
    rows.append(row)
# trim empty top/bottom rows
def blank(r): return all(c[0]==" " for c in r)
while rows and blank(rows[0]): rows.pop(0)
while rows and blank(rows[-1]): rows.pop()
# right-trim trailing spaces
for r in rows:
    while r and r[-1][0]==" ": r.pop()
json.dump(rows,open("face.json","w"))
print("rows",len(rows),"cols",max(len(r) for r in rows))
# ascii preview to eyeball shape
print("\n".join("".join(c[0] for c in r) for r in rows))
