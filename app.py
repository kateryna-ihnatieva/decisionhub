# # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ #
# █                                                   █ #
# █             ██╗  ██╗          ██╗                 █ #
# █             ██║ ██╔╝          ██║                 █ #
# █             █████╔╝           ██║                 █ #
# █             ██╔═██╗           ██║                 █ #
# █             ██║  ██╗ ██╗      ██║ ██╗             █ #
# █             ╚═╝  ╚═╝ ╚═╝      ╚═╝ ╚═╝             █ #
# █                                                   █ #
# █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from flask import Flask, render_template, request, redirect, url_for
from blueprints import (
    hierarchy_bp,
    binary_relations_bp,
    experts_bp,
    kriteriy_laplasa_bp,
    maximin_bp,
    savage_bp,
    hurwitz_bp,
    drafts_bp,
)
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from UserLogin import UserLogin
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session
from flask_paginate import Pagination, get_page_args
from mymodules.methods import add_object_to_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["TIMEZONE"] = "Europe/Kiev"

db.init_app(app)

app.register_blueprint(hierarchy_bp)
app.register_blueprint(binary_relations_bp)
app.register_blueprint(experts_bp)
app.register_blueprint(kriteriy_laplasa_bp)
app.register_blueprint(maximin_bp)
app.register_blueprint(savage_bp)
app.register_blueprint(hurwitz_bp)
app.register_blueprint(drafts_bp)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    return UserLogin().create(user) if user else None


