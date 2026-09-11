from fastapi import APIRouter

from app.api.v1 import admin, applications, assessments, auth, collaboration, portfolios, profiles, projects, reviews, skills, verifications


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
api_router.include_router(verifications.router)
api_router.include_router(collaboration.router)
