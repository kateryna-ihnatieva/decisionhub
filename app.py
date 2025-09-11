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

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
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
from mymodules.file_parser import FileParser
from werkzeug.utils import secure_filename
import tempfile
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["TIMEZONE"] = "Europe/Kiev"

# File upload configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}

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
            criteria_names = session.get(HierarchyCriteria, result.method_id).names
            alternatives_names = session.get(
                HierarchyAlternatives, result.method_id
            ).names
            owner_name = session.get(User, result.user_id).name
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
            binary_names = session.get(BinaryNames, result.method_id).names
            owner_name = session.get(User, result.user_id).name
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
            name_research = session.get(ExpertsNameResearch, result.method_id).names
            owner_name = session.get(User, result.user_id).name
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
            name_alternatives = session.get(LaplasaAlternatives, result.method_id).names
            name_conditions = session.get(LaplasaConditions, result.method_id).names
            owner_name = session.get(User, result.user_id).name
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
            name_alternatives = session.get(MaximinAlternatives, result.method_id).names
            name_conditions = session.get(MaximinConditions, result.method_id).names
            owner_name = session.get(User, result.user_id).name
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
            name_alternatives = session.get(SavageAlternatives, result.method_id).names
            name_conditions = session.get(SavageConditions, result.method_id).names
            owner_name = session.get(User, result.user_id).name
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
            name_alternatives = session.get(HurwitzAlternatives, result.method_id).names
            name_conditions = session.get(HurwitzConditions, result.method_id).names
            owner_name = session.get(User, result.user_id).name
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
            # Delete alternatives matrices that reference this criteria_id
            HierarchyAlternativesMatrix.query.filter_by(
                criteria_id=result.method_id
            ).delete()
            # Delete alternatives matrices that reference this hierarchy_alternatives_id
            HierarchyAlternativesMatrix.query.filter_by(
                hierarchy_alternatives_id=result.method_id
            ).delete()
            # Delete criteria matrix
            HierarchyCriteriaMatrix.query.filter_by(id=result.method_id).delete()
            # Delete main records
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


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload_file", methods=["POST"])
@login_required
def upload_file():
    """Handle file upload and parsing"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"})

        if not allowed_file(file.filename):
            return jsonify(
                {
                    "success": False,
                    "error": "Invalid file type. Only Excel (.xlsx, .xls) and CSV files are allowed",
                }
            )

        # Get method parameters
        method_type = request.form.get("method_type")
        expected_criteria = int(request.form.get("expected_criteria", 0))
        expected_alternatives = int(request.form.get("expected_alternatives", 0))

        if not method_type:
            return jsonify({"success": False, "error": "Method type not specified"})

        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)

        try:
            # Parse file
            parser = FileParser()
            result = parser.parse_file(
                temp_path, method_type, expected_criteria, expected_alternatives
            )

            if result["success"]:
                # Store parsed data in session for later use
                session["uploaded_data"] = {
                    "method_type": method_type,
                    "criteria_names": result.get("criteria_names", []),
                    "alternative_names": result.get("alternative_names", []),
                    "condition_names": result.get("condition_names", []),
                    "matrices": result.get("matrices", []),
                    "matrix": result.get("matrix", []),
                    "file_name": filename,
                }

                return jsonify(
                    {
                        "success": True,
                        "message": "File parsed successfully",
                        "data": {
                            "criteria_names": result.get("criteria_names", []),
                            "alternative_names": result.get("alternative_names", []),
                            "condition_names": result.get("condition_names", []),
                            "matrices_count": len(result.get("matrices", [])),
                            "matrix_size": (
                                len(result.get("matrix", []))
                                if result.get("matrix")
                                else 0
                            ),
                        },
                    }
                )
            else:
                return jsonify(
                    {
                        "success": False,
                        "error": result.get("error", "Unknown parsing error"),
                    }
                )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

    except Exception as e:
        return jsonify({"success": False, "error": f"Upload error: {str(e)}"})


@app.route("/parse_file_preview", methods=["POST"])
@login_required
def parse_file_preview():
    """Preview file content without saving to database"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"})

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"})

        method_type = request.form.get("method_type")
        expected_criteria = int(request.form.get("expected_criteria", 0))
        expected_alternatives = int(request.form.get("expected_alternatives", 0))

        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)

        try:
            # Parse file
            parser = FileParser()
            result = parser.parse_file(
                temp_path, method_type, expected_criteria, expected_alternatives
            )

            return jsonify(
                {
                    "success": result["success"],
                    "error": result.get("error", ""),
                    "preview": {
                        "criteria_names": result.get("criteria_names", []),
                        "alternative_names": result.get("alternative_names", []),
                        "condition_names": result.get("condition_names", []),
                        "matrices": result.get("matrices", [])[
                            :3
                        ],  # Show first 3 matrices for preview
                        "matrix": (
                            result.get("matrix", [])[:5] if result.get("matrix") else []
                        ),  # Show first 5 rows
                    },
                }
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

    except Exception as e:
        return jsonify({"success": False, "error": f"Preview error: {str(e)}"})


@app.route("/download_example/<method_type>")
@login_required
def download_example(method_type):
    """Download example file for the specified method"""
    try:
        # Create example file based on method type
        parser = FileParser()

        if method_type == "hierarchy":
            # Create example hierarchy file
            example_data = {
                "criteria_names": ["Quality", "Price", "Service"],
                "alternative_names": ["Option A", "Option B", "Option C", "Option D"],
                "matrices": [
                    # Criteria comparison matrix
                    {
                        "names": ["Quality", "Price", "Service"],
                        "matrix": [[1, 2, 3], [0.5, 1, 4], [0.33, 0.25, 1]],
                    },
                    # Alternative matrices for each criterion
                    {
                        "names": ["Option A", "Option B", "Option C", "Option D"],
                        "matrix": [
                            [1, 5, 1, 1],
                            [0.2, 1, 1, 1],
                            [1, 1, 1, 1],
                            [1, 1, 1, 1],
                        ],
                    },
                    {
                        "names": ["Option A", "Option B", "Option C", "Option D"],
                        "matrix": [
                            [1, 0.5, 2, 3],
                            [2, 1, 4, 5],
                            [0.5, 0.25, 1, 2],
                            [0.33, 0.2, 0.5, 1],
                        ],
                    },
                    {
                        "names": ["Option A", "Option B", "Option C", "Option D"],
                        "matrix": [
                            [1, 1, 1, 1],
                            [1, 1, 1, 1],
                            [1, 1, 1, 1],
                            [1, 1, 1, 1],
                        ],
                    },
                ],
            }
        elif method_type in ["laplasa", "maximin", "savage", "hurwitz"]:
            # Create example cost matrix file
            example_data = {
                "alternative_names": ["Option A", "Option B", "Option C", "Option D"],
                "condition_names": ["Condition 1", "Condition 2", "Condition 3"],
                "matrix": [
                    [100, 200, 150],
                    [120, 180, 160],
                    [90, 220, 140],
                    [110, 190, 170],
                ],
            }
        elif method_type == "binary":
            # Create example binary relations file
            example_data = {
                "alternative_names": ["Option A", "Option B", "Option C", "Option D"],
                "matrix": [[0, 1, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 0]],
            }
        else:
            return jsonify({"success": False, "error": "Unknown method type"})

        # Create temporary Excel file
        import pandas as pd

        temp_dir = tempfile.mkdtemp()

        if method_type == "hierarchy":
            # Create multiple sheets for hierarchy
            with pd.ExcelWriter(
                os.path.join(temp_dir, f"example_{method_type}.xlsx"), engine="openpyxl"
            ) as writer:
                # Criteria matrix
                criteria_df = pd.DataFrame(
                    example_data["matrices"][0]["matrix"],
                    index=example_data["matrices"][0]["names"],
                    columns=example_data["matrices"][0]["names"],
                )
                criteria_df.to_excel(writer, sheet_name="Criteria")

                # Alternative matrices
                for i, matrix in enumerate(example_data["matrices"][1:], 1):
                    alt_df = pd.DataFrame(
                        matrix["matrix"], index=matrix["names"], columns=matrix["names"]
                    )
                    alt_df.to_excel(writer, sheet_name=f"Criterion_{i}")
        else:
            # Create single sheet for other methods
            if "matrix" in example_data:
                df = pd.DataFrame(
                    example_data["matrix"],
                    index=example_data["alternative_names"],
                    columns=example_data.get(
                        "condition_names", example_data["alternative_names"]
                    ),
                )
            else:
                df = pd.DataFrame(
                    example_data["matrices"][0]["matrix"],
                    index=example_data["matrices"][0]["names"],
                    columns=example_data["matrices"][0]["names"],
                )

            df.to_excel(os.path.join(temp_dir, f"example_{method_type}.xlsx"))

        # Return file
        from flask import send_file

        return send_file(
            os.path.join(temp_dir, f"example_{method_type}.xlsx"),
            as_attachment=True,
            download_name=f"example_{method_type}.xlsx",
        )

    except Exception as e:
        return jsonify(
            {"success": False, "error": f"Error creating example file: {str(e)}"}
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
