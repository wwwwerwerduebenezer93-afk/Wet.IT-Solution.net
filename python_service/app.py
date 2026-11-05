import base64, io, os
from flask import Flask, jsonify, request
from PIL import Image, ImageStat

app = Flask(__name__)

def fingerprint(img):
    img = img.convert('L').resize((32, 32))
    px = list(img.getdata()); mean = sum(px) / len(px)
    return [1 if p >= mean else 0 for p in px]

@app.post('/verify')
def verify():
    data = request.get_json(silent=True) or {}
    ref = data.get('reference_path', '')
    raw = data.get('candidate_base64', '')
    if not os.path.isfile(ref) or ',' not in raw:
        return jsonify(error='Invalid verification input', verified=False), 400
    try:
        reference = Image.open(ref)
        candidate = Image.open(io.BytesIO(base64.b64decode(raw.split(',', 1)[1])))
        a, b = fingerprint(reference), fingerprint(candidate)
        similarity = sum(x == y for x, y in zip(a, b)) / len(a)
        # Demo threshold; replace with a production face-recognition/liveness provider.
        return jsonify(verified=similarity >= 0.58, similarity=round(similarity, 4), method='perceptual-demo')
    except Exception:
        return jsonify(error='Unreadable image', verified=False), 400

@app.get('/health')
def health(): return jsonify(status='ok')

if __name__ == '__main__': app.run(host='127.0.0.1', port=5001, debug=False)

