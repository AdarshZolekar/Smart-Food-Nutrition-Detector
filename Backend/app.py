import os, tempfile, json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from model_clip import FoodZeroShot

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(APP_DIR, 'foods.csv')
LABELS_PATH = os.path.join(APP_DIR, 'labels.json')

app = Flask(__name__, static_folder=None)
CORS(app)

# Load data
foods = pd.read_csv(CSV_PATH)
# Normalize helper
def norm(s):
    return str(s).strip().lower()

# Build lookup by any alias -> canonical food_name
alias_to_name = {}
for _, r in foods.iterrows():
    base = norm(r['food_name'])
    alias_to_name[base] = base
    if 'aliases' in foods.columns and isinstance(r.get('aliases', ''), str):
        for a in r['aliases'].split(';'):
            a = norm(a)
            if a:
                alias_to_name[a] = base

# Image model
zs = FoodZeroShot(LABELS_PATH)

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/api/search')
def search():
    q = norm(request.args.get('q', ''))
    if not q:
        return jsonify([])
    # match on food_name or aliases contains token
    mask = (
        foods['food_name'].str.lower().str.contains(q, na=False)
        | foods.get('aliases', '').astype(str).str.lower().str.contains(q, na=False)
    )
    out = foods.loc[mask].copy()
    # group by canonical name to avoid duplicates via aliases
    out['canonical'] = out['food_name'].str.lower()
    out = (
        out.sort_values('food_name')
           .drop_duplicates(subset=['canonical'])
           .drop(columns=['canonical'])
    )
    return out.to_json(orient='records')

@app.post('/api/predict')
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'no image'}), 400
    file = request.files['image']
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, file.filename)
        file.save(path)
        top = zs.predict(path, topk=5)
    # map best label to canonical food_name
    best = top[0]['label']
    canonical = alias_to_name.get(best, best)
    row = foods[foods['food_name'].str.lower() == canonical].head(1)
    if row.empty:
        return jsonify({'candidates': top, 'match': None, 'nutrition': None})
    nutrition = row.to_dict(orient='records')[0]
    return jsonify({'candidates': top, 'match': canonical, 'nutrition': nutrition})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))