from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.portfolio import Portfolio, PortfolioEvidence, PortfolioEvidenceSkill


def run_additive_migrations(engine: Engine) -> None:
    """Create additive tables and give legacy portfolios private evidence records."""

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        portfolios = list(db.scalars(select(Portfolio)))
        for portfolio in portfolios:
            evidence = db.scalar(
                select(PortfolioEvidence).where(
                    PortfolioEvidence.portfolio_id == portfolio.id
                )
            )
            if evidence is None:
                evidence = PortfolioEvidence(portfolio_id=portfolio.id)
                db.add(evidence)
                db.flush()
            linked = db.scalar(
                select(PortfolioEvidenceSkill).where(
                    PortfolioEvidenceSkill.evidence_id == evidence.id,
                    PortfolioEvidenceSkill.skill_id == portfolio.skill_id,
                )
            )
            if linked is None:
                db.add(
                    PortfolioEvidenceSkill(
                        evidence_id=evidence.id, skill_id=portfolio.skill_id
                    )
                )
        db.commit()