@app.route("/")
def index():
    context = {
        "title": "Головна",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("index.html", **context)


@app.route("/documentation")
def documentation():
    context = {
        "title": "Довідка",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("documentation.html", **context)


@app.route("/test-fix")
def test_fix():
    context = {
        "title": "Тест исправления",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("test-fix.html", **context)


@app.route("/login", methods=["GET", "POST"])
def login():
    context = {
        "title": "Авторизація",
    }

    if request.method == "POST":
        email = request.form["email"]
        psw = request.form["psw"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.psw, psw):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get("remainme") else False
            login_user(userlogin, remember=rm)
            return redirect(url_for("profile"))

        error = "Невірна пара логін/пароль"
        context["error"] = error

    return render_template("login.html", **context)


@app.route("/register", methods=["GET", "POST"])
def register():
    context = {"title": "Реєстрація"}

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        psw = request.form["psw"]
        psw2 = request.form["psw2"]

        if len(name) > 2 and len(email) > 4 and len(psw) > 4 and psw == psw2:
            hash = generate_password_hash(psw)

            # Перевірка унікальності email
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error = "Користувач з такою електронною адресою вже існує"
            else:
                res = add_object_to_db(db, User, name=name, email=email, psw=hash)
                if res:
                    success = "Ви успішно зареєструвалися!"
                    context["success"] = success
                    context["title"] = "Авторизація"
                    return render_template("login.html", **context)
                else:
                    error = "Помилка при додаванні у БД"
        else:
            if psw != psw2:
                error = "Паролі не співпадають!"
            else:
                error = "Невірно заповнені поля!"

        if error:
            context = {"title": "Реєстрація", "error": error}
            return render_template("register.html", **context)

    return render_template("register.html", **context)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    success = "Ви вийшли з акаунту"
    context = {"title": "Авторизація", "success": success}
    return render_template("login.html", **context)


@app.route("/profile", methods=["POST", "GET"])
@login_required
def profile():
    page, _, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    per_page = 12

    user = current_user
    if user.get_name() == "admin":
        results = Result.query.all()
    else:
        results = Result.query.filter_by(user_id=user.get_id()).all()

    # Сортування результатів за новизною
    results.sort(key=lambda x: x.id, reverse=True)

    result_history = []
    for result in results:
        result_id = result.id
        method_name = result.method_name
        method_id = result.method_id

        if method_name == "Hierarchy":
            session = Session(bind=db.engine)

            # Check if records exist before accessing them
            criteria_record = session.get(HierarchyCriteria, result.method_id)
            alternatives_record = session.get(HierarchyAlternatives, result.method_id)
            user_record = session.get(User, result.user_id)

            if not criteria_record or not alternatives_record or not user_record:
                # Skip this result if data is missing
                continue

            criteria_names = criteria_record.names
            alternatives_names = alternatives_record.names
            owner_name = user_record.name
            result_history.append(
                {
                    "result_id": result_id,
                    "method_id": method_id,
                    "method_name": method_name,
                    "criteria_names": criteria_names,
                    "alternatives_names": alternatives_names,
                    "owner_name": owner_name,
                }
            )
            session.close()

        if method_name == "Binary":
            session = Session(bind=db.engine)

            # Check if records exist before accessing them
            binary_record = session.get(BinaryNames, result.method_id)
            user_record = session.get(User, result.user_id)

            if not binary_record or not user_record:
                # Skip this result if data is missing
                continue

            binary_names = binary_record.names
            owner_name = user_record.name
            result_history.append(
                {
                    "result_id": result_id,
                    "method_id": method_id,
                    "method_name": method_name,
                    "binary_names": binary_names,
                    "owner_name": owner_name,
                }
            )
            session.close()

        if method_name == "Experts":
            session = Session(bind=db.engine)

            # Check if records exist before accessing them
            research_record = session.get(ExpertsNameResearch, result.method_id)
            user_record = session.get(User, result.user_id)

            if not research_record or not user_record:
                # Skip this result if data is missing
                continue

            name_research = research_record.names
            owner_name = user_record.name
            result_history.append(
                {
                    "result_id": result_id,
                    "method_id": method_id,
                    "method_name": method_name,
                    "name_research": name_research,
                    "owner_name": owner_name,
                }
            )
            session.close()

        if method_name == "Laplasa":
            session = Session(bind=db.engine)

            # Check if records exist before accessing them
            alternatives_record = session.get(LaplasaAlternatives, result.method_id)
            conditions_record = session.get(LaplasaConditions, result.method_id)
            user_record = session.get(User, result.user_id)

            if not alternatives_record or not conditions_record or not user_record:
                # Skip this result if data is missing
                continue

            name_alternatives = alternatives_record.names
            name_conditions = conditions_record.names
            owner_name = user_record.name
            result_history.append(
                {
                    "result_id": result_id,
                    "method_id": method_id,
                    "method_name": method_name,
                    "name_alternatives": name_alternatives,
                    "name_conditions": name_conditions,
                    "owner_name": owner_name,
                }
            )
            session.close()

        if method_name == "Maximin":
            session = Session(bind=db.engine)

            # Check if records exist before accessing them
            alternatives_record = session.get(MaximinAlternatives, result.method_id)
            conditions_record = session.get(MaximinConditions, result.method_id)
            user_record = session.get(User, result.user_id)

            if not alternatives_record or not conditions_record or not user_record:
                # Skip this result if data is missing
                continue

            name_alternatives = alternatives_record.names
            name_conditions = conditions_record.names
            owner_name = user_record.name
            result_history.append(
                {
                    "result_id": result_id,
                    "method_id": method_id,
                    "method_name": method_name,
                    "name_alternatives": name_alternatives,
                    "name_conditions": name_conditions,
                    "owner_name": owner_name,
                }
            )
            session.close()

        if method_name == "Savage":
            session = Session(bind=db.engine)

            # Check if records exist before accessing them
            alternatives_record = session.get(SavageAlternatives, result.method_id)
            conditions_record = session.get(SavageConditions, result.method_id)
            user_record = session.get(User, result.user_id)

            if not alternatives_record or not conditions_record or not user_record:
                # Skip this result if data is missing
                continue

            name_alternatives = alternatives_record.names
            name_conditions = conditions_record.names
            owner_name = user_record.name
            result_history.append(
                {
                    "result_id": result_id,
                    "method_id": method_id,
                    "method_name": method_name,
                    "name_alternatives": name_alternatives,
                    "name_conditions": name_conditions,
                    "owner_name": owner_name,
                }
            )
            session.close()

        if method_name == "Hurwitz":
            session = Session(bind=db.engine)

            # Check if records exist before accessing them
            alternatives_record = session.get(HurwitzAlternatives, result.method_id)
            conditions_record = session.get(HurwitzConditions, result.method_id)
            user_record = session.get(User, result.user_id)

            if not alternatives_record or not conditions_record or not user_record:
                # Skip this result if data is missing
                continue

            name_alternatives = alternatives_record.names
            name_conditions = conditions_record.names
            owner_name = user_record.name
            result_history.append(
                {
                    "result_id": result_id,
                    "method_id": method_id,
                    "method_name": method_name,
                    "name_alternatives": name_alternatives,
                    "name_conditions": name_conditions,
                    "owner_name": owner_name,
                }
            )
            session.close()

    # Розбиваємо список результатів на сторінці
    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=len(result_history),
        record_name="result_history",
    )
    result_history = result_history[offset : offset + per_page]

    context = {
        "title": "Профіль",
        "name": current_user.get_name(),
        "email": current_user.get_email(),
        "result_history": result_history,
        "pagination": pagination,
    }

    return render_template("profile.html", **context)


@app.route("/delete_result/<int:result_id>", methods=["POST"])
@login_required
def delete_result(result_id):
    result = db.session.get(Result, result_id)
    if result:
        # Видалення пов'язаних записів
        if result.method_name == "Hierarchy":
            HierarchyCriteriaMatrix.query.filter_by(id=result.method_id).delete()
            HierarchyAlternativesMatrix.query.filter_by(id=result.method_id).delete()
            HierarchyCriteria.query.filter_by(id=result.method_id).delete()
            HierarchyAlternatives.query.filter_by(id=result.method_id).delete()
            HierarchyTask.query.filter_by(id=result.method_id).delete()
            GlobalPrioritiesPlot.query.filter_by(id=result.method_id).delete()
        elif result.method_name == "Binary":
            BinaryTransitivity.query.filter_by(id=result.method_id).delete()
            BinaryTask.query.filter_by(id=result.method_id).delete()
            BinaryRanj.query.filter_by(id=result.method_id).delete()
            BinaryMatrix.query.filter_by(binary_names_id=result.method_id).delete()
            BinaryNames.query.filter_by(id=result.method_id).delete()
        elif result.method_name == "Experts":
            ExpertsTask.query.filter_by(id=result.method_id).delete()
            ExpertsData.query.filter_by(
                experts_name_research_id=result.method_id
            ).delete()
            ExpertsCompetency.query.filter_by(id=result.method_id).delete()
            ExpertsNameResearch.query.filter_by(id=result.method_id).delete()

        # Видалення самого результату
        db.session.delete(result)
        db.session.commit()
        return redirect(url_for("profile"))
    else:
        return "404", 404


@app.route("/change_name", methods=["GET", "POST"])
@login_required
def change_name():
    context = {
        "title": "Зміна імені",
        "name": current_user.get_name(),
        "email": current_user.get_email(),
    }
    if request.method == "POST":
        new_name = request.form["new_name"]

        if new_name.strip() == "":
            error = "Нове ім'я не може бути порожнім!"
            context["error"] = error
            return render_template("change_name.html", **context)

        user_id = current_user.get_id()
        user = User.query.filter_by(id=user_id).first()
        user.name = new_name
        db.session.commit()

        return redirect(url_for("profile"))

    return render_template("change_name.html", **context)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
