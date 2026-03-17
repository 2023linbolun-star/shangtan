from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ContentGenerateRequest(BaseModel):
    content_type: str  # video_script, note, image, live_script, ad
    product_id: str
    platform: str
    style: str = "lively"
    notes: str = ""


@router.post("/generate")
def generate_content(req: ContentGenerateRequest):
    # TODO: integrate Claude API
    return {
        "success": True,
        "data": {
            "type": req.content_type,
            "content": {
                "title_suggestions": ["穿上就是蜜桃臀｜这条瑜伽裤绝了", "健身女孩必入｜提臀神裤测评"],
                "scenes": [
                    {"scene": 1, "camera": "特写镜头", "voiceover": "姐妹们！这条瑜伽裤我真的要吹爆！", "duration": "3s"},
                ],
            },
            "credits_used": 30,
        },
        "message": "生成完成",
        "error": None,
    }


@router.get("/list")
def list_contents():
    return {"success": True, "data": {"contents": []}, "message": "ok", "error": None}


@router.get("/assets")
def list_assets():
    return {"success": True, "data": {"assets": []}, "message": "ok", "error": None}
