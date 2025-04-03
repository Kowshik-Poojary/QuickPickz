from flask import Blueprint, render_template, jsonify
from flask import request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User,Product,Order, OrderItem
from app.extensions import db
from flask_dance.contrib.google import google
import logging
import traceback
from datetime import datetime



main = Blueprint('main', __name__)

payment_bp = Blueprint('payment', __name__)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])

            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash("❌ Username or Email already exists.")
                return redirect(url_for('main.register'))

            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("✅ Registration successful! Please log in.")
            return redirect(url_for('main.login'))
        except Exception as e:
            traceback.print_exc()  # This shows the error in terminal
            flash("⚠️ An unexpected error occurred.")
    return render_template('register.html')

@main.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)
def home():
    if "google_oauth_token" in session:
        return f"Logged in as: {session['google_user']['email']}"
    return "Not logged in"

@main.route('/product/<int:id>')
def product(id):
    product = Product.query.get_or_404(id)  # Retrieve product by id
    return render_template('product.html', product=product)


import logging

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logging.info(f"Trying login: {username}")

        user = User.query.filter_by(username=username).first()
        if user:
            logging.info("User found, checking password...")
        else:
            logging.warning("User not found!")

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('✅ Logged in successfully!')
            logging.info("Login successful")
            return redirect(url_for('main.dashboard'))  # ⬅ redirecting to dashboard
        else:
            flash('❌ Invalid username or password')
            logging.warning("Login failed")

    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))



@main.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash("✅ Product added to cart!")
    return redirect(url_for('main.index'))

@main.route('/cart')
def cart():
    cart = session.get('cart', {})
    products = []
    total = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        product.qty = qty
        product.subtotal = product.price * qty
        total += product.subtotal
        products.append(product)
    return render_template('cart.html', products=products, total=total)

@main.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('main.cart'))

@main.route('/increase/<int:product_id>')
def increase_qty(product_id):
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    return redirect(url_for('main.cart'))

@main.route('/decrease/<int:product_id>')
def decrease_qty(product_id):
    cart = session.get('cart', {})
    if cart.get(str(product_id), 0) > 1:
        cart[str(product_id)] -= 1
    else:
        cart.pop(str(product_id))
    session['cart'] = cart
    return redirect(url_for('main.cart'))

@main.route('/search')
def search():
    query = request.args.get('query', '').strip().lower()

    if not query:
        return jsonify([])  # Return empty list if no query

    # Fetch matching products
    products = Product.query.filter(Product.name.ilike(f"%{query}%")).all()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return product names for AJAX suggestions
        return jsonify([product.name for product in products])

    return render_template('search_results.html', results=products, query=query)

@main.route('/search-results')
def search_results():
    query = request.args.get('query', '').strip().lower()
    if not query:
        flash("⚠️ Please enter a search term.")
        return redirect(url_for('main.index'))

    # Store search query in session history
    search_history = session.get('search_history', [])
    if query not in search_history:
        search_history.insert(0, query)  # Insert recent search at the top
        session['search_history'] = search_history[:5]  # Keep only last 5 searches
        session.modified = True  # Ensure session updates

    results = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
    return render_template('search_results.html', results=results, query=query)


@main.route("/login/google")
def login_google():
    if not google.authorized:
        return redirect(url_for("google.login"))

    # If already authorized, get user info and log them in
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info.")
        return redirect(url_for("main.login"))

    user_info = resp.json()
    email = user_info["email"]
    username = user_info.get("name", email.split("@")[0])

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(username=username, email=email, password=generate_password_hash("oauth_dummy"))
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash("✅ Logged in with Google!")
    return redirect(url_for("main.index"))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


from flask import request
import razorpay

@main.route('/orders')
@login_required
def view_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date.desc()).all()
    
    order_data = []
    for order in orders:
        items = []
        for item in order.order_items:
            items.append({
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price": item.product.price,
                "subtotal": item.quantity * item.product.price
            })
        order_data.append({
            "id": order.id,
            "status": order.status,
            "amount": order.amount / 100,
            "date": order.date.strftime("%Y-%m-%d %H:%M"),
            "order_items": items
        })

    return render_template('orders.html', orders=order_data)

@payment_bp.route('/pay')
@login_required
def pay():
    try:
        cart = session.get('cart', {})
        if not cart:
            flash("⚠️ Your cart is empty!")
            return redirect(url_for('main.cart'))

        total = int(float(request.args.get('total', 0)))
        amount_in_paisa = total * 100

        client = razorpay.Client(auth=("rzp_test_qgoZNdxlHZY4kJ", "T8cGNIneP9TanfTObOTDn5EH"))

        # Create Razorpay order
        razorpay_order = client.order.create({
            "amount": amount_in_paisa,
            "currency": "INR",
            "payment_capture": 1
        })

        # Create order in database
        new_order = Order(
            user_id=current_user.id,
            razorpay_order_id=razorpay_order['id'],
            amount=amount_in_paisa,
            status='created',
            date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.session.add(new_order)
        db.session.commit()  # get new_order.id without committing

        print(f"Creating Order #{new_order.id} for User {current_user.id}")
        # Add order items
        for product_id_str, quantity in cart.items():
            product_id = int(product_id_str)
            product = Product.query.get(product_id)
    
            if product:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=quantity
                )
                db.session.add(order_item)
                print(f"✅ Added OrderItem: {product.name} x {quantity}")
            else:
                print(f"⚠️ Product ID {product_id} not found!")

        db.session.commit()

        

        # ✅ Clear cart after placing order
        session['cart'] = {}
        session.modified = True  # make sure session is saved

        return render_template("payment.html", order=razorpay_order, total=total)

    except Exception as e:
        print("🔥 ERROR during payment and order creation")
        import traceback
        traceback.print_exc()
        flash("❌ Something went wrong during payment.")
        return redirect(url_for('main.cart'))

@main.route('/clear-search-history')
def clear_search_history():
    session.pop('search_history', None)  # Remove search history from session
    flash("✅ Search history cleared!")
    return redirect(url_for('main.search_results'))

@main.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        # Check if the current password is correct
        if not check_password_hash(current_user.password, current_password):
            flash('Incorrect current password!', 'danger')
            return redirect(url_for('main.account'))

        # Update user info
        if username:
            current_user.username = username
        if email:
            current_user.email = email
        if new_password:
            current_user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('main.account'))

    return render_template('account.html')