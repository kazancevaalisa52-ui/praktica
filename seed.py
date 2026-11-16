from models import db, User, Category


def seed():
    if not User.query.filter_by(username="admin").first():
        for name, role, pwd in [
            ("admin", "admin", "Admin!234"),
            ("operator", "operator", "Oper!234"),
            ("executor", "executor", "Exec!234"),
            ("executor2", "executor", "Exec2!234"),
        ]:
            u = User(username=name, role=role)
            u.set_password(pwd)
            db.session.add(u)
    for c in ["Cets", "Печать", "ПО"]:
        if not Category.query.filter_by(name=c).first():
            db.session.add(Category(name=c))
    db.session.commit()