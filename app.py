from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User

import models
print("models chargé depuis :", models.__file__)
print("User class :", User)
print("User a set_password ? :", hasattr(User, "set_password"))

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-key-change-moi"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -------------------------
# LOGIN
# -------------------------
@app.get("/")
def login_page():
    return render_template("login.html")

@app.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("Email inconnu. Crée un compte.")
        return redirect(url_for("login_page"))

    if not user.check_password(password):
        flash("Mot de passe incorrect.")
        return redirect(url_for("login_page"))

    session["user_id"] = user.id
    flash(f"Connexion réussie. Bienvenue {user.firstname} !")
    return redirect(url_for("dashboard"))

# -------------------------
# REGISTER
# -------------------------
@app.get("/register")
def register_page():
    return render_template("register.html")

@app.post("/register")
def register_post():
    firstname = request.form.get("firstname", "").strip()
    lastname = request.form.get("lastname", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not firstname or not lastname or not email or not password or not confirm:
        flash("Tous les champs sont obligatoires.")
        return redirect(url_for("register_page"))

    if password != confirm:
        flash("Les mots de passe ne correspondent pas.")
        return redirect(url_for("register_page"))

    if User.query.filter_by(email=email).first():
        flash("Cet email est déjà utilisé.")
        return redirect(url_for("register_page"))

    user = User(firstname=firstname, lastname=lastname, email=email)

    # IMPORTANT : il faut que set_password existe bien dans models.py
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    session["registered_email"] = email
    return redirect(url_for("register_success_page"))

@app.get("/register/success")
def register_success_page():
    email = session.get("registered_email")
    return render_template("register_success.html", email=email)

# -------------------------
# DASHBOARD (protégé)
# -------------------------
@app.get("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        flash("Veuillez vous connecter.")
        return redirect(url_for("login_page"))

    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        flash("Session invalide. Veuillez vous reconnecter.")
        return redirect(url_for("login_page"))

    return render_template("dashboard.html", user=user)

# -------------------------
# LOGOUT
# -------------------------
@app.get("/logout")
def logout():
    session.clear()
    flash("Déconnecté.")
    return redirect(url_for("login_page"))

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
