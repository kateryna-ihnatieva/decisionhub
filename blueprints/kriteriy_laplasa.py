from flask import Blueprint, render_template, request, session, redirect, url_for
from mymodules.mai import *
from models import *
from mymodules.gpt_response import *
from mymodules.methods import *
from mymodules.binary import *
from flask_login import current_user

kriteriy_laplasa_bp = Blueprint(
    "kriteriy_laplasa", __name__, url_prefix="/kriteriy-laplasa"
)


@kriteriy_laplasa_bp.route("/")
def index():
    context = {
        "title": "Критерій Лапласа",
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }
    return render_template("Laplasa/index.html", **context)


@kriteriy_laplasa_bp.route("/names", methods=["GET", "POST"])
def names():
    num_alt = int(request.args.get("num_alt"))
    num_conditions = int(request.args.get("num_conditions"))
    laplasa_task = (
        request.args.get("laplasa_task") if request.args.get("laplasa_task") else None
    )

    # Збереження змінної у сесії
    session["num_alt"] = num_alt
    session["num_conditions"] = num_conditions
    session["laplasa_task"] = laplasa_task

    context = {
        "title": "Імена",
        "num_alt": num_alt,
        "num_conditions": num_conditions,
        "name": current_user.get_name() if current_user.is_authenticated else None,
    }

    return render_template("Laplasa/names.html", **context)
