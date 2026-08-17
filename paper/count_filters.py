import pandas as pd

df = pd.read_csv("data/archive/postings.csv", usecols=["description"])
print("total postings:      ", len(df))

df = df.dropna(subset=["description"])
print("non-empty description:", len(df))

df = df[df["description"].str.len().between(1500, 6000)]
print("after length filter: ", len(df))

df = df.drop_duplicates(subset=["description"])
print("after deduplication: ", len(df))