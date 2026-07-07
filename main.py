from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from collections import defaultdict, deque
import uuid
import time

app = FastAPI()

EMAIL = "24f1002853@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = {
    "https://app-gxpafu.example.com",
    "https://exam.sanand.workers.dev",
}

RATE_LIMIT = 12
WINDOW = 10

client_requests = defaultdict(deque)


# ---------------------------------------
# Middleware
# ---------------------------------------
@app.middleware("http")
async def middleware(request: Request, call_next):

    # Request ID
    request_id = request.headers.get("x-request-id")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate Limiter
    client = request.headers.get("x-client-id")

    if client:

        now = time.time()

        q = client_requests[client]

        while q and now - q[0] >= WINDOW:
            q.popleft()

        if len(q) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"X-Request-ID": request_id},
            )

        q.append(now)

    response = await call_next(request)

    # Echo SAME request id
    response.headers["X-Request-ID"] = request_id

    return response


# ---------------------------------------
# Root
# ---------------------------------------
@app.get("/")
async def root():
    return {"status": "running"}


# ---------------------------------------
# OPTIONS /ping
# ---------------------------------------
@app.options("/ping")
async def ping_options(request: Request):

    origin = request.headers.get("origin")

    if origin in ALLOWED_ORIGINS:

        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": request.headers.get(
                    "access-control-request-headers",
                    "*",
                ),
                "Vary": "Origin",
            },
        )

    return Response(status_code=403)


# ---------------------------------------
# GET /ping
# ---------------------------------------
@app.get("/ping")
async def ping(request: Request):

    response = JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request.state.request_id,
        }
    )

    origin = request.headers.get("origin")

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"

    return response
