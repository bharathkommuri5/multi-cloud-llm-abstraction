from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.api.routes import router
from app.api.admin_routes import admin_router
from app.core.database import Base, engine
from app.core.middleware import CorrelationIdMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Cloud LLM Gateway")

templates = Jinja2Templates(directory="app/templates")

app.add_middleware(CorrelationIdMiddleware)


app.include_router(router, prefix="/api")
app.include_router(admin_router, prefix="/admin")


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
