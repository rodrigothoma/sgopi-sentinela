from fastapi import FastAPI

app = FastAPI(title="SGOPI Sentinela")


@app.get("/")
def read_root():
    return {"status": "SGOPI Sentinela API rodando"}
