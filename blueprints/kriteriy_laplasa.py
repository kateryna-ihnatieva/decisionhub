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
