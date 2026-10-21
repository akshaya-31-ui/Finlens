"""Trains the sentence-tone classifier (risk / growth / neutral) used by the analyzer.
Run:  python train_model.py     ->  writes model/tone_model.joblib
"""
import itertools, random, joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report

SUBJECTS = ["The company", "Management", "Our business", "The group", "During the year, we",
            "In the current period, the company", "The board", "Our segment"]
PHRASES = {
 "risk": ["reported a net loss compared with a profit last year", "faces significant liquidity risk and uncertainty",
  "has substantial doubt about its ability to continue as a going concern", "saw margins decline due to rising input costs",
  "is exposed to litigation and regulatory penalties", "recorded a goodwill impairment charge",
  "experienced a sharp drop in demand and falling revenue", "carries high debt and may breach loan covenants",
  "is dependent on a small number of customers who may reduce orders", "warned of inflation, supply disruption and currency volatility",
  "increased provisions for bad debts and defaults", "reported weaker cash flow and a deteriorating working capital position"],
 "growth": ["achieved record revenue and strong profit growth", "expanded into new markets with rising customer demand",
  "improved operating margins through cost efficiency", "reduced debt and strengthened the balance sheet",
  "reported higher cash flow and increased dividends", "launched new products that drove double-digit sales growth",
  "gained market share and grew its customer base", "delivered earnings above expectations and raised guidance",
  "invested in capacity expansion to support future growth", "saw net income rise significantly year over year",
  "secured major contracts and a growing order backlog", "benefited from strong demand and improved profitability"],
 "neutral": ["is incorporated and headquartered in the country of registration", "prepared these statements in accordance with applicable accounting standards",
  "operates through several business segments", "held its annual general meeting during the period",
  "employed staff across multiple locations", "appointed an independent auditor for the financial year",
  "describes its accounting policies in the notes to the statements", "has offices and manufacturing facilities in several regions",
  "maintains a board with audit and remuneration committees", "reports amounts in millions unless otherwise stated",
  "disclosed related-party transactions as required", "completed the review of its internal controls"],
}
PHRASES["risk"] += ["reported declining sales and a widening loss", "faces adverse market conditions and competitive pressure",
 "recognised write-downs and increased impairment losses", "saw costs escalate while profits fell",
 "is subject to cyber security threats and operational disruption", "reported lower earnings and reduced margins",
 "faces uncertainty around tariffs, defaults and credit risk", "suffered a downturn with falling orders and layoffs",
 "disclosed a material weakness and an ongoing investigation", "reported rising borrowings and heavy interest burden"]
PHRASES["growth"] += ["reported increased sales and rising profits", "benefited from favourable market conditions and robust demand",
 "recognised strong earnings and improved returns", "saw revenue climb as profits expanded",
 "strengthened its position with successful acquisitions and innovation", "reported higher earnings and widening margins",
 "enjoyed opportunities from new contracts and record orders", "achieved an upturn with rising orders and hiring",
 "reported effective controls and a clean audit with strong results", "reported falling borrowings and lower interest costs"]
PHRASES["neutral"] += ["presents consolidated financial statements for the financial year", "has registered offices at the stated address",
 "follows the reporting framework adopted by the board", "provides segment information in the notes",
 "lists its shares on the stock exchange", "discloses the number of employees by region",
 "includes the directors' report and the auditor's statement", "reports figures rounded to the nearest million",
 "describes the composition of its committees", "summarises key accounting estimates and judgements"]
def build(idx):
    X, y = [], []
    for label, ps in PHRASES.items():
        for s, p in itertools.product(SUBJECTS, [ps[i] for i in idx]):
            X.append(f"{s} {p}."); y.append(label)
    return X, y

if __name__ == "__main__":
    random.seed(7)
    # hold out 6 phrases per class so evaluation is not just memorised templates
    Xtr, ytr = build(range(16)); Xte, yte = build(range(16, 22))
    pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                         LogisticRegression(max_iter=1000, C=4.0))
    pipe.fit(Xtr, ytr)
    print(classification_report(yte, pipe.predict(Xte), digits=3))
    Xall, yall = build(range(22)); pipe.fit(Xall, yall)   # final model uses everything
    joblib.dump(pipe, "model/tone_model.joblib"); print("saved model/tone_model.joblib")
