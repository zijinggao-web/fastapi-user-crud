import os
from typing import List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# 数据库配置（容器里会被 docker-compose 的 DATABASE_URL 覆盖）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://appuser:apppass@localhost:3306/appdb"
)

# 生产并发建议：连接池 + 断线检测（echo=True 只建议开发用）
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    # 等应用启动时再建表，更稳
    Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    id: int
    name: str
    age: int


class UserResponse(BaseModel):
    id: int
    name: str
    age: int

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 直接插入，靠数据库主键保证唯一；并发下用 IntegrityError 兜底
    db_user = UserModel(id=user.id, name=user.name, age=user.age)
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")
    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(UserModel).all()


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, updated_user: UserCreate, db: Session = Depends(get_db)):
    if updated_user.id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新用户信息
    db_user.name = updated_user.name
    db_user.age = updated_user.age
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted"}
