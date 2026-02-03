# app/utils/database.py
# ----------------------------------------------------------------------------------
# 数据库工具 (Database Utils)
# 作用：配置异步数据库引擎 (Async Engine) 和会话生成器 (SessionMaker)。
# 技术栈：SQLAlchemy + aiomysql
# ----------------------------------------------------------------------------------

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# 数据库连接 URL
# 格式: mysql+aiomysql://user:password@host:port/dbname
DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/medical_qc"

# 创建异步引擎
# echo=True: 开启 SQL 日志输出，方便调试
engine = create_async_engine(DATABASE_URL, echo=True)

# 创建异步会话工厂
# expire_on_commit=False: 提交后不立即使对象过期，允许在会话关闭后继续访问属性
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# ORM 模型基类
Base = declarative_base()

# ----------------------------------------------------------------------------------
# 依赖函数：获取数据库会话
# 作用：用于 FastAPI 的 Depends 依赖注入，每个请求创建一个独立的数据库会话。
# ----------------------------------------------------------------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
