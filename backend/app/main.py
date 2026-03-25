import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, scout, content, listing, ads, ops, cs, data, credits, pipeline, feedback, stores, autopilot, onboarding
from app.db.engine import init_db, close_db
from app.middleware.logging import RequestLoggingMiddleware

# ── Logging setup ──
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","msg":"%(message)s"}',
)


# ── Lifespan: DB init on startup, cleanup on shutdown ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logging.getLogger("shangtanai").info("Database initialized")
    yield
    await close_db()
    logging.getLogger("shangtanai").info("Database closed")


app = FastAPI(
    title="商探AI API",
    description="全自动电商操盘系统 — AI 替你做电商，你只管收钱",
    version="2.0.0",
    lifespan=lifespan,
)

# ── Middleware ──
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


# ── Health ──
@app.get("/")
def root():
    return {"success": True, "data": {"name": "商探AI API", "version": "2.0.0"}, "message": "ok", "error": None}


@app.get("/health")
def health():
    return {"success": True, "data": {"status": "healthy"}, "message": "ok", "error": None}


# ── Routers ──
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["流水线"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(scout.router, prefix="/api/scout", tags=["选品雷达"])
app.include_router(content.router, prefix="/api/content", tags=["内容工厂"])
app.include_router(listing.router, prefix="/api/listing", tags=["上架中心"])
app.include_router(ads.router, prefix="/api/ads", tags=["广告助手"])
app.include_router(ops.router, prefix="/api/ops", tags=["运营管家"])
app.include_router(cs.router, prefix="/api/cs", tags=["客服大脑"])
app.include_router(data.router, prefix="/api/data", tags=["数据驾驶舱"])
app.include_router(credits.router, prefix="/api/credits", tags=["积分中心"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["反馈与进化"])
app.include_router(stores.router, prefix="/api/stores", tags=["店铺管理"])
app.include_router(autopilot.router, prefix="/api/autopilot", tags=["自动驾驶"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["新用户引导"])

# ── Static files (uploaded assets) ──
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
app.mount("/static/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
