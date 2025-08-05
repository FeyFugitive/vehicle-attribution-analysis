# markov_channel_prov_series.py
# ------------------------------------------
# 依赖：pip install pandas numpy openpyxl
# ------------------------------------------
import pandas as pd, numpy as np, os, json

# === 0. 参数 ===
FILE = "/Users/Bowen/Downloads/整车订单状态指标表.xlsx"   # ← 改成真实路径
TOP_N = 8        # 拆解前 N 省份 / 系列
STAGE_COLS = [
    ("wish_create_time",      "Wish"),
    ("intention_payment_time","Intention"),
    ("deposit_payment_time",  "Deposit"),
    ("lock_time",             "Lock"),
    ("final_payment_time",    "Final"),
    ("delivery_date",         "Delivery"),
]

# ---------- 1. 读数据 + 方案 B 清洗 ----------
print("⏳  loading …")
df = pd.read_excel(FILE, engine="openpyxl")

jump = (
    (df["deposit_payment_time"].notna()  & df["intention_payment_time"].isna()) |
    (df["lock_time"].notna()             & df["deposit_payment_time"].isna())   |
    (df["final_payment_time"].notna()    & df["lock_time"].isna())              |
    (df["delivery_date"].notna()         & df["final_payment_time"].isna())
)
df = df[~jump]

# ---------- 2. 省份 / 系列 Top N 归类 ----------
top_prov   = df["province_name"].value_counts().head(TOP_N).index.tolist()
top_series = df["series"].value_counts().head(TOP_N).index.tolist()

df["prov_cat"]   = df["province_name"].fillna("UNKNOWN").apply(lambda x: x if x in top_prov else "OTHER")
df["series_cat"] = df["series"].fillna("UNKNOWN").apply(lambda x: x if x in top_series else "OTHER")

# ---------- 3. 构造路径函数 ----------
def build_paths(cat_col):
    def row_path(r):
        path = ["Start"]
        cat  = r[cat_col]
        for col, stage in STAGE_COLS:
            if pd.notna(r[col]):
                path.append(f"{stage}_{cat}")
        path.append("Conversion" if pd.notna(r["delivery_date"]) else "Null")
        return path
    return df.apply(row_path, axis=1).tolist()

# ---------- 4. Markov Removal Effect ----------
def removal_effect(paths, test_nodes):
    # 状态集合
    states = sorted({s for p in paths for s in p})
    idx = {s:i for i,s in enumerate(states)}
    n   = len(states)

    # 转移矩阵
    T = np.zeros((n,n))
    for p in paths:
        for a,b in zip(p[:-1], p[1:]):
            T[idx[a], idx[b]] += 1
    row_sum = T.sum(1, keepdims=True)
    T = np.divide(T, row_sum, out=np.zeros_like(T), where=row_sum!=0)

    # 吸收链：prob(Start→Conversion)
    start_i, conv_i = idx["Start"], idx["Conversion"]
    absorb = ["Conversion","Null"]
    trans  = [s for s in states if s not in absorb]
    Q = T[np.ix_([idx[s] for s in trans], [idx[s] for s in trans])]
    R = T[np.ix_([idx[s] for s in trans], [idx[s] for s in absorb])]
    N = np.linalg.inv(np.eye(len(Q)) - Q)
    v = np.zeros(len(trans)); v[trans.index("Start")] = 1
    baseline = (v @ N @ R)[0]      # baseline conversion prob

    results = []
    for node in test_nodes:
        if node not in idx:            # 该节点在路径中不存在
            continue
        Ti = T.copy()
        Ti[:, idx[node]] = 0
        Ti[idx[node], :] = 0
        rs = Ti.sum(1, keepdims=True)
        Ti = np.divide(Ti, rs, out=np.zeros_like(Ti), where=rs!=0)

        # 重新计算 conv prob
        Q2 = Ti[np.ix_([idx[s] for s in trans], [idx[s] for s in trans])]
        R2 = Ti[np.ix_([idx[s] for s in trans], [idx[s] for s in absorb])]
        N2 = np.linalg.inv(np.eye(len(Q2)) - Q2)
        new_conv = (v @ N2 @ R2)[0]

        results.append((node, round((baseline - new_conv)*100, 2)))   # 百分点
    return results

# ---------- 5. Province Stage Markov ----------
paths_prov = build_paths("prov_cat")
nodes_prov = [f"{stage}_{prov}" for prov in top_prov for _,stage in STAGE_COLS[1:]]  # Skip Wish if想省略可改
eff_prov   = removal_effect(paths_prov, nodes_prov)
prov_df = pd.DataFrame([{"Province": n.split("_")[-1],
                         "Stage": "_".join(n.split("_")[:-1]),
                         "Removal_Effect_pp": eff} for n,eff in eff_prov])
prov_df.to_csv("province_stage_removal.csv", index=False)
print("\n✔  Province Stage Removal → province_stage_removal.csv")

# ---------- 6. Series Stage Markov ----------
paths_ser = build_paths("series_cat")
nodes_ser = [f"{stage}_{ser}" for ser in top_series for _,stage in STAGE_COLS[1:]]
eff_ser   = removal_effect(paths_ser, nodes_ser)
ser_df = pd.DataFrame([{"Series": n.split("_")[-1],
                        "Stage": "_".join(n.split("_")[:-1]),
                        "Removal_Effect_pp": eff} for n,eff in eff_ser])
ser_df.to_csv("series_stage_removal.csv", index=False)
print("✔  Series  Stage Removal → series_stage_removal.csv\n")

print("Top Province contributions:")
print(prov_df.sort_values("Removal_Effect_pp", ascending=False).head(12))
