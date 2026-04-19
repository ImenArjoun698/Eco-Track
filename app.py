from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db, User, Action, Historique

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-key-change-moi"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -------------------------
# LOGIN REQUIRED
# -------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return wrapper


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
        flash("Email inconnu.")
        return redirect(url_for("login_page"))

    if not user.check_password(password):
        flash("Mot de passe incorrect.")
        return redirect(url_for("login_page"))

    session["user_id"] = user.id
    return redirect(url_for("actions_page"))


# -------------------------
# REGISTER
# -------------------------
@app.get("/register")
def register_page():
    return render_template("register.html")


@app.post("/register")
def register_post():
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password")

    if not firstname or not lastname or not email or not password:
        flash("Tous les champs sont obligatoires.")
        return redirect(url_for("register_page"))

    if User.query.filter_by(email=email).first():
        flash("Email déjà utilisé.")
        return redirect(url_for("register_page"))

    user = User(firstname=firstname, lastname=lastname, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash("Compte créé ! Connecte-toi.")
    return redirect(url_for("login_page"))


# -------------------------
# ACTIONS
# -------------------------
@app.get("/actions")
@login_required
def actions_page():
    user_id = session.get("user_id")

    actions = Action.query.all()
    historiques = Historique.query.filter_by(user_id=user_id).all()

    score_total = 0
    for h in historiques:
        action = db.session.get(Action, h.action_id)
        if action:
            score_total += action.points

    nb_actions_faites = len(historiques)

    # 🌍 PLANÈTE
    if score_total < 50:
        planet = "🌫️"
        planet_text = "Planète polluée"
    elif score_total < 150:
        planet = "🌿"
        planet_text = "Planète en amélioration"
    else:
        planet = "🌳"
        planet_text = "Planète en pleine santé"

    # 📊 PROGRESSION
    progress = min(score_total, 100)

    # 🎁 RECOMPENSES
    notification = None
    gift = None

    if score_total >= 300:
        gift = "🎁 CARREFOUR -15%"
        notification = "🎉 Bravo !"

    elif score_total >= 100:
        gift = "🎁 -20%"
        notification = f"🔥 Plus que {300 - score_total} points"

    elif score_total >= 50:
        gift = "🎁 LIDL -10%"
        notification = f"🎯 Plus que {100 - score_total} points"

    else:
        notification = f"🚀 Plus que {50 - score_total} points"

    # BADGE
    if score_total >= 100:
        badge = "🌳 Héros écologique"
    elif score_total >= 50:
        badge = "🌱 Expert vert"
    else:
        badge = "🌿 Débutant"

    return render_template(
        "actions.html",
        planet=planet,
        planet_text=planet_text,
        progress=progress,
        actions=actions,
        score_total=score_total,
        nb_actions_faites=nb_actions_faites,
        badge=badge,
        notification=notification,
        gift=gift
    )


# -------------------------
# DO ACTION
# -------------------------
@app.post("/actions/do/<int:action_id>")
@login_required
def do_action(action_id):
    user_id = session.get("user_id")

    historique = Historique(user_id=user_id, action_id=action_id)
    db.session.add(historique)
    db.session.commit()

    flash("Action enregistrée !")
    return redirect(url_for("actions_page"))


# -------------------------
# SETTINGS
# -------------------------
@app.get("/settings")
@login_required
def settings():
    user_id = session.get("user_id")

    user = db.session.get(User, user_id)

    historiques = Historique.query.filter_by(user_id=user_id).all()
    actions_count = len(historiques)

    co2_saved = actions_count * 2.3

    if actions_count >= 50:
        level = "🌍 Champion du climat"
    elif actions_count >= 20:
        level = "🌱 Eco actif"
    else:
        level = "🌿 Débutant"

    return render_template(
        "settings.html",
        user=user,
        actions_count=actions_count,
        co2_saved=co2_saved,
        level=level
    )


# -------------------------
# LOGOUT
# -------------------------
@app.get("/logout")
@login_required
def logout():
    session.clear()
    flash("Déconnecté.")
    return redirect(url_for("login_page"))


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)