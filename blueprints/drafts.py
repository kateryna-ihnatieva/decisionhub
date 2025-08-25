from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    current_app,
    session,
)
from models import db, Draft
from flask_login import login_required, current_user
from datetime import datetime
import json

drafts_bp = Blueprint("drafts", __name__, url_prefix="/drafts")


@drafts_bp.route("/")
@login_required
def index():
    """Страница со списком черновиков пользователя"""
    user_drafts = (
        Draft.query.filter_by(user_id=current_user.get_id())
        .order_by(Draft.updated_at.desc())
        .all()
    )

    context = {
        "title": "Мої чернетки",
        "name": current_user.get_name(),
        "drafts": user_drafts,
    }
    return render_template("drafts/index.html", **context)


@drafts_bp.route("/api", methods=["POST"])
@login_required
def save_draft():
    """API для сохранения черновика"""
    try:
        data = request.get_json()

        # Валидация данных
        required_fields = ["method_type", "current_route", "form_data"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Генерация названия черновика
        title = data.get("title") or generate_draft_title(data["method_type"])

        # Создание нового черновика
        draft = Draft(
            title=title,
            method_type=data["method_type"],
            current_route=data["current_route"],
            form_data=data["form_data"],
            user_id=current_user.get_id(),
        )

        db.session.add(draft)
        db.session.commit()

        return (
            jsonify(
                {"success": True, "message": "Чернетку збережено", "draft_id": draft.id}
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error saving draft: {str(e)}")
        return jsonify({"error": "Помилка збереження чернетки"}), 500


@drafts_bp.route("/api", methods=["GET"])
@login_required
def get_drafts():
    """API для получения списка черновиков пользователя"""
    try:
        drafts = (
            Draft.query.filter_by(user_id=current_user.get_id())
            .order_by(Draft.updated_at.desc())
            .all()
        )

        drafts_list = []
        for draft in drafts:
            drafts_list.append(
                {
                    "id": draft.id,
                    "title": draft.title,
                    "method_type": draft.method_type,
                    "current_route": draft.current_route,
                    "created_at": draft.created_at.isoformat(),
                    "updated_at": draft.updated_at.isoformat(),
                }
            )

        return jsonify({"drafts": drafts_list}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting drafts: {str(e)}")
        return jsonify({"error": "Помилка отримання чернеток"}), 500


@drafts_bp.route("/api/<int:draft_id>", methods=["GET"])
@login_required
def get_draft(draft_id):
    """API для получения конкретного черновика"""
    try:
        draft = Draft.query.filter_by(
            id=draft_id, user_id=current_user.get_id()
        ).first()

        if not draft:
            return jsonify({"error": "Чернетку не знайдено"}), 404

        return (
            jsonify(
                {
                    "id": draft.id,
                    "title": draft.title,
                    "method_type": draft.method_type,
                    "current_route": draft.current_route,
                    "form_data": draft.form_data,
                    "created_at": draft.created_at.isoformat(),
                    "updated_at": draft.updated_at.isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting draft: {str(e)}")
        return jsonify({"error": "Помилка отримання чернетки"}), 500


@drafts_bp.route("/api/<int:draft_id>", methods=["PUT"])
@login_required
def update_draft(draft_id):
    """API для обновления черновика"""
    try:
        draft = Draft.query.filter_by(
            id=draft_id, user_id=current_user.get_id()
        ).first()

        if not draft:
            return jsonify({"error": "Чернетку не знайдено"}), 404

        data = request.get_json()

        # Обновление полей
        if "title" in data:
            draft.title = data["title"]
        if "current_route" in data:
            draft.current_route = data["current_route"]
        if "form_data" in data:
            draft.form_data = data["form_data"]

        draft.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"success": True, "message": "Чернетку оновлено"}), 200

    except Exception as e:
        current_app.logger.error(f"Error updating draft: {str(e)}")
        return jsonify({"error": "Помилка оновлення чернетки"}), 500


@drafts_bp.route("/api/<int:draft_id>", methods=["DELETE"])
@login_required
def delete_draft(draft_id):
    """API для удаления черновика"""
    try:
        draft = Draft.query.filter_by(
            id=draft_id, user_id=current_user.get_id()
        ).first()

        if not draft:
            return jsonify({"error": "Чернетку не знайдено"}), 404

        db.session.delete(draft)
        db.session.commit()

        return jsonify({"success": True, "message": "Чернетку видалено"}), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting draft: {str(e)}")
        return jsonify({"error": "Помилка видалення чернетки"}), 500


def generate_draft_title(method_type):
    """Генерация названия черновика"""
    method_names = {
        "hierarchy": "Метод Аналізу Ієрархій",
        "binary": "Метод Бінарних Відношень",
        "experts": "Метод Експертних Оцінок",
        "laplasa": "Критерій Лапласа",
        "maximin": "Критерій Максиміна",
        "savage": "Критерій Севіджа",
        "hurwitz": "Критерій Гурвіца",
    }

    method_name = method_names.get(method_type, method_type.title())
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    return f"{method_name} - {current_time}"
