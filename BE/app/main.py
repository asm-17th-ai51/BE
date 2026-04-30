from fastapi import FastAPI


app = FastAPI(
    title="BE API",
    description="Basic FastAPI application",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "Hello, FastAPI"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
