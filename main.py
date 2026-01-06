import os
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# =========================
# Database
# =========================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://appuser:apppass@localhost:3306/appdb",
)

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

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)


# =========================
# JWT (Access token only, for demo loop)
# =========================
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(sub)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# FastAPI
# =========================
app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


# =========================
# Schemas
# =========================
class UserCreate(BaseModel):
    name: str
    age: int


class UserUpdate(BaseModel):
    name: str
    age: int


class UserResponse(BaseModel):
    id: int
    name: str
    age: int

    class Config:
        from_attributes = True


# =========================
# DB Dependency
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# Auth
# =========================
@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    # Demo loop: use username as user_id (int). password is ignored.
    try:
        user_id = int(form.username)
    except ValueError:
        raise HTTPException(status_code=400, detail="username must be an int user_id")

    token = create_access_token(user_id=user_id)
    return {"access_token": token, "token_type": "bearer"}


# =========================
# Users (JWT protected)
# =========================
@app.post("/users", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    _ = current_user_id  # only enforce authentication for demo

    db_user = UserModel(name=user.name, age=user.age)
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")

    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    _ = current_user_id
    return db.query(UserModel).all()


@app.get("/users/me", response_model=UserResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    _ = current_user_id
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updated_user: UserUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    _ = current_user_id

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = updated_user.name
    db_user.age = updated_user.age
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    _ = current_user_id

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return {"message": "User deleted"}


# =========================
# Test Page (Self-check loop)
# =========================
@app.get("/test", response_class=HTMLResponse)
def test_page():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>JWT User API 测试页面</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; max-width: 1200px; }
    .section { border: 1px solid #ddd; padding: 16px; margin: 16px 0; border-radius: 4px; }
    .section h3 { margin-top: 0; color: #333; }
    input, button, textarea { margin: 6px 0; padding: 8px; }
    input[type="text"], input[type="number"], input[type="password"] { width: 220px; }
    textarea { width: 100%; height: 100px; font-family: monospace; }
    button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 4px; }
    button:hover { background: #0056b3; }
    button.danger { background: #dc3545; }
    button.danger:hover { background: #c82333; }
    pre { background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; }
    .success { color: #28a745; }
    .error { color: #dc3545; }
    .form-group { margin: 12px 0; }
    label { display: block; margin-bottom: 4px; font-weight: bold; }
    .hint { color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <h1>🔐 JWT User API 测试页面</h1>

  <div class="section">
    <h3>使用说明（推荐闭环流程）</h3>
    <ol class="hint">
      <li>先在“创建用户”里创建一个用户（不需要填 ID，数据库会自动生成）。</li>
      <li>在响应里找到返回的 <b>id</b>，把它填到登录的 User ID 里。</li>
      <li>登录拿到 Token 后，再测试 <b>/users/me</b> 或其他接口。</li>
    </ol>
  </div>

  <!-- 登录区域 -->
  <div class="section">
    <h3>1. 登录获取 Token</h3>
    <p><strong>说明：</strong>使用 <b>User ID</b> 作为用户名（密码可任意，仅用于演示）</p>
    <div class="form-group">
      <label>User ID (作为用户名):</label>
      <input id="uid" type="number" value="1" />
    </div>
    <div class="form-group">
      <label>Password (可任意):</label>
      <input id="pwd" type="password" value="demo" />
    </div>
    <button onclick="login()">🔑 登录获取 Token</button>
  </div>

  <!-- Token 显示 -->
  <div class="section">
    <h3>2. Access Token</h3>
    <textarea id="token" placeholder="登录后 token 会显示在这里..."></textarea>
    <button onclick="copyToken()">📋 复制 Token</button>
  </div>

  <!-- 查询操作 -->
  <div class="section">
    <h3>3. 查询操作 (GET)</h3>
    <button onclick="callApi('GET', '/users/me')">获取当前用户信息 (/users/me)</button>
    <button onclick="callApi('GET', '/users')">获取所有用户 (/users)</button>
    <div class="form-group" style="margin-top: 12px;">
      <label>查询指定用户 ID:</label>
      <input id="getUserId" type="number" value="1" style="width: 120px;" />
      <button onclick="callApi('GET', '/users/' + document.getElementById('getUserId').value)">查询用户</button>
    </div>
  </div>

  <!-- 创建操作 -->
  <div class="section">
    <h3>4. 创建用户 (POST)</h3>
    <p class="hint">注意：创建用户不需要传 ID，数据库会自动生成并在响应中返回。</p>
    <div class="form-group">
      <label>Name:</label>
      <input id="createName" type="text" value="测试用户" />
    </div>
    <div class="form-group">
      <label>Age:</label>
      <input id="createAge" type="number" value="25" />
    </div>
    <button onclick="createUser()">➕ 创建用户</button>
  </div>

  <!-- 更新操作 -->
  <div class="section">
    <h3>5. 更新用户 (PUT)</h3>
    <p class="hint">更新时：路径使用 User ID，请求体只需要 name/age。</p>
    <div class="form-group">
      <label>User ID (路径参数):</label>
      <input id="updateId" type="number" value="1" />
    </div>
    <div class="form-group">
      <label>Name:</label>
      <input id="updateName" type="text" value="更新后的名字" />
    </div>
    <div class="form-group">
      <label>Age:</label>
      <input id="updateAge" type="number" value="30" />
    </div>
    <button onclick="updateUser()">✏️ 更新用户</button>
  </div>

  <!-- 删除操作 -->
  <div class="section">
    <h3>6. 删除用户 (DELETE)</h3>
    <div class="form-group">
      <label>User ID:</label>
      <input id="deleteId" type="number" value="1" />
    </div>
    <button class="danger" onclick="deleteUser()">🗑️ 删除用户</button>
  </div>

  <!-- 响应显示 -->
  <div class="section">
    <h3>📋 API 响应</h3>
    <pre id="out">等待操作...</pre>
  </div>

  <script>
    function getToken() {
      return document.getElementById('token').value.trim();
    }

    function showResponse(status, data) {
      const out = document.getElementById('out');
      const statusText = status >= 200 && status < 300 ?
        `<span class="success">✓ ${status}</span>` :
        `<span class="error">✗ ${status}</span>`;
      out.innerHTML = statusText + '\\n' + JSON.stringify(data, null, 2);
    }

    async function login() {
      const uid = document.getElementById('uid').value;
      const pwd = document.getElementById('pwd').value;

      const form = new URLSearchParams();
      form.append('username', uid);
      form.append('password', pwd);

      try {
        const r = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: form
        });

        const data = await r.json();
        if (data.access_token) {
          document.getElementById('token').value = data.access_token;
          showResponse(r.status, { message: '登录成功！', ...data });
        } else {
          showResponse(r.status, data);
        }
      } catch (error) {
        showResponse(500, { error: error.message });
      }
    }

    async function callApi(method, path, body = null) {
      const token = getToken();
      if (!token) {
        showResponse(401, { error: '请先登录获取 Token' });
        return;
      }

      const options = {
        method: method,
        headers: {
          'Authorization': 'Bearer ' + token,
          'Content-Type': 'application/json'
        }
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      try {
        const r = await fetch(path, options);
        const text = await r.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch {
          data = text;
        }
        showResponse(r.status, data);
      } catch (error) {
        showResponse(500, { error: error.message });
      }
    }

    function createUser() {
      const name = document.getElementById('createName').value;
      const age = parseInt(document.getElementById('createAge').value);
      callApi('POST', '/users', { name, age });
    }

    function updateUser() {
      const id = parseInt(document.getElementById('updateId').value);
      const name = document.getElementById('updateName').value;
      const age = parseInt(document.getElementById('updateAge').value);
      callApi('PUT', '/users/' + id, { name, age });
    }

    function deleteUser() {
      const id = document.getElementById('deleteId').value;
      if (confirm('确定要删除用户 ID ' + id + ' 吗？')) {
        callApi('DELETE', '/users/' + id);
      }
    }

    function copyToken() {
      const token = getToken();
      if (token) {
        navigator.clipboard.writeText(token).then(() => {
          alert('Token 已复制到剪贴板！');
        });
      } else {
        alert('请先登录获取 Token');
      }
    }
  </script>
</body>
</html>
"""
