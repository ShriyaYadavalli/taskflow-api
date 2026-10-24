from fastapi import FastAPI

app = FastAPI(title="TaskFlow API")

@app.get("/")
def root():
    return {"message": "Welcome to TaskFlow API"}

@app.get("/health")
def health_check():
    return{"status": "healthy"}
