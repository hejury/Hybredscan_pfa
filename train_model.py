import pandas as pd, pickle, os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

CSV = os.path.expanduser("~/pfe/dataset.csv")
MODEL = os.path.expanduser("~/pfe/model.pkl")

df = pd.read_csv(CSV)
print("Dataset :", df.shape)
print(df["label"].value_counts().to_dict(), "(0=sain, 1=malveillant)\n")

X = df.drop("label", axis=1)
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y)

clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
clf.fit(X_train, y_train)
pred = clf.predict(X_test)

print("Matrice de confusion :")
print(confusion_matrix(y_test, pred))
print("\n", classification_report(y_test, pred, target_names=["sain","malveillant"]))

imp = sorted(zip(X.columns, clf.feature_importances_), key=lambda t: -t[1])[:10]
print("Top 10 features :")
for n, v in imp:
    print("  %-25s %.4f" % (n, v))

pickle.dump({"model": clf, "features": list(X.columns)}, open(MODEL, "wb"))
print("\nModele sauvegarde :", MODEL)
