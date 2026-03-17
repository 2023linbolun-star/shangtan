from fastapi import APIRouter

router = APIRouter()


@router.get("/balance")
def get_balance():
    return {"success": True, "data": {"credits": 3000, "level": "新手", "discount": 0.9}, "message": "ok", "error": None}


@router.post("/checkin")
def daily_checkin():
    return {"success": True, "data": {"credits_earned": 100, "streak": 5}, "message": "签到成功", "error": None}


@router.get("/transactions")
def get_transactions():
    return {"success": True, "data": {"transactions": []}, "message": "ok", "error": None}


@router.post("/recharge")
def recharge(amount: int):
    return {"success": True, "data": {"credits_added": amount}, "message": "充值成功", "error": None}
