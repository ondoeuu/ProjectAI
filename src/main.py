from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router as documents_router

app = FastAPI(
    title="Document Processing API",
    description="API pro automatické zpracování a vytěžování dat z firemních dokumentů.",
    version="1.0.0"
)

# Nastavení CORS (pokud by se budoucí frontend připojoval z jiné domény)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])

@app.get("/")
def root():
    return {"message": "Vítejte v Document Processing API. Přejděte na /docs pro Swagger dokumentaci."}

if __name__ == "__main__":
    import uvicorn
    # Pro lokální vývoj spustíme uvicorn přímo
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)
