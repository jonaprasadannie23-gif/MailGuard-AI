# ProbMail — Intelligent Spam & Phishing Email Detection System

ProbMail is a complete, production-grade cybersecurity AI platform built for probabilistic email classification and threat explainability. Combining natural language preprocessing, statistical corpus analysis, **Chi-Square ($\chi^2$) feature selection**, and **Multinomial Naive Bayes**, ProbMail detects malicious spam and phishing lures while ensuring **zero data leakage** between training and inference.

---

## Technical Responsibilities & Architecture

ProbMail centers on three core machine learning engineering responsibilities:

```
Raw CSV / Email Text
         │
         ▼
┌─────────────────────────────────┐
│  1. Data Preprocessing          │  HTML unescaping & tag removal, URL/Email/Currency
│     & Data Hygiene              │  tokenization, label mapping, deduplication
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  2. Statistical Analysis        │  Class imbalance ratio, length metrics (char/word),
│     & Corpus Profiling          │  lexical frequencies, and syntactic characteristics
└────────────────┬────────────────┘
                 │
                 ▼  [Stratified Train/Test Split (80/20)]
┌─────────────────────────────────┐
│  3. Chi-Square (χ²) Feature     │  Non-negative TF-IDF matrix (L2 normalized) fitted
│     Selection (SelectKBest)     │  strictly on X_train; p-value significance (p < 0.05)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  4. Multinomial Naive Bayes     │  Laplace smoothing (α = 1.0), posterior probabilities,
│     Classification & Evaluation │  per-class Precision/Recall/F1, and Confusion Matrix
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  5. Explainable Inference &     │  Real-time email scanning, influential token highlights,
│     SQLite Audit Persistence    │  privacy-preserving snippet logging (probmail.db)
└─────────────────────────────────┘
```

---

## 1. Technical Components Breakdown

### 1. Data Preprocessing (`backend/ml/preprocessing.py`)
- **HTML entity decoding & tag stripping**: Normalizes `&amp;`, `&lt;`, and strips `<p>`, `<a>`, `<div>` tags without losing anchor text.
- **Security-specific semantic tokenization**:
  - URLs $\to$ `url_token`
  - Email addresses $\to$ `email_token`
  - Currency symbols (`$`, `€`, `£`, `¥`) $\to$ `currency_token`
  - Floating numbers and integers $\to$ `num_token`
- **Label Normalization**: Transparently maps binary target labels (`spam`/`ham`, `1`/`0`, `legitimate`/`phishing`) with explicit ambiguity validation.
- **Dataset Hygiene Audit**: Tracks missing texts, missing labels, and duplicate records safely removed.

### 2. Statistical Analysis (`backend/ml/statistics.py`)
- **Class Imbalance Quantification**: Calculates $N_{\text{majority}} : N_{\text{minority}}$ ratio and assesses whether stratified sampling is required.
- **Descriptive Length Distributions**: Computes mean, median, min, max, and standard deviation for character and word counts across both Ham and Spam partitions.
- **Discriminative Lexical Profiling**: Compares top 15 non-stopword token frequencies between classes.
- **Behavioral Signatures**: Measures ALL-CAPS uppercase character ratios, hyperlink presence percentages, and psychological urgency keyword densities.

### 3. Chi-Square Feature Selection (`backend/ml/feature_selection.py`)
- **Non-negative Feature Transformation**: Uses sublinear TF-IDF vectorization with L2 normalization to fulfill non-negativity requirements for the Chi-Square test.
- **Pearson's Chi-Square Test of Independence**:
  $$\chi^2 = \sum \frac{(O - E)^2}{E}$$
  Tests the null hypothesis ($H_0$) that a word's occurrence is independent of the email class label.
- **Score vs. $p$-value Distinction**:
  - The $\chi^2$ score represents the magnitude of divergence from independence.
  - The $p$-value represents the probability of observing that divergence by chance under $H_0$. Features are certified statistically significant only when $p < 0.05$ (or $p < 0.001$ for highly significant features).
- **Zero Data Leakage**: Vectorizer vocabulary extraction and Chi-Square selection are fitted strictly inside `X_train` during training.
=======
# ProbMail — Intelligent Spam & Ham Email Security Platform

ProbMail is a modern, high-performance cybersecurity web application built with **React 18 / Vite / TypeScript / Tailwind CSS** for probabilistic email classification, threat detection, and explainable AI.

It features a mathematically grounded **Multinomial Naive Bayes** classification engine coupled with **Pearson's Chi-Square ($\chi^2$) Feature Selection**, rigorous stratified evaluation, exploratory data analysis (EDA), and zero-dependency PDF security scan report generation.

---

## Key Features

