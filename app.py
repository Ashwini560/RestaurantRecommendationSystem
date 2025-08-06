from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import re
app = Flask(__name__, static_folder='static')  
app.secret_key = 'your_secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cuisine = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    ratings = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(200), nullable=False)
def create_tables():
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    query = request.args.get('query', '')
    search_by = request.args.get('search_by', 'names')
    recommendations = get_recommendations(query, search_by) if query else []
    return render_template('index.html', recommendations=recommendations, query=query, search_by=search_by)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('login'))
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')
@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    if request.method == 'POST':
        query = request.form.get('query')
        search_by = request.form.get('search_by', 'names')
        recommendations = get_recommendations(query, search_by)
        return render_template('index.html', recommendations=recommendations, query=query, search_by=search_by)
    return render_template('index.html', recommendations=None)
def get_recommendations(query, search_by):
    try:
        df = pd.read_csv("HyderabadResturants.csv", on_bad_lines='skip')
        query = query.strip().lower()

        if 'price' in df.columns:
            df['price_cleaned'] = (
                df['price'].astype(str)
                .str.replace(r'[^\d]', '', regex=True)
                .replace('', '0')
                .astype(int)
            )

        if search_by == 'name':
            filtered = df[df['name'].str.lower().str.contains(query, na=False)]

        elif search_by == 'cuisine':
            filtered = df[df['cuisine'].str.lower().str.contains(query, na=False)]

        elif search_by == 'price':
            try:
                price_val = int(query)
                if price_val <= 500:
                    filtered = df[df['price_cleaned'] <= 500]
                elif price_val <= 1000:
                    filtered = df[(df['price_cleaned'] > 500) & (df['price_cleaned'] <= 1000)]
                elif price_val <= 1500:
                    filtered = df[(df['price_cleaned'] > 1000) & (df['price_cleaned'] <= 1500)]
                elif price_val <= 2000:
                    filtered = df[(df['price_cleaned'] > 1500) & (df['price_cleaned'] <= 2000)]
                elif price_val <= 2500:
                    filtered = df[(df['price_cleaned'] > 2000) & (df['price_cleaned'] <= 2500)]
                elif price_val <= 3000:
                    filtered = df[(df['price_cleaned'] > 2500) & (df['price_cleaned'] <= 3000)]
                else:
                    filtered = df[df['price_cleaned'] > 3000]
            except ValueError:
                filtered = pd.DataFrame()

        elif search_by == 'ratings':
            filtered = df[df['ratings'].astype(str).str.contains(query, na=False)]

        else:
            filtered = pd.DataFrame()

        return filtered[['link', 'name', 'ratings', 'cuisine', 'price']].head(10).to_dict(orient='records')
    
    except Exception as e:
        print("Error in get_recommendations:", e)
        return []
def exact_price_match(query, price_value):
    try:
        price_value = re.sub(r'[^\d]', '', str(price_value)) 
        query = str(query).strip()  
        print(f"Matching price: query = {query}, price_value = {price_value}")
        if '-' in price_value:
            price_range = re.findall(r'\d+', price_value)
            min_price, max_price = map(int, price_range)
            print(f"Price range: {min_price} - {max_price}, Query: {query}")
            return min_price <= int(query) <= max_price
        return query == price_value

    except Exception as e:
        print(f"Error in price matching: {e}")
    return False
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)