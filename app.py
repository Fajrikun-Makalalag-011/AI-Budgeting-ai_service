from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import re
import os
import google.generativeai as genai
import json

app = Flask(__name__)
CORS(app) # Ini akan mengizinkan request dari semua origin

# Konfigurasi Gemini API
# Pastikan Anda sudah set environment variable GEMINI_API_KEY
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    model = None

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

@app.route('/generate-plan', methods=['POST'])
def generate_plan():
    if model is None:
        return jsonify({"error": "Gemini model is not initialized. Check API Key."}), 500

    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt is missing"}), 400

    try:
        response = model.generate_content(prompt)
        
        # Ekstrak teks dan bersihkan untuk mendapatkan JSON yang valid
        raw_text = response.text
        
        # Pendekatan yang lebih kuat untuk mengekstrak blok kode JSON
        # Menemukan ```json ... ``` dan mengambil isinya
        match = re.search(r'```json\s*([\s\S]+?)\s*```', raw_text)

        if match:
            json_string = match.group(1)
        else:
            # Jika format markdown tidak ditemukan, coba cari array/objek JSON mentah
            # Ini membantu jika AI hanya mengembalikan JSON tanpa markdown
            json_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', raw_text)
            if not json_match:
                print(f"Warning: Could not extract JSON from Gemini response. Raw text: {raw_text}")
                return jsonify({"error": "Failed to parse AI response. No JSON block found.", "details": raw_text}), 500
            json_string = json_match.group(0)

        # Hapus komentar (jika ada) dan coba parse
        json_string = re.sub(r'//.*', '', json_string)
        budget_plan = json.loads(json_string)
        
        return jsonify(budget_plan)

    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON. String attempted: '{json_string}'. Original text: '{raw_text}'")
        return jsonify({"error": f"Invalid JSON format received from AI. Details: {e}", "details": raw_text}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500


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