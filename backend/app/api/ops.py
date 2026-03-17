from fastapi import APIRouter

router = APIRouter()


@router.get("/pricing")
def get_pricing():
    return {"success": True, "data": {"products": []}, "message": "ok", "error": None}


@router.get("/inventory")
def get_inventory():
    return {"success": True, "data": {"items": []}, "message": "ok", "error": None}


@router.get("/promotions")
def get_promotions():
    return {"success": True, "data": {"plans": []}, "message": "ok", "error": None}


@router.post("/promotions/generate")
def generate_promotion():
    return {"success": True, "data": {"plan": {}}, "message": "ok", "error": None}


@router.get("/reviews")
def get_reviews():
    return {"success": True, "data": {"reviews": []}, "message": "ok", "error": None}


@router.post("/reviews/generate-reply")
def generate_reply(review_id: str):
    return {"success": True, "data": {"reply": ""}, "message": "ok", "error": None}
