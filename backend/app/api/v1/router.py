from fastapi import APIRouter

from app.api.v1 import admin, applications, assessments, auth, portfolios, profiles, projects, reviews, skills


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(skills.router)
api_router.include_router(portfolios.router)
api_router.include_router(projects.router)
api_router.include_router(admin.router)
api_router.include_router(applications.router)
api_router.include_router(reviews.router)
api_router.include_router(assessments.router)
