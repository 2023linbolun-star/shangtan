from fastapi import APIRouter

router = APIRouter()


@router.get("/campaigns")
def list_campaigns():
    return {"success": True, "data": {"campaigns": []}, "message": "ok", "error": None}


@router.post("/generate-plan")
def generate_ad_plan(product_id: str, budget: float, platform: str = "qianchuan"):
    return {"success": True, "data": {"plan": {}}, "message": "方案生成完成", "error": None}


@router.get("/analytics")
def get_analytics():
    return {"success": True, "data": {"metrics": {}}, "message": "ok", "error": None}


@router.get("/ab-tests")
def list_ab_tests():
    return {"success": True, "data": {"tests": []}, "message": "ok", "error": None}
