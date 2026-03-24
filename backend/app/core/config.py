import os
from dotenv import load_dotenv

load_dotenv()

# --- 基础服务 ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/shangtanai")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# --- AI 模型 API ---
# Claude（测试阶段临时使用，后续切换到国内模型）
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# OpenAI（测试阶段）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# DeepSeek（市场分析 / 降级备选）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 豆包 Doubao / 火山引擎（社媒内容：抖音脚本/小红书笔记）
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
DOUBAO_BASE_URL = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DOUBAO_MODEL_PRO = os.getenv("DOUBAO_MODEL_PRO", "doubao-seed-2-0-pro")  # 内容生成
DOUBAO_MODEL_LITE = os.getenv("DOUBAO_MODEL_LITE", "doubao-1.5-lite-32k")  # 轻量任务

# 通义千问 Qwen / DashScope（正式文案 / Listing优化）
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL_PLUS = os.getenv("QWEN_MODEL_PLUS", "qwen-plus")  # 正式文案
QWEN_MODEL_FLASH = os.getenv("QWEN_MODEL_FLASH", "qwen-turbo")  # SEO/批量

# 智谱 GLM（免费快速任务：关键词拓展/违规检测）
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
GLM_MODEL_FLASH = os.getenv("GLM_MODEL_FLASH", "glm-4-flash")  # 免费

# --- 联盟 API 密钥 ---
# 淘宝联盟（阿里妈妈）
TAOBAO_APP_KEY = os.getenv("TAOBAO_APP_KEY", "")
TAOBAO_APP_SECRET = os.getenv("TAOBAO_APP_SECRET", "")
TAOBAO_ADZONE_ID = os.getenv("TAOBAO_ADZONE_ID", "")

# 多多进宝（拼多多）
PDD_CLIENT_ID = os.getenv("PDD_CLIENT_ID", "")
PDD_CLIENT_SECRET = os.getenv("PDD_CLIENT_SECRET", "")
PDD_PID = os.getenv("PDD_PID", "")

# 抖音精选联盟（聚推客）
JUTUIKE_PUB_ID = os.getenv("JUTUIKE_PUB_ID", "")

# 1688 开放平台
ALIBABA_APP_KEY = os.getenv("ALIBABA_APP_KEY", "")
ALIBABA_APP_SECRET = os.getenv("ALIBABA_APP_SECRET", "")

# 小红书开放平台
XHS_APP_ID = os.getenv("XHS_APP_ID", "")
XHS_APP_SECRET = os.getenv("XHS_APP_SECRET", "")

# 维易 API（veapi.cn）— 聚合中间层
VEAPI_KEY = os.getenv("VEAPI_KEY", "")
VEAPI_TB_PID = os.getenv("VEAPI_TB_PID", "")
VEAPI_PDD_PID = os.getenv("VEAPI_PDD_PID", "")
VEAPI_PDD_CUSTOM = os.getenv("VEAPI_PDD_CUSTOM", "")

# --- 凭证加密 ---
CREDENTIAL_ENCRYPTION_KEY = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "")

# --- 抖音开放平台（视频发布）---
DOUYIN_CLIENT_KEY = os.getenv("DOUYIN_CLIENT_KEY", "")
DOUYIN_CLIENT_SECRET = os.getenv("DOUYIN_CLIENT_SECRET", "")

# --- 微信公众号 ---
WECHAT_OA_APP_ID = os.getenv("WECHAT_OA_APP_ID", "")
WECHAT_OA_APP_SECRET = os.getenv("WECHAT_OA_APP_SECRET", "")

# --- 趋势数据 ---
ALAPI_TOKEN = os.getenv("ALAPI_TOKEN", "")  # alapi.cn free tier
