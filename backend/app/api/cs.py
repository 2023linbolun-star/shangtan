from fastapi import APIRouter

router = APIRouter()


@router.get("/conversations")
def list_conversations():
    return {"success": True, "data": {"conversations": []}, "message": "ok", "error": None}


@router.post("/reply")
def ai_reply(conversation_id: str, message: str):
    # TODO: Claude Haiku for fast replies
    return {
        "success": True,
        "data": {"reply": "感谢您的咨询...", "confidence": 0.92},
        "message": "ok",
        "error": None,
    }


@router.get("/knowledge")
def get_knowledge():
    return {"success": True, "data": {"entries": []}, "message": "ok", "error": None}


@router.get("/tickets")
def get_tickets():
    return {"success": True, "data": {"tickets": []}, "message": "ok", "error": None}
