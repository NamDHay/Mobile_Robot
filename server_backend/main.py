from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt
from fastapi.middleware.cors import CORSMiddleware  # Thêm middleware CORS

app = FastAPI()

# Middleware CORS để cho phép yêu cầu từ client (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Cho phép client ở localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kết nối MongoDB
client = MongoClient('mongodb+srv://hoangkahn123:0968269517@cluster0.8to29z8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  # Thay đổi chuỗi kết nối nếu cần
db = client["userdb"]
users_collection = db["users"]

class User(BaseModel):
    username: str
    password: str

@app.post("/register/") 
async def register_user(user: User):
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    
    print ("đã đăng ký")

    try:
        users_collection.insert_one({"username": user.username, "password": hashed_password})
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/login/")
async def login_user(user: User):
    found_user = users_collection.find_one({"username": user.username})
    
    if found_user and bcrypt.checkpw(user.password.encode("utf-8"), found_user["password"]):
        # Không trả về mật khẩu
        return {"username": found_user["username"], "id": str(found_user["_id"])}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")