from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
import uuid
import time

app = FastAPI()

EMAIL = "24f1002853@ds.study.iitm.ac.in"

# Allowed origins
ALLOWED_ORIGINS = [
    "https://app-gxpafu.example.com",
    "https://tds.s-anand.net",
    "https://exam.s-anand.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Rate Limiting
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
# Root Endpoint
# ---------------------------
@app.get("/")
async def root():
    return {"status": "running"}


# ---------------------------
# Ping Endpoint
# ---------------------------
@app.get("/ping")
async def ping(request: Request):

    return JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request.state.request_id,
        },
        headers={
            "X-Request-ID": request.state.request_id,
        },
    )
