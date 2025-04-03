from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import current_user
from app.models import Order, OrderItem, CartItem, db
import razorpay
from datetime import datetime

payment_bp = Blueprint('payment_bp', __name__) 

@payment_bp.route('/pay')
def pay():
    if not current_user.is_authenticated:
        flash("You need to log in to proceed to payment.", "warning")
        return redirect(url_for('main.login'))  # Redirect to login page
    
    total = int(float(request.args.get('total', 0)))
    amount_in_paisa = total * 100

    client = razorpay.Client(auth=("rzp_test_qgoZNdxlHZY4kJ", "T8cGNIneP9TanfTObOTDn5EH"))

    razorpay_order = client.order.create({
        "amount": amount_in_paisa,
        "currency": "INR",
        "payment_capture": 1
    })
    new_order = Order(
        user_id=current_user.id,
        razorpay_order_id=razorpay_order['id'],
        amount=amount_in_paisa,
        status='created',
        created_at=datetime.now(),
        date=datetime.now()
        )
    db.session.add(new_order)
    db.session.commit()

    return render_template("payment.html", order=razorpay_order, total=total)

@payment_bp.route('/success', methods=['POST'])
def payment_success():
    # You can verify payment here (optional, for real deployment)
    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')

    # Do any processing or save to DB here if needed
    # ✅ Clear the cart
    session.pop('cart', None)
    return redirect(url_for('payment_bp.success_page'))


@payment_bp.route('/success-page', methods=['GET'])
def success_page():
    return render_template('success.html')
