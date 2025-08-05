# markov_absorbing.py
import pandas as pd, numpy as np

FILE = "/Users/bowen/Downloads/整车订单状态指标表.xlsx"
STAGES = [("wish_create_time","Wish"),
          ("intention_payment_time","Intention"),
          ("deposit_payment_time","Deposit"),
          ("lock_time","Lock"),
          ("final_payment_time","Final"),
          ("delivery_date","Delivery")]

print("⏳ loading …")
df = pd.read_excel(FILE, engine="openpyxl")

invalid = (
    (df["deposit_payment_time"].notna()  & df["intention_payment_time"].isna()) |
    (df["lock_time"].notna()             & df["deposit_payment_time"].isna())   |
    (df["final_payment_time"].notna()    & df["lock_time"].isna())             |
    (df["delivery_date"].notna()         & df["final_payment_time"].isna())
)
df = df[~invalid]

def to_path(r):
    p = ["Start"]
    for col, name in STAGES:
        if pd.notna(r[col]): p.append(name)
    p.append("Conversion" if pd.notna(r["delivery_date"]) else "Null")
    return p

paths = df.apply(to_path, axis=1).tolist()
print("✔ paths:", len(paths))

# ---------- transition matrix ----------
states = sorted({s for p in paths for s in p})
idx = {s:i for i,s in enumerate(states)}
n = len(states)
T = np.zeros((n,n))

for p in paths:
    for a,b in zip(p[:-1], p[1:]):
        T[idx[a], idx[b]] += 1
T = T / T.sum(1, keepdims=True, where=T.sum(1,keepdims=True)!=0)

# ---------- helper to compute final conv prob ----------
def conv_prob(mat):
    # split into transient (non-absorbing) and absorbing
    absorb = ["Conversion","Null"]
    trans  = [s for s in states if s not in absorb]
    Q = mat[np.ix_([idx[s] for s in trans], [idx[s] for s in trans])]
    R = mat[np.ix_([idx[s] for s in trans], [idx[s] for s in absorb])]
    N = np.linalg.inv(np.eye(len(Q)) - Q)         # Fundamental matrix
    start_vec = np.zeros(len(trans)); start_vec[trans.index("Start")] = 1
    conv_prob = start_vec @ N @ R                 # [p_to_Conv, p_to_Null]
    return conv_prob[0]                           # probability to Conversion

baseline = conv_prob(T)

effects = {}
for stage in [s for _,s in STAGES]:
    Ti = T.copy()
    # zero out row & column of this stage
    Ti[:, idx[stage]] = 0
    Ti[idx[stage], :] = 0
    # re-normalize each affected row
    row_sum = Ti.sum(1, keepdims=True)
    Ti = np.divide(Ti, row_sum, out=np.zeros_like(Ti), where=row_sum!=0)
    effects[stage] = round((baseline - conv_prob(Ti))*100, 2)   # 百分点

print("\n★ Removal Effect (最终转化率百分点↓)")
for stg, eff in effects.items():
    print(f"{stg:<10}: {eff:+.2f} pp")
