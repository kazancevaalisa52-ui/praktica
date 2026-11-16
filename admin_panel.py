from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, Category
from auth import role_required

bp = Blueprint("admin_panel", __name__, url_prefix="/admin")


@bp.route("/users")
@role_required("admin")
def users():
    return render_template("users.html", users=User.query.all())


@bp.route("/users/new", methods=["POST"])
@role_required("admin")
def users_new():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "operator")
    if not username or not password:
        flash("Логин и пароль обязательны", "error")
        return redirect(url_for("admin_panel.users")), 400
    if User.query.filter_by(username=username).first():
        flash("Пользователь уже существует", "error")
        return redirect(url_for("admin_panel.users")), 409
    u = User(username=username, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    flash("Пользователь создан", "ok")
    return redirect(url_for("admin_panel.users"))


@bp.route("/categories")
@role_required("admin")
def categories():
    return render_template("categories.html", categories=Category.query.all())


@bp.route("/categories/new", methods=["POST"])
@role_required("admin")
def categories_new():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Название обязательно", "error")
        return redirect(url_for("admin_panel.categories")), 400
    if Category.query.filter_by(name=name).first():
        flash("Категория уже есть", "error")
        return redirect(url_for("admin_panel.categories")), 409
    db.session.add(Category(name=name))
    db.session.commit()
    flash("Категория создана", "ok")
    return redirect(url_for("admin_panel.categories"))