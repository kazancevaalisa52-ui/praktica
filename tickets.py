from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Ticket, Category, User, StatusHistory, ALLOWED_TRANSITIONS
from auth import role_required

bp = Blueprint("tickets", __name__)


def can_open(user, ticket):
    if user.role in ("operator", "admin"):
        return True
    return user.role == "executor" and ticket.executor_id == user.id


@bp.route("/")
@login_required
def list_tickets():
    q = Ticket.query
    if current_user.role == "executor":
        q = q.filter(Ticket.executor_id == current_user.id)
    room = request.args.get("room", "").strip()
    category_id = request.args.get("category", "").strip()
    if room:
        q = q.filter(Ticket.room == room)
    if category_id.isdigit():
        q = q.filter(Ticket.category_id == int(category_id))
    tickets = q.order_by(Ticket.id.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template("tickets_list.html", tickets=tickets,
                           categories=categories, room=room, category_id=category_id)


@bp.route("/ticket/<int:tid>")
@login_required
def ticket_card(tid):
    ticket = Ticket.query.get_or_404(tid)
    if not can_open(current_user, ticket):
        abort(403)
    history = StatusHistory.query.filter_by(ticket_id=tid) \
        .order_by(StatusHistory.changed_at.desc()).all()
    executors = User.query.filter_by(role="executor", active=True).all()
    return render_template("ticket_card.html", ticket=ticket,
                           history=history, executors=executors)


@bp.route("/ticket/new", methods=["GET", "POST"])
@role_required("operator", "admin")
def ticket_new():
    categories = Category.query.order_by(Category.name).all()
    executors = User.query.filter_by(role="executor", active=True).all()
    errors = {}
    if request.method == "POST":
        data = request.form
        subject = data.get("subject", "").strip()
        room = data.get("room", "").strip()
        category_id = data.get("category_id", "").strip()
        executor_id = data.get("executor_id", "").strip()
        service_down = data.get("service_down") == "1"
        affected_raw = data.get("affected_count", "0").strip()

        if not subject:
            errors["subject"] = "Тема обязательна"
        if not room:
            errors["room"] = "Кабинет обязателен"
        if not category_id.isdigit():
            errors["category_id"] = "Выберите категорию"
        try:
            affected_count = int(affected_raw)
            if affected_count < 0:
                raise ValueError
        except ValueError:
            errors["affected_count"] = "Число — неотрицательное целое"

        if errors:
            return render_template("ticket_form.html", categories=categories,
                                   executors=executors, errors=errors, data=data), 400

        last = Ticket.query.order_by(Ticket.source_id.desc()).first()
        next_sid = (last.source_id + 1) if last else 1001
        ticket = Ticket(
            source_id=next_sid,
            date=datetime.utcnow().date(),
            room=room,
            category_id=int(category_id),
            subject=subject,
            status="Новая",
            executor_id=int(executor_id) if executor_id.isdigit() else None,
            service_down=service_down,
            affected_count=affected_count,
        )
        db.session.add(ticket)
        db.session.flush()
        db.session.add(StatusHistory(ticket_id=ticket.id, old_status=None,
                                     new_status="Новая", changed_by=current_user.id))
        db.session.commit()
        flash("Заявка создана", "ok")
        return redirect(url_for("tickets.ticket_card", tid=ticket.id))
    return render_template("ticket_form.html", categories=categories,
                           executors=executors, errors={}, data={})


@bp.route("/ticket/<int:tid>/status", methods=["POST"])
@role_required("executor", "admin")
def change_status(tid):
    ticket = Ticket.query.get_or_404(tid)
    if not can_open(current_user, ticket):
        abort(403)
    new_status = request.form.get("status", "")
    if (ticket.status, new_status) not in ALLOWED_TRANSITIONS:
        flash(f"Недопустимый переход: {ticket.status} → {new_status}", "error")
        return redirect(url_for("tickets.ticket_card", tid=tid)), 409
    old = ticket.status
    ticket.status = new_status
    db.session.add(StatusHistory(ticket_id=tid, old_status=old,
                                 new_status=new_status, changed_by=current_user.id))
    db.session.commit()
    flash(f"Статус изменён: {old} → {new_status}", "ok")
    return redirect(url_for("tickets.ticket_card", tid=tid))


@bp.route("/ticket/<int:tid>/assign", methods=["POST"])
@role_required("operator", "admin")
def assign(tid):
    ticket = Ticket.query.get_or_404(tid)
    executor_id = request.form.get("executor_id", "")
    if not executor_id.isdigit():
        flash("Выберите исполнителя", "error")
        return redirect(url_for("tickets.ticket_card", tid=tid)), 400
    ticket.executor_id = int(executor_id)
    db.session.commit()
    flash("Исполнитель назначен", "ok")
    return redirect(url_for("tickets.ticket_card", tid=tid))