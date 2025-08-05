import pandas as pd, numpy as np

FILE = "/Users/bowen/Downloads/整车订单状态指标表.xlsx"

# 1️⃣  读取与方案 B 清洗
df = pd.read_excel(FILE, engine="openpyxl")
jump = (
    (df["deposit_payment_time"].notna()  & df["intention_payment_time"].isna()) |
    (df["lock_time"].notna()             & df["deposit_payment_time"].isna())   |
    (df["final_payment_time"].notna()    & df["lock_time"].isna())             |
    (df["delivery_date"].notna()         & df["final_payment_time"].isna())
)
df = df[~jump]

# 2️⃣  渠道映射函数
def ch(cat):
    if cat == "门店":
        return "STORE"
    elif cat == "总部":
        return "HQ"
    else:
        return "OTHER"

df["ch"] = df["big_channel_name"].map(ch).fillna("OTHER")

# 3️⃣  阶段列
STAGE_COLS = [
    ("wish_create_time",      "Wish"),
    ("intention_payment_time","Intention"),
    ("deposit_payment_time",  "Deposit"),
    ("lock_time",             "Lock"),
    ("final_payment_time",    "Final"),
    ("delivery_date",         "Delivery"),
]

# 4️⃣  构造 “Stage_Channel” 路径
def to_path(r):
    p = ["Start"]
    chan = r["ch"]
    for col, stage in STAGE_COLS:
        if pd.notna(r[col]):
            p.append(f"{stage}_{chan}")
    p.append("Conversion" if pd.notna(r["delivery_date"]) else "Null")
    return p

paths = df.apply(to_path, axis=1).tolist()
print("paths:", len(paths))

# 5️⃣  构建转移矩阵
states = sorted({s for p in paths for s in p})
idx = {s:i for i,s in enumerate(states)}
n = len(states)
T = np.zeros((n,n))
for p in paths:
    for a,b in zip(p[:-1], p[1:]):
        T[idx[a], idx[b]] += 1
row_sum = T.sum(1, keepdims=True)
T = np.divide(T, row_sum, out=np.zeros_like(T), where=row_sum!=0)

# 6️⃣  吸收链函数：返回 Start→Conversion 概率
def conv_prob(mat):
    absorb = ["Conversion","Null"]
    trans  = [s for s in states if s not in absorb]
    Q = mat[np.ix_([idx[s] for s in trans], [idx[s] for s in trans])]
    R = mat[np.ix_([idx[s] for s in trans], [idx[s] for s in absorb])]
    N = np.linalg.inv(np.eye(len(Q)) - Q)
    start = np.zeros(len(trans)); start[trans.index("Start")] = 1
    return (start @ N @ R)[0]          # prob to Conversion

baseline = conv_prob(T)

# 7️⃣  计算 Removal Effect
effects = {}
for stage, _ in STAGE_COLS:            # 五大阶段
    for ch in ["HQ","STORE"]:
        node = f"{_}_{ch}"
        if node not in idx:            # 某渠道无此阶段
            continue
        Ti = T.copy()
        Ti[:, idx[node]] = 0
        Ti[idx[node], :] = 0
        # 行归一
        rsum = Ti.sum(1, keepdims=True)
        Ti = np.divide(Ti, rsum, out=np.zeros_like(Ti), where=rsum!=0)
        effects[node] = round((baseline - conv_prob(Ti))*100, 2)  # 百分点

print("\n★ Removal Effect pp (Stage × Channel)")
for node, eff in sorted(effects.items(), key=lambda x:-x[1]):
    print(f"{node:<15}: {eff:+.2f} pp")
