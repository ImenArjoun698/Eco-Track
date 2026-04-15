from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db, User, Action, Historique

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-key-change-moi"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -------------------------
# SECURITE LOGIN REQUIRED
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

    total_actions = len(historiques)

    if score_total >= 100:
        badge = "🌳 Héros écologique"
    elif score_total >= 50:
        badge = "🌱 Expert vert"
    else:
        badge = "🌿 Débutant"

    return render_template(
        "actions.html",
        actions=actions,
        score_total=score_total,
        total_actions=total_actions,
        badge=badge
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
# UPDATE SETTINGS
# -------------------------
@app.post("/settings")
@login_required
def update_settings():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)

    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email", "").strip().lower()

    if not firstname or not lastname or not email:
        flash("Tous les champs sont obligatoires.")
        return redirect(url_for("settings"))

    user.firstname = firstname
    user.lastname = lastname
    user.email = email

    db.session.commit()

    flash("Profil mis à jour !")
    return redirect(url_for("settings"))


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
# CHANGE PASSWORD
# -------------------------
@app.post("/settings/change_password")
@login_required
def change_password():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)

    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")

    if not user.check_password(old_password):
        flash("Ancien mot de passe incorrect.")
        return redirect(url_for("settings"))

    user.set_password(new_password)
    db.session.commit()

    flash("Mot de passe mis à jour !")
    return redirect(url_for("settings"))

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if not Action.query.first():
            actions = [
                Action(name="Vélo (trajet quotidien)", points=10),
                Action(name="Tri des déchets", points=5),
                Action(name="Économie d’eau", points=8),
                Action(name="Réduction chauffage", points=6),
                Action(name="Utilisation gourde réutilisable", points=4),
                Action(name="Extinction des lumières inutiles", points=3),
                Action(name="Réduction plastique", points=7),
                Action(name="Plantation d’un arbre", points=15),
                Action(name="Compostage des déchets organiques", points=8)
            ]
            db.session.add_all(actions)
            db.session.commit()

    app.run(debug=True)