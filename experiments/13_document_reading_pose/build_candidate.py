"""Diagnostic registration of expression donors to the document-reading master.

Candidate-only tooling: do not publish, do not modify the neutral master.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MASTER = ROOT / "static/poses/document_reading/neutral.png"
OUT = HERE / "candidate_review"
OUT.mkdir(exist_ok=True)


def load(p):
    return np.asarray(Image.open(p).convert("RGBA"))


master = load(MASTER)
assert master.shape == (1448,1086,4)
box = (480, 90, 686, 260)
head = (409, 5, 709, 280)


def align_to_master(donor, label):
    # Restrict correspondences to stable head and hair detail; expressions are free to change.
    def keypoints(im):
        x0,y0,x1,y1=head
        grey=cv2.cvtColor(im[y0:y1,x0:x1,:3], cv2.COLOR_RGB2GRAY)
        sift = cv2.SIFT_create(nfeatures=3500, contrastThreshold=0.012)
        kp,des=sift.detectAndCompute(grey,None)
        for p in kp: p.pt = (p.pt[0]+x0,p.pt[1]+y0)
        return kp,des
    src_kp,src_d=keypoints(master)
    don_kp,don_d=keypoints(donor)
    matcher=cv2.BFMatcher()
    paired=matcher.knnMatch(don_d,src_d,k=2)
    good=[m for m,n in paired if m.distance < 0.77*n.distance]
    D=np.float32([don_kp[m.queryIdx].pt for m in good])
    S=np.float32([src_kp[m.trainIdx].pt for m in good])
    M,inliers=cv2.estimateAffinePartial2D(D,S,method=cv2.RANSAC,ransacReprojThreshold=2.5,confidence=.995)
    if M is None:raise RuntimeError(label+" insufficient registration")
    keep=inliers.ravel()>0
    print(label,"matches",len(good),"inliers",int(keep.sum()),"matrix",M.tolist())
    residual=np.linalg.norm((D[keep] @ M[:,:2].T + M[:,2])-S[keep], axis=1)
    print(label,"residual median",float(np.median(residual)), "maximum",float(np.max(residual)))
    h,w=master.shape[:2]
    rgba = cv2.warpAffine(donor,M,(w,h),flags=cv2.INTER_LINEAR)
    return rgba,M,D[keep],S[keep]


def shown(im, crop=box, magnification=3):
    part = Image.fromarray(im).crop(crop).convert("RGBA")
    bg=Image.new("RGBA",part.size,"#eeeeee")
    bg.alpha_composite(part)
    return bg.convert("RGB").resize((part.width*magnification,part.height*magnification),Image.Resampling.NEAREST)


all_panels=[("Neutral",shown(master))]
for name in ("happy","shocked"):
    donor=load(HERE/"assets"/(name+"_donor.png"))
    aligned,M,D,S=align_to_master(donor,name)
    all_panels.extend([("Original "+name,shown(donor)),("Aligned "+name,shown(aligned))])
    # 50% overlap makes double contours in unchanged anatomy visible.
    overlay=master.copy()
    overlay[:,:,:3]=np.clip(master[:,:,:3].astype(float)*.5 + aligned[:,:,:3].astype(float)*.5,0,255).astype("uint8")
    all_panels.append(("Overlay "+name,shown(overlay)))
    Image.fromarray(aligned).crop(box).save(OUT/(name+"_aligned_face.png"))
    # Diagnostic anchor/match marks on the source and aligned donor, sample for visual checking.
    marks=shown(master,crop=head,magnification=2)
    d=ImageDraw.Draw(marks)
    for xy in S[:50]:
        x,y=xy
        d.ellipse((2*(x-head[0])-2,2*(y-head[1])-2,2*(x-head[0])+2,2*(y-head[1])+2), fill="#17cf4d")
    marks.save(OUT/(name+"_matches.png"))

width=max(p.width for _,p in all_panels)
height=max(p.height for _,p in all_panels)
board=Image.new("RGB",(width*4,height*2+24),"#eeeeee")
draw=ImageDraw.Draw(board)
for i,(title,im) in enumerate(all_panels):
    x=(i%4)*width;y=(i//4)*(height+12)
    board.paste(im,(x,y+12))
    draw.text((x+8,y),title,fill="#000000")
board.save(OUT/"registration_compare.png")
print("saved", sorted(p.name for p in OUT.glob("*.png")))