1. **Email Security Scanner**:
   - Real-time text analysis or `.eml`/`.txt` file upload.
   - Circular animated Risk Score Gauge ($0–100$).
   - Exact Bayesian posterior probabilities: $P(\text{Spam} \mid \text{Words})$ vs. $P(\text{Ham} \mid \text{Words})$.
   - Grounded warning sign detection (Urgent Action Pressure, Credential Phishing, Financial Incentive Claims).
   - Chi-Square feature contribution breakdown with log-odds impact badges.
   - Actionable cybersecurity precautions tailored to the evaluated risk tier.
   - **1-Click PDF Security Scan Report Generation & Download**.

2. **Security Dashboard & KPIs**:
   - Live platform metrics: total emails scanned, spam detected, ham detected, and percentage breakdown.
   - Scanner status indicator.
   - 3-step threat analysis workflow overview.
   - Recent scanned emails table with quick inspection links.

3. **Scan History & Audit Log**:
   - Persistent audit log of all scanned emails.
   - Real-time search by subject line or content snippet.
   - Filter by All, Spam, or Ham.
   - Detailed modal preview with risk score and posterior probability bars.
   - Direct PDF export per audit record.
   - Log erasure with safety confirmation.

4. **Dataset Management & Hygiene**:
   - Ingestion of custom CSV datasets and preloaded benchmark dataset.
   - Interactive column remapping (`text_column`, `label_column`, `subject_column`).
   - Automated hygiene audit: duplicate detection, missing value stripping, and label normalization.
   - Tabular dataset preview with column breakdown.

5. **Exploratory Data Analysis (EDA) & Statistics**:
   - Descriptive length distributions: Mean, Median, Standard Deviation ($\sigma$), Min, and Max for character counts and word counts.
   - Empirical class imbalance analysis and stratified sampling justification.
   - Top 15 frequent terms per class with stopword filtering.
   - Behavioral email signatures: uppercase percentage, hyperlink presence, currency presence, and urgency keyword frequency.
   - Interactive length comparison and class distribution charts using Recharts.

6. **Chi-Square ($\chi^2$) Feature Selection**:
   - Non-negative TF-IDF matrix with $n$-grams (1, 2).
   - Statistical test of independence against the target class ($df = 1$).
   - Exact $p$-value computation and significance certification ($p < 0.05$).
   - Interactive $k$-best selector ($k = 15, 30, 50, 100$).
   - Class tendency classification (Spam Indicator vs. Ham Indicator).

7. **Model Training & Hyperparameter Tuning**:
   - Configurable $k$-best features slider, stratified train/test split ratio (80/20, 75/25, 70/30), and Laplace smoothing ($\alpha$).
   - Real-time training progress tracking and animated status updates.
   - Active model metadata display.

8. **Model Evaluation & Confusion Matrix**:
   - Held-out test set validation with zero data leakage.
   - Comprehensive metrics: Accuracy, Macro/Weighted Precision, Recall, and F1-Scores.
   - $2 \times 2$ Confusion Matrix with True Negatives, False Positives (Type I), False Negatives (Type II), and True Positives.
   - Cybersecurity trade-off analysis explaining false alarm vs. breach risk.

---

## Technology Stack

### Backend
- **Python 3.13 / 3.11+**
- **Flask & Flask-CORS**: REST API routing and cross-origin security.
- **PostgreSQL (Neon / Supabase / RDS)**: Persistent production database via `DATABASE_URL` / `POSTGRES_URL`.
- **SQLite3**: Privacy-preserving audit logs and zero-configuration local development.
- **scikit-learn**: `TfidfVectorizer`, `SelectKBest`, `chi2`, `MultinomialNB`, `train_test_split`, `metrics`.
- **pandas & NumPy & SciPy**: Dataset hygiene, matrix calculations, and descriptive statistics.
- **Joblib**: Atomic pipeline artifact serialization.
- **pytest**: Automated unit and integration testing suite.

### Frontend
- **React 19 with Vite**
- **TypeScript**: Complete type safety for API contracts and ML metrics.
- **Tailwind CSS**: Custom cybersecurity palette (Dark Navy `#0B0F19`, Slate `#111827`, Cyan `#06B6D4`, Emerald `#10B981`, Rose `#F43F5E`).
- **Lucide React**: Security, model, and analytics iconography.
- **Recharts**: Responsive confusion matrix, class distribution, and length charts.

---

## Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Node.js 18+ (Tested on Node.js 24)
- npm or pnpm

### 1. Clone & Setup Backend
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Frontend
```bash
# From workspace root
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build
```

---

## Running the Application

### Option A: Unified Production Server (Recommended)
Because the Flask application serves the built React frontend directly from `frontend/dist`, you can run the entire platform with one command:

```bash
cd backend
venv\Scripts\python app.py
```
Open your browser at **`http://127.0.0.1:5000`**.

### Option B: Development Mode (Hot-Reloading)
Run backend and frontend concurrently in two terminals:

**Terminal 1 (Flask API):**
```bash
cd backend
venv\Scripts\python app.py
```

**Terminal 2 (Vite Dev Server):**
```bash
cd frontend
npm run dev
```
Open your browser at **`http://localhost:5173`**.

---

## Automated Testing Suite

