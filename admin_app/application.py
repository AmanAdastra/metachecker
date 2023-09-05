import uvicorn


def app(scope, receive, send):
    ...
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=4004,reload=True, log_level="info",env_file=".env")