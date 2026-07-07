from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from collections import defaultdict, deque
import uuid
import time

app = FastAPI()

EMAIL = "24f1002853@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-gxpafu.example.com"

RATE_LIMIT = 12
WINDOW = 10  # seconds

client_requests = defaultdict(deque)


# ---------------------------
# Request Context Middleware
# ---------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# ---------------------------
# Rate Limiter Middleware
# ---------------------------
@app.middleware("http")
async def rate_limiter(request: Request, call_next):

    client = request.headers.get("X-Client-Id")

    if client:

        now = time.time()

        q = client_requests[client]

        while q and now - q[0] > WINDOW:
            q.popleft()

        if len(q) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        q.append(now)

    return await call_next(request)


# ---------------------------
# Root
# ---------------------------
@app.get("/")
async def root():
    return {"status": "running"}


# ---------------------------
# CORS Preflight
# ---------------------------
@app.options("/ping")
async def ping_options(request: Request):

    origin = request.headers.get("origin")

    if origin == ALLOWED_ORIGIN:
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )

    return Response(status_code=403)


# ---------------------------
# Ping
# ---------------------------
@app.get("/ping")
async def ping(request: Request):

    response = JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request.state.request_id,
        }
    )

    origin = request.headers.get("origin")

    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["X-Request-ID"] = request.state.request_id

    return response
