from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
def get_dashboard():
    return {
        "success": True,
        "data": {
            "kpis": {
                "total_sales": 128500,
                "total_profit": 38200,
                "orders": 1856,
                "avg_order_value": 69.2,
            }
        },
        "message": "ok",
        "error": None,
    }


@router.get("/reports")
def get_reports():
    return {"success": True, "data": {"reports": []}, "message": "ok", "error": None}


@router.post("/reports/generate")
def generate_report(report_type: str = "weekly"):
    return {"success": True, "data": {"report": {}}, "message": "报告生成中", "error": None}


@router.get("/forecast")
def get_forecast():
    return {"success": True, "data": {"forecast": {}}, "message": "ok", "error": None}
