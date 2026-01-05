from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    age: int

users: List[User] = []

@app.post("/users", response_model=User)
def create_user(user: User):
    for u in users:
        if u.id == user.id:
            raise HTTPException(status_code=400, detail="User already exists")
    users.append(user)
    return user

@app.get("/users", response_model=List[User])
def get_users():
    return users

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, updated_user: User):
    if updated_user.id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    for index, user in enumerate(users):
        if user.id == user_id:
            users[index] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for index, user in enumerate(users):
        if user.id == user_id:
            users.pop(index)
            return {"message": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")
