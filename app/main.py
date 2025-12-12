from fastapi import FastAPI, Depends
from app.db.session import get_db, engine
from app.db.base import Base
from app.config.firebase import init_firebase
from app.routes import auth
from app.routes import batch 


async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)
    
    init_firebase()

    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(batch.router)


@app.get("/")
def root():
    return {"message": "API running"}
