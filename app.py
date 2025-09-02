import os
import json
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt
import datetime
import pymysql
import requests

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'ai_recipe_db')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
INTRASEND_API_URL = "https://api.intrasend.com/mpesa"
INTRASEND_ACCOUNT = "+254794916644"

def get_db():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

def token_required(f):
    def wrap(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'msg': 'Missing token'}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user = payload
        except:
            return jsonify({'msg': 'Invalid token'}), 401
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    db = get_db()
    with db.cursor() as cur:
        try:
            cur.execute("INSERT INTO users (name, email, password_hash, phone_number) VALUES (%s, %s, %s, %s)",
                        (data['name'], data['email'], pw_hash, data.get('phone_number')))
            db.commit()
            return jsonify({'msg': 'Registered successfully'})
        except pymysql.err.IntegrityError:
            return jsonify({'msg': 'Email already exists'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email=%s", (data['email'],))
        user = cur.fetchone()
        if user and bcrypt.check_password_hash(user['password_hash'], data['password']):
            token = jwt.encode({
                'user_id': user['user_id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({'token': token})
        return jsonify({'msg': 'Invalid credentials'}), 401

@app.route('/api/recipes', methods=['POST'])
@token_required
def get_recipes():
    user_ingredients = request.json.get('ingredients', [])
    if not user_ingredients:
        return jsonify({'msg': 'Missing ingredients'}), 400
    prompt = (f"Suggest 3 creative recipes using the following ingredients: {', '.join(user_ingredients)}. "
              "Include ingredients + cooking steps. Make it simple, affordable, and healthy.")
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        result = r.json()
        recipes = result['choices'][0]['message']['content']
        return jsonify({'recipes': recipes})
    except Exception:
        # Fallback to stored recipes
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM recipes ORDER BY RAND() LIMIT 3")
            fallback_recipes = cur.fetchall()
        return jsonify({'recipes': fallback_recipes, 'msg': 'AI API failed, showing fallback recipes.'})

@app.route('/api/pay', methods=['POST'])
@token_required
def make_payment():
    data = request.json
    user_id = request.user['user_id']
    amount = data.get('amount')
    phone = data.get('phone', INTRASEND_ACCOUNT)
    if not amount:
        return jsonify({'msg': 'Missing amount'}), 400
    payload = {
        "phone_number": phone,
        "amount": amount,
        "account_reference": f"user_{user_id}",
    }
    try:
        r = requests.post(INTRASEND_API_URL, json=payload)
        payment_result = r.json()
        db = get_db()
        with db.cursor() as cur:
            cur.execute("INSERT INTO payments (user_id, amount, payment_method, status) VALUES (%s, %s, %s, %s)",
                        (user_id, amount, 'IntraSend-MPesa', payment_result.get('status', 'PENDING')))
            db.commit()
        return jsonify({'msg': 'Payment initiated', 'result': payment_result})
    except Exception as e:
        return jsonify({'msg': 'Payment API error', 'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
@token_required
def analytics():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT title, COUNT(*) as count FROM recipes GROUP BY title ORDER BY count DESC LIMIT 5")
        popular_recipes = cur.fetchall()
        cur.execute("SELECT status, COUNT(*) as count FROM payments GROUP BY status")
        payments = cur.fetchall()
    return jsonify({
        'popular_recipes': popular_recipes,
        'payments': payments
    })

if __name__ == '__main__':
    app.run(debug=True)