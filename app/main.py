# main.py
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import logging
from typing import List, Optional
from .database import engine, Base
from .models import *

# 모델 정의
class APIKeys(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    user_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)

class Anime(Base):
    __tablename__ = "anime"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genre = Column(String)
    aired_date = Column(DateTime)
    synopsis = Column(String)
    studio = Column(String)
    episodes = Column(Integer)
    rating = Column(Float)
    image_url = Column(String)

app = FastAPI(title="Zooda API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 시작 시 테이블 생성
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

# 데이터베이스 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API 키 검증 - 간단화된 버전
def validate_api_key(request: Request, db: Session = Depends(get_db)):
    api_key = request.query_params.get('key')
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is required")

    key_record = db.query(APIKeys).filter(
        APIKeys.key == api_key,
        APIKeys.is_active == 1
    ).first()

    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    return api_key

# 엔드포인트
@app.get("/")
async def read_root():
    return {"message": "Welcome to Zooda API"}

@app.get("/anime")
async def get_anime_list(
    db: Session = Depends(get_db),
    api_key: str = Depends(validate_api_key),
    skip: int = 0,
    limit: int = 10
):
    anime_list = db.query(Anime).offset(skip).limit(limit).all()
    total = db.query(Anime).count()
    return {
        "total": total,
        "data": anime_list,
        "page": skip // limit + 1 if limit > 0 else 1,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@app.get("/anime/search")
async def search_anime(
    db: Session = Depends(get_db),
    api_key: str = Depends(validate_api_key),
    title: Optional[str] = None,
    genre: Optional[str] = None
):
    query = db.query(Anime)
    if title:
        query = query.filter(Anime.title.ilike(f"%{title}%"))
    if genre:
        query = query.filter(Anime.genre.ilike(f"%{genre}%"))
    return query.all()

@app.get("/anime/{anime_id}")
async def get_anime_detail(
    anime_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(validate_api_key)
):
    anime = db.query(Anime).filter(Anime.id == anime_id).first()
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")
    return anime

# 테스트용 엔드포인트들
@app.get("/test/add-sample")
async def add_sample_data(db: Session = Depends(get_db)):
    """테스트용 샘플 데이터를 추가합니다"""
    sample_animes = [
        Anime(
            title="원피스",
            genre="액션, 모험",
            aired_date=datetime(1999, 10, 20),
            synopsis="해적왕을 꿈꾸는 소년 루피의 모험 이야기",
            studio="토에이 애니메이션",
            episodes=1000,
            rating=9.5,
            image_url="https://example.com/onepiece.jpg"
        ),
        Anime(
            title="나루토",
            genre="액션, 모험",
            aired_date=datetime(2002, 10, 3),
            synopsis="닌자의 꿈을 향해 달리는 소년의 이야기",
            studio="스튜디오 피에로",
            episodes=720,
            rating=9.0,
            image_url="https://example.com/naruto.jpg"
        ),
        Anime(
            title="귀멸의 칼날",
            genre="액션, 판타지",
            aired_date=datetime(2019, 4, 6),
            synopsis="가족을 지키기 위한 탄지로의 여정",
            studio="유포테이블",
            episodes=26,
            rating=9.3,
            image_url="https://example.com/kimetsu.jpg"
        )
    ]
    
    try:
        # 기존 데이터가 있는지 확인
        existing = db.query(Anime).first()
        if existing:
            return {"message": "샘플 데이터가 이미 존재합니다"}
            
        # 데이터 추가
        for anime in sample_animes:
            db.add(anime)
        db.commit()
        return {"message": f"{len(sample_animes)}개의 샘플 애니메이션이 추가되었습니다"}
        
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@app.get("/test/check-db")
async def check_database(db: Session = Depends(get_db)):
    """데이터베이스 상태를 확인합니다"""
    try:
        anime_count = db.query(func.count(Anime.id)).scalar()
        api_keys_count = db.query(func.count(APIKeys.id)).scalar()
        active_keys = db.query(func.count(APIKeys.id)).filter(APIKeys.is_active == 1).scalar()
        
        return {
            "status": "정상",
            "애니메이션 수": anime_count,
            "총 API 키 수": api_keys_count,
            "활성화된 API 키 수": active_keys,
            "데이터베이스 위치": DATABASE_URL
        }
    except Exception as e:
        return {"status": "오류", "error": str(e)}

@app.get("/test/list-keys")
async def list_api_keys(db: Session = Depends(get_db)):
    """등록된 API 키들을 확인합니다"""
    try:
        keys = db.query(APIKeys).all()
        return [{
            "key": key.key,
            "user_id": key.user_id,
            "created_at": key.created_at,
            "is_active": key.is_active == 1
        } for key in keys]
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/clear-db")
async def clear_database(db: Session = Depends(get_db)):
    """주의: 모든 데이터를 삭제합니다"""
    try:
        db.query(Anime).delete()
        db.commit()
        return {"message": "모든 애니메이션 데이터가 삭제되었습니다"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    # 데이터베이스 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)
