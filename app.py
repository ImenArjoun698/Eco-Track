from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Action, Historique

# Création de l'application Flask
app = Flask(__name__)

# Configuration de base
app.config["SECRET_KEY"] = "dev-key-change-moi"  # pour les sessions
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"  # base de données
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialisation de la base de données
db.init_app(app)

# -------------------------
# PAGE LOGIN
# -------------------------
@app.get("/")
def login_page():
    # Affiche la page de connexion
    return render_template("login.html")


@app.post("/login")
def login_post():
    # Récupération des données du formulaire
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Recherche de l'utilisateur dans la base
    user = User.query.filter_by(email=email).first()

    # Vérifie si l'utilisateur existe
    if not user:
        flash("Email inconnu.")
        return redirect(url_for("login_page"))

    # Vérifie le mot de passe
    if not user.check_password(password):
        flash("Mot de passe incorrect.")
        return redirect(url_for("login_page"))

    # Connexion → on stocke l'id dans la session
    session["user_id"] = user.id

    # Redirection vers les actions
    return redirect(url_for("actions_page"))


# -------------------------
# PAGE REGISTER
# -------------------------
@app.get("/register")
def register_page():
    return render_template("register.html")


@app.post("/register")
def register_post():
    # Récupération des données
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email").lower()
    password = request.form.get("password")

    # Vérifie si l'email existe déjà
    if User.query.filter_by(email=email).first():
        flash("Email déjà utilisé.")
        return redirect(url_for("register_page"))

    # Création utilisateur
    user = User(firstname=firstname, lastname=lastname, email=email)

    # Hash du mot de passe
    user.set_password(password)

    # Sauvegarde en base
    db.session.add(user)
    db.session.commit()

    flash("Compte créé ! Connecte-toi.")
    return redirect(url_for("login_page"))


# -------------------------
# PAGE ACTIONS
# -------------------------
@app.get("/actions")
def actions_page():
    user_id = session.get("user_id")

    # Vérifie si connecté
    if not user_id:
        return redirect(url_for("login_page"))

    # Récupère toutes les actions disponibles
    actions = Action.query.all()

    # Récupère l'historique de l'utilisateur
    historiques = Historique.query.filter_by(user_id=user_id).all()

    # Calcul du score total
    score_total = 0
    for h in historiques:
        action = db.session.get(Action, h.action_id)
        if action:
            score_total += action.points

    # Nombre d'actions réalisées
    total_actions = len(historiques)

    # Attribution d'un badge simple
    if score_total >= 100:
        badge = "🌳 Héros écologique"
    elif score_total >= 50:
        badge = "🌱 Expert vert"
    else:
        badge = "🌿 Débutant"

    # Envoie les données au HTML
    return render_template(
        "actions.html",
        actions=actions,
        score_total=score_total,
        total_actions=total_actions,
        badge=badge
    )


# -------------------------
# FAIRE UNE ACTION
# -------------------------
@app.post("/actions/do/<int:action_id>")
def do_action(action_id):
    user_id = session.get("user_id")

    # Vérifie si connecté
    if not user_id:
        return redirect(url_for("login_page"))

    # Ajoute l'action dans l'historique
    historique = Historique(user_id=user_id, action_id=action_id)
    db.session.add(historique)
    db.session.commit()

    flash("Action enregistrée !")
    return redirect(url_for("actions_page"))


# -------------------------
# PARAMETRES (simple)
# -------------------------
@app.get("/settings")
def settings():
    user_id = session.get("user_id")

    # Vérifie si connecté
    if not user_id:
        return redirect(url_for("login_page"))

    return render_template("settings.html")


# -------------------------
# DECONNEXION
# -------------------------
@app.get("/logout")
def logout():
    # Supprime la session
    session.clear()
    flash("Déconnecté.")
    return redirect(url_for("login_page"))


# -------------------------
# LANCEMENT APP
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # crée les tables si elles n'existent pas

        # Ajoute des actions par défaut si la table est vide
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

    # Lance le serveur
    app.run(debug=True)