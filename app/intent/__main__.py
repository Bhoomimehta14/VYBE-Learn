"""python -m app.intent  ->  evaluate, then train and save the intent head.

Prints numbers for the report: held-out accuracy of transfer learning (frozen
pretrained embeddings + small head) versus a baseline with no pretrained
knowledge (TF-IDF + the same kind of head), including how each behaves when
only a few labelled examples per intent are available.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold, train_test_split

from app.intent import embedder, model


def _subsample(texts, labels, per_class, seed):
    rng = np.random.default_rng(seed)
    keep = []
    for intent in sorted(set(labels)):
        idx = [i for i, l in enumerate(labels) if l == intent]
        keep.extend(rng.choice(idx, size=min(per_class, len(idx)), replace=False))
    return [texts[i] for i in keep], [labels[i] for i in keep]


def main() -> None:
    texts, labels = model.dataset()
    X = embedder.embed(texts)
    if X is None:
        raise SystemExit("embedding model unavailable - install fastembed and check your connection")
    y = np.array(labels)
    print(f"{len(texts)} labelled questions, {len(set(labels))} intents\n")

    # 1) Cross-validated accuracy, transfer vs. baseline.
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    t_scores, b_scores = [], []
    for tr, te in skf.split(X, y):
        t_scores.append(accuracy_score(y[te], model.new_head().fit(X[tr], y[tr]).predict(X[te])))
        tf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        Xtr = tf.fit_transform([texts[i] for i in tr])
        base = LogisticRegression(C=10.0, max_iter=2000).fit(Xtr, y[tr])
        b_scores.append(accuracy_score(y[te], base.predict(tf.transform([texts[i] for i in te]))))
    print("5-fold accuracy")
    print(f"  transfer (pretrained embeddings + head): {np.mean(t_scores):.1%}")
    print(f"  baseline (TF-IDF, no pretrained model):  {np.mean(b_scores):.1%}\n")

    # 2) Few-shot: the real point of transfer learning.
    tr_idx, te_idx = train_test_split(range(len(texts)), test_size=0.3, stratify=y, random_state=1)
    tr_texts = [texts[i] for i in tr_idx]
    tr_labels = [labels[i] for i in tr_idx]
    te_texts = [texts[i] for i in te_idx]
    te_y = y[list(te_idx)]
    Xte = X[list(te_idx)]
    print("Accuracy with only N labelled examples per intent (avg of 5 draws)")
    print("  N    transfer   baseline")
    for n in (2, 4, 8, 16):
        ts, bs = [], []
        for seed in range(5):
            sub_t, sub_l = _subsample(tr_texts, tr_labels, n, seed)
            ts.append(accuracy_score(te_y, model.new_head().fit(embedder.embed(sub_t), sub_l).predict(Xte)))
            tf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            base = LogisticRegression(C=10.0, max_iter=2000).fit(tf.fit_transform(sub_t), sub_l)
            bs.append(accuracy_score(te_y, base.predict(tf.transform(te_texts))))
        print(f"  {n:<4} {np.mean(ts):>8.1%}   {np.mean(bs):>8.1%}")

    # 3) Per-intent report on the held-out split, then train on everything and save.
    head = model.new_head().fit(X[list(tr_idx)], np.array(tr_labels))
    print("\nHeld-out report (30% split)")
    print(classification_report(te_y, head.predict(Xte), zero_division=0))

    model.train_and_save()
    print(f"Saved trained head to {model.HEAD_PATH}")


if __name__ == "__main__":
    main()
