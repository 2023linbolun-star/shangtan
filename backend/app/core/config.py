import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/shangtanai")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

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

# 维易 API（veapi.cn）— 聚合中间层，暂时替代各平台官方 API
VEAPI_KEY = os.getenv("VEAPI_KEY", "")
VEAPI_TB_PID = os.getenv("VEAPI_TB_PID", "")  # 淘宝推广位 PID (mm_xx_xx_xx)
VEAPI_PDD_PID = os.getenv("VEAPI_PDD_PID", "")  # 拼多多推广位 ID
VEAPI_PDD_CUSTOM = os.getenv("VEAPI_PDD_CUSTOM", "")  # 拼多多自定义参数