ProbMail includes 14 automated backend tests covering dataset validation, text cleaning, label mapping, statistics, Chi-Square significance, leakage prevention, persistence, and REST endpoints:

```bash
# From project root
backend\venv\Scripts\pytest -v
```

Expected output:
```
backend/tests/test_api_endpoints.py::test_health_endpoint PASSED
backend/tests/test_api_endpoints.py::test_dashboard_endpoint PASSED
backend/tests/test_api_endpoints.py::test_dataset_summary_and_sample_load PASSED
backend/tests/test_api_endpoints.py::test_analytics_endpoints PASSED
backend/tests/test_api_endpoints.py::test_predict_and_prediction_history_flow PASSED
backend/tests/test_api_endpoints.py::test_invalid_predict_input PASSED
backend/tests/test_feature_selection.py::test_chi_square_selection_and_pvalues PASSED
backend/tests/test_model_pipeline.py::test_pipeline_train_leakage_prevention_and_predict PASSED
backend/tests/test_preprocessing.py::test_clean_text_basic PASSED
backend/tests/test_preprocessing.py::test_clean_text_html_stripping PASSED
backend/tests/test_combine_subject_and_body PASSED
backend/tests/test_normalize_label PASSED
backend/tests/test_validate_and_preprocess_dataset_synthetic PASSED
backend/tests/test_statistics.py::test_statistics_calculation PASSED
============================== 14 passed in 5.54s ==============================
=======
- **Framework**: React 18
- **Build Tool**: Vite 6
- **Language**: TypeScript (Strict type safety)
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Reports**: Native Client-Side PDF 1.4 Generation Engine

---

## Development & Build Commands

```bash
# Install dependencies
npm install

# Start Vite dev server on port 3000
npm run dev

# Build production bundle with TypeScript type-checking
npm run build

# Preview production build on port 3000
npm run preview
```

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status and model status |
| `GET` | `/api/dashboard` | Real-time scan counts, accuracy, and recent predictions |
| `POST` | `/api/dataset/upload` | Upload CSV dataset with column mapping |
| `GET` | `/api/dataset/summary` | Active dataset metadata, preview, and cleaning audit |
| `POST` | `/api/dataset/load-sample` | 1-Click load of bundled benchmark email dataset |
| `POST` | `/api/dataset/remap` | Update active text and label column mappings |
| `GET` | `/api/analytics/statistics` | Class imbalance, length distributions, and characteristics |
| `GET` | `/api/analytics/chi-square` | Top $k$ Chi-Square features, $\chi^2$ scores, and $p$-values |
| `POST` | `/api/model/train` | Asynchronous pipeline training with genuine job tracking |
| `GET` | `/api/model/status` | Real-time training progress and step messages |
| `GET` | `/api/model/evaluation` | Held-out test evaluation report, confusion matrix, per-class metrics |
| `POST` | `/api/predict` | Scan raw email text or file upload; logs to SQLite |
| `GET` | `/api/predictions/history` | Retrieve stored scan audit records |
| `DELETE` | `/api/predictions/history` | Erase stored scan records from SQLite |

---

## University Viva & Project Defense Guide

### Q1: Why is Accuracy insufficient on an imbalanced email dataset?
**A:** If 90% of incoming emails are legitimate (Ham) and 10% are spam, a trivial dummy classifier that predicts "Ham" for every email achieves 90% accuracy while failing to detect a single security threat. In security applications, Precision (minimizing false alarms / Type I errors) and Recall (minimizing missed attacks / Type II errors) are critical, making **Macro F1-Score** the necessary evaluation benchmark.

### Q2: What is the exact difference between a Chi-Square score and a $p$-value?
**A:** The $\chi^2$ score measures the quantitative distance between observed word occurrences and expected occurrences assuming independence. The $p$-value measures the probability that this distance occurred purely by random sampling noise under the null hypothesis ($H_0$). A high $\chi^2$ score is only statistically conclusive if its $p$-value satisfies $p < 0.05$.

### Q3: How did you prevent data leakage during feature selection?
**A:** In naive implementations, developers apply TF-IDF and Chi-Square selection to the entire dataset before splitting into train/test sets, which leaks test set vocabulary and frequency statistics into the model. In ProbMail, the data is split first using stratified sampling, and the Scikit-Learn `Pipeline([('tfidf', ...), ('chi2', ...), ('nb', ...)])` is fitted strictly on `X_train`. The held-out `X_test` is only transformed during evaluation.

### Q4: Why use Multinomial Naive Bayes rather than Gaussian Naive Bayes?
**A:** Text data represented by TF-IDF or token frequencies consists of discrete non-negative counts and frequencies. Gaussian Naive Bayes assumes a continuous bell-curve distribution with negative-infinity support, which violates word count reality. Multinomial Naive Bayes models the multinomial distribution of discrete features, making it mathematically suited for text classification.

---

## License & Academic Attribution
Developed as an academic demonstration and cybersecurity AI project.
Licensed under the MIT License.
