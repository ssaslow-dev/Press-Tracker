import openpyxl,csv,sys
a=openpyxl.load_workbook('in.xlsx',read_only=True);b=openpyxl.load_workbook('AJG Coverage - NewsBank STAGED run-mvvcnrpbuuz save 2026-10-30.xlsx',read_only=True)
out=[];sh={}
print(a.sheetnames==b.sheetnames, b.sheetnames)
for n in b.sheetnames:
    A=list(a[n].iter_rows(values_only=True));B=list(b[n].iter_rows(values_only=True))
    hdr=B[0]; ch=0
    for r in range(max(len(A),len(B))):
        ra=A[r] if r<len(A) else (); rb=B[r] if r<len(B) else ()
        for c in range(max(len(ra),len(rb))):
            va=ra[c] if c<len(ra) else None; vb=rb[c] if c<len(rb) else None
            if va!=vb and not(va in(None,'') and vb in(None,'')):
                ch+=1; out.append((n,r+1,hdr[c] if c<len(hdr) else c,'added' if r>=len(A) else ('changed' if va not in(None,'') else 'filled'),va,vb))
    sh[n]=(len(A),len(B),ch)
print(sh)
with open('/tmp/claude-0/-home-claude/989ae3e6-bb40-514f-8289-716f9d98407d/scratchpad/lib/work/out/runsave_changes_2026-10-30.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['sheet','row','column','kind','old','new']);w.writerows(out)
from collections import Counter
print(Counter((o[0],o[3]) for o in out))
for o in out:
    if o[3]=='changed': print(o)
