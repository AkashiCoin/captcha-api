from config import PORT, HOST
from router import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host=HOST, port=PORT)
