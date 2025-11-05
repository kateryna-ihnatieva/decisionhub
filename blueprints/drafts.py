from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    current_app,
)
from models import db, Draft
from flask_login import login_required, current_user
from datetime import datetime
import pytz

drafts_bp = Blueprint("drafts", __name__, url_prefix="/drafts")


@drafts_bp.route("/")
@login_required
def index():
    """Страница со списком черновиков пользователя"""
    # Получаем параметры пагинации
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Ограничиваем количество элементов на странице
    if per_page > 50:
        per_page = 50
    elif per_page < 1:
        per_page = 10

    # Получаем черновики с пагинацией
    pagination = (
        Draft.query.filter_by(user_id=current_user.get_id())
        .order_by(Draft.updated_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    user_drafts = pagination.items

    context = {
        "title": "Мої чернетки",
        "name": current_user.get_name(),
        "drafts": user_drafts,
        "pagination": pagination,
        "current_page": page,
        "per_page": per_page,
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

        # Проверяем, является ли это автосохранением
        is_auto_save = data.get("is_auto_save", False)

        # Если это автосохранение, добавляем пометку к названию
        if is_auto_save:
            if not data.get("title"):
                title = f"🔄 {title}"
            elif not title.startswith("🔄"):
                title = f"🔄 {title}"

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
    """API для получения списка черновиков пользователя с пагинацией"""
    try:
        # Получаем параметры пагинации
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        # Ограничиваем количество элементов на странице
        if per_page > 50:
            per_page = 50
        elif per_page < 1:
            per_page = 10

        # Получаем черновики с пагинацией
        pagination = (
            Draft.query.filter_by(user_id=current_user.get_id())
            .order_by(Draft.updated_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        drafts = pagination.items

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

        return (
            jsonify(
                {
                    "drafts": drafts_list,
                    "pagination": {
                        "page": pagination.page,
                        "per_page": pagination.per_page,
                        "pages": pagination.pages,
                        "total": pagination.total,
                        "has_prev": pagination.has_prev,
                        "has_next": pagination.has_next,
                        "prev_num": pagination.prev_num,
                        "next_num": pagination.next_num,
                    },
                }
            ),
            200,
        )

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

        kiev_tz = pytz.timezone("Europe/Kiev")
        draft.updated_at = datetime.now(kiev_tz)
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
        "maximin": "Критерій Вальда",
        "savage": "Критерій Севіджа",
        "hurwitz": "Критерій Гурвіца",
    }

    method_name = method_names.get(method_type, method_type.title())
    kiev_tz = pytz.timezone("Europe/Kiev")
    current_time = datetime.now(kiev_tz).strftime("%d.%m.%Y %H:%M")

    return f"{method_name} - {current_time}"
