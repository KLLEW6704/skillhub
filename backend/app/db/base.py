from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import assessment, application, portfolio, profile, project, review, skill, user, verification  # noqa: E402,F401
