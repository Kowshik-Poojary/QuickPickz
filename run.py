from app import create_app
from app.routes import main, payment_bp



app = create_app()
app.register_blueprint(main)
app.register_blueprint(payment_bp)

if __name__ == "__main__":
    app.run(debug=True)
