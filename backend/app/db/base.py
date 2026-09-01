from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import application, portfolio, profile, project, skill, user  # noqa: E402,F401
