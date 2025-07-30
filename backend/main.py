// Placeholder for main.py
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import stripe
import jwt
import asyncpg
import uvicorn

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # your Supabase JWT secret
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

stripe.api_key = STRIPE_SECRET_KEY

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB pool will be set on startup
db_pool = None


async def get_db_pool():
    return db_pool


async def verify_supabase_jwt(token: str = Header(...)):
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience=SUPABASE_URL)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Supabase JWT token")


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)


@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()


@app.post("/api/remove-vocals")
async def remove_vocals(
    file: UploadFile = File(...),
    user=Depends(verify_supabase_jwt),
    db=Depends(get_db_pool),
):
    user_id = user["sub"]

    # Check user credits
    async with db.acquire() as conn:
        credits = await conn.fetchval("SELECT credits FROM users WHERE id = $1", user_id)
        if credits is None:
            raise HTTPException(status_code=400, detail="User not found")
        if credits < 1:
            raise HTTPException(status_code=402, detail="Insufficient credits")

    # Save uploaded file temporarily
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    # TODO: Call your vocal remover logic here (e.g., Spleeter)
    # For demo, just simulate processing:
    output_path = f"/tmp/processed_{file.filename}"
    with open(output_path, "wb") as f:
        f.write(content)  # No real processing for demo

    # Deduct one credit and log usage
    async with db.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE users SET credits = credits - 1 WHERE id = $1", user_id
            )
            await conn.execute(
                "INSERT INTO usage_logs(user_id, action, details) VALUES ($1, $2, $3)",
                user_id,
                "vocal_remove",
                f"Processed file {file.filename}",
            )

    # Return response (ideally, you’d return a URL or processed file, here dummy)
    return {"message": f"File {file.filename} processed successfully. 1 credit deducted."}


@app.get("/api/credits")
async def get_credits(user=Depends(verify_supabase_jwt), db=Depends(get_db_pool)):
    user_id = user["sub"]
    async with db.acquire() as conn:
        credits = await conn.fetchval("SELECT credits FROM users WHERE id = $1", user_id)
        return {"credits": credits}


@app.get("/api/usage")
async def get_usage(user=Depends(verify_supabase_jwt), db=Depends(get_db_pool)):
    user_id = user["sub"]
    async with db.acquire() as conn:
        rows = await conn.fetch(
            "SELECT action, details, created_at FROM usage_logs WHERE user_id = $1 ORDER BY created_at DESC LIMIT 20",
            user_id,
        )
        usage = [
            {"action": r["action"], "details": r["details"], "timestamp": r["created_at"].isoformat()}
            for r in rows
        ]
        return {"usage": usage}


@app.post("/api/create-checkout-session")
async def create_checkout_session(user=Depends(verify_supabase_jwt)):
    # Create Stripe Checkout Session for purchasing credits
    YOUR_DOMAIN = "http://localhost:3000"
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": "price_1Hxxxxxx",  # Replace with your Stripe Price ID
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=YOUR_DOMAIN + "/dashboard?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=YOUR_DOMAIN + "/dashboard",
        metadata={"user_id": user["sub"]},
    )
    return {"id": session.id}


@app.post("/api/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        amount_paid = session["amount_total"] / 100  # in dollars
        credits_to_add = int(amount_paid * 10)  # Example: $1 = 10 credits

        # Update user credits in DB
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE users SET credits = credits + $1 WHERE id = $2",
                    credits_to_add,
                    user_id,
                )

    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
