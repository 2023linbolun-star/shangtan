from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, scout, content, listing, ads, ops, cs, data, credits

app = FastAPI(
    title="商探AI API",
    description="AI 全链路电商运营一体化工具",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"success": True, "data": {"name": "商探AI API", "version": "1.0.0"}, "message": "ok", "error": None}


@app.get("/health")
def health():
    return {"success": True, "data": {"status": "healthy"}, "message": "ok", "error": None}


app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(scout.router, prefix="/api/scout", tags=["选品雷达"])
app.include_router(content.router, prefix="/api/content", tags=["内容工厂"])
app.include_router(listing.router, prefix="/api/listing", tags=["上架中心"])
app.include_router(ads.router, prefix="/api/ads", tags=["广告助手"])
app.include_router(ops.router, prefix="/api/ops", tags=["运营管家"])
app.include_router(cs.router, prefix="/api/cs", tags=["客服大脑"])
app.include_router(data.router, prefix="/api/data", tags=["数据驾驶舱"])
app.include_router(credits.router, prefix="/api/credits", tags=["积分中心"])
