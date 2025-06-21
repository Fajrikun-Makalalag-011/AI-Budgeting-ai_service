from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import re
import os

app = Flask(__name__)
CORS(app) # Ini akan mengizinkan request dari semua origin

# Simple keyword-based classifier
CATEGORY_KEYWORDS = {
    'Food': ['makan', 'nasi', 'kopi', 'resto', 'warung', 'sarapan', 'lunch', 'dinner'],
    'Transport': ['ojek', 'grab', 'gojek', 'angkot', 'bus', 'parkir', 'taksi'],
    'Shopping': ['baju', 'sepatu', 'belanja', 'shopping', 'mall'],
    'Bills': ['listrik', 'pulsa', 'tagihan', 'bayar', 'internet'],
    'Other': []
}

def classify_description(desc):
    desc = desc.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', desc):
                return cat
    return 'Other'

@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    desc = data.get('description', '')
    category = classify_description(desc)
    return jsonify({'category': category})

@app.route('/predict-budget', methods=['POST'])
def predict_budget():
    # Dummy: prediksi budget bulan depan = rata-rata pengeluaran per bulan + 10%
    data = request.json
    transactions = data.get('transactions', [])
    if not transactions:
        return jsonify({'suggested_budget': 0})
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month')['amount'].sum()
    avg = monthly.mean() if not monthly.empty else 0
    suggested = int(avg * 1.1)
    return jsonify({'suggested_budget': suggested})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)