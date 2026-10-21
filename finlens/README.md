# Finlens: AI Financial Report Analyzer

## Run it
Windows: double-click `run.bat`. Mac/Linux: `./run.sh`. Then open http://localhost:5000
(needs Python 3.9+; first run installs packages). Click "Try the sample report" to see it work immediately.

## Components
| Part | File | Job |
|---|---|---|
| Frontend | `static/index.html`, `style.css`, `app.js` | Upload, results display |
| API server | `app.py` | Flask: `/api/analyze`, `/api/health` |
| Analysis engine | `analyzer.py` | PDF text, figure extraction, ratios, health score, summary |
| ML model | `train_model.py` -> `model/tone_model.joblib` | TF-IDF + logistic regression: risk / growth / neutral sentences |
| Prompt strategies | `prompts.py` | Zero-shot, few-shot, chain-of-thought (the prompt engineering part) |
| Test data | `make_sample.py`, `samples/` | Generates a fictional annual report |

## Optional: AI commentary (prompt engineering mode)
Set an Anthropic key before starting and a style selector appears in the UI:
`set ANTHROPIC_API_KEY=your_key` (Windows) or `export ANTHROPIC_API_KEY=your_key`.
Without a key everything else still works.

## Honest limits
- Tone model is trained on a small synthetic phrase set (about 71% accuracy on held-out phrases). For better results retrain `train_model.py` on Financial PhraseBank.
- Figure extraction relies on standard line labels ("Total assets", "Net profit"). Scanned/image PDFs are not supported.
- Ratio thresholds are generic rules of thumb, not industry-specific.
