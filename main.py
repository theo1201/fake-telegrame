from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Cookie, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import secrets

from database import engine, init_db, get_session
from models import (
    Account, AccountUpdate,
    Transaction, TransactionCreate, TransactionUpdate,
)

# 简单的 session 存储（生产环境应该使用 Redis 等）
active_sessions = set()


# --------------- Seed default data ---------------

def seed_data():
    """Seed default data. Safe to call multiple times."""
    try:
        # Ensure tables exist before querying
        # init_db() should have been called in lifespan, but call it again to be safe
        init_db()
        
        # Small delay to ensure tables are created (for serverless environments)
        import time
        time.sleep(0.1)
        
        with Session(engine) as session:
            # Check if account table exists by trying to query it
            # If it fails, the table doesn't exist yet
            try:
                account = session.exec(select(Account)).first()
            except Exception as e:
                # If table doesn't exist, log and return (don't crash)
                # This can happen in serverless cold starts
                print(f"Seed data warning (may be normal): {e}")
                # Try to create tables one more time
                try:
                    init_db()
                    time.sleep(0.1)
                    account = session.exec(select(Account)).first()
                except Exception as e2:
                    # If still fails, just return - seeding will happen on next request
                    print(f"Error: Could not query account table after retry: {e2}")
                    return
            
            # Only seed if no account exists
            if not account:
                account = Account(
                    holder_name="AMY VANESSA DAVIS",
                    account_number="215979558875",
                    routing_number="101019644",
                    holder_address="PTB 24692, Jalan Senyum, Johor Bahru, Johor 80300",
                    bank_name="Lead Bank in the USA",
                    bank_address="1801 Main St., Kansas City, MO 64108",
                    country="USA",
                    balance=0.95,
                    currency="USD",
                    first_name="Minlan",
                    last_name="Zhou",
                    date_of_birth="3 Dec 1998",
                    email="rxehjqv4297@hotmail.com",
                    phone_number="+18633890587",
                    address="123 Main St, San Francisco, CA 94102",
                )
                session.add(account)

                transactions = [
                    Transaction(
                        tx_type="sent",
                        amount=48.05,
                        currency="USD",
                        counterparty="AZVQ...C8bB",
                        date="08 Feb - 01:44 PM",
                        description="Sent",
                        created_at="2024-02-08T13:44:00",
                    ),
                    Transaction(
                        tx_type="received",
                        amount=49.00,
                        currency="USDT",
                        counterparty="TK4y...n3qJ",
                        date="08 Feb - 01:41 PM",
                        description="Received",
                        created_at="2024-02-08T13:41:00",
                    ),
                    Transaction(
                        tx_type="fee",
                        amount=0.00,
                        currency="USD",
                        counterparty="",
                        date="04 Feb - 02:03 AM",
                        description="Card fee",
                        created_at="2024-02-04T02:03:00",
                    ),
                ]
                for tx in transactions:
                    session.add(tx)

                session.commit()
    except Exception as e:
        # If seeding fails, log but don't crash the app
        import traceback
        print(f"Error seeding data (non-fatal): {e}")
        traceback.print_exc()


# --------------- App lifecycle ---------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database and seed data on startup
    # This works in both local and serverless environments
    try:
        init_db()
        seed_data()
    except Exception as e:
        # Log but don't crash - database might already be initialized
        import traceback
        print(f"Lifespan init warning (may be normal): {e}")
        traceback.print_exc()
    yield


app = FastAPI(title="KAST Bank Admin", lifespan=lifespan)

# CORS – allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use absolute path for templates to work in both local and serverless environments
import os
from pathlib import Path

# Get the directory where main.py is located
_main_dir = Path(__file__).parent.resolve()
templates_dir = _main_dir / "templates"

# Ensure templates directory exists
# In serverless, the working directory might be different
if not templates_dir.exists():
    # Fallback: try relative to current working directory
    cwd_templates = Path.cwd() / "templates"
    if cwd_templates.exists():
        templates_dir = cwd_templates
    else:
        # Last resort: try parent directory
        parent_templates = Path.cwd().parent / "templates"
        if parent_templates.exists():
            templates_dir = parent_templates
        else:
            # Debug: log available paths
            print(f"Warning: Templates directory not found!")
            print(f"  Tried: {_main_dir / 'templates'}")
            print(f"  Tried: {Path.cwd() / 'templates'}")
            print(f"  Tried: {Path.cwd().parent / 'templates'}")
            print(f"  Current working directory: {Path.cwd()}")
            print(f"  __file__ location: {_main_dir}")
            # Use the first path anyway (might work if files are in a different location)
            templates_dir = _main_dir / "templates"

print(f"Using templates directory: {templates_dir} (exists: {templates_dir.exists()})")
templates = Jinja2Templates(directory=str(templates_dir))


# ============================================================
#  API  –  /api/...
# ============================================================

# ---------- Account ----------

@app.get("/api/account")
def get_account(session: Session = Depends(get_session)):
    account = session.exec(select(Account)).first()
    if not account:
        raise HTTPException(404, "Account not found")
    return account


@app.put("/api/account")
def update_account(data: AccountUpdate, session: Session = Depends(get_session)):
    account = session.exec(select(Account)).first()
    if not account:
        raise HTTPException(404, "Account not found")

    update_fields = data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(account, key, value)

    session.add(account)
    session.commit()
    session.refresh(account)
    return account


# ---------- Transactions ----------

@app.get("/api/transactions")
def list_transactions(session: Session = Depends(get_session)):
    txs = session.exec(select(Transaction).order_by(Transaction.created_at.desc())).all()
    return txs


@app.delete("/api/transactions/clear")
def clear_all_transactions(session: Session = Depends(get_session)):
    """清空所有交易记录"""
    transactions = session.exec(select(Transaction)).all()
    count = len(transactions)
    
    for tx in transactions:
        session.delete(tx)
    
    session.commit()
    
    return {
        "message": f"Cleared {count} transactions",
        "cleared": count
    }


@app.post("/api/transactions/generate")
def generate_transactions(
    min_count: int = 10,
    max_amount: float = 100.0,
    min_sent_count: int = 0,
    start_time: str | None = None,
    session: Session = Depends(get_session)
):
    """自动生成交易流水，使余额达到当前设置的目标金额
    
    Args:
        min_count: 最少生成多少笔交易（默认10笔）
        max_amount: 单笔交易最大金额（默认100.0）
        min_sent_count: 最少生成多少笔支出交易（默认0笔）
        start_time: 开始时间（ISO 格式，如 2024-01-15T14:30），留空则从 30 天前开始
    """
    from datetime import datetime, timedelta
    import random
    
    account = session.exec(select(Account)).first()
    if not account:
        raise HTTPException(404, "Account not found")
    
    # 获取当前实际余额（通过计算所有交易）
    transactions = session.exec(select(Transaction)).all()
    actual_balance = 0.0
    for tx in transactions:
        if tx.tx_type == "received":
            actual_balance += tx.amount
        elif tx.tx_type == "sent":
            actual_balance += tx.amount  # 已经是负数了
    
    # 目标余额是账户设置的余额
    target_balance = account.balance
    difference = target_balance - actual_balance
    
    if abs(difference) < 0.01:
        return {"message": "Balance already matches target", "generated": 0}
    
    if min_count < 1:
        raise HTTPException(400, "min_count must be at least 1")
    
    if max_amount <= 0:
        raise HTTPException(400, "max_amount must be greater than 0")
    
    if min_sent_count < 0:
        raise HTTPException(400, "min_sent_count must be non-negative")
    
    if min_sent_count > min_count:
        raise HTTPException(400, "min_sent_count cannot be greater than min_count")
    
    # 时间范围：可指定开始时间，或默认最近 30 天
    now_us = datetime.now()
    if start_time:
        try:
            # 解析 ISO 格式，精确到分钟（如 2024-01-15T14:30）
            earliest_time = datetime.fromisoformat(start_time.strip()[:16])
            earliest_time = earliest_time.replace(second=0, microsecond=0)
            if earliest_time > now_us:
                raise HTTPException(400, "start_time 不能晚于当前时间")
        except ValueError as e:
            raise HTTPException(400, f"start_time 格式无效: {e}")
    else:
        earliest_time = now_us - timedelta(days=30)
    
    # 生成交易
    # 如果需要增加余额（difference > 0），主要生成 received 交易
    # 如果需要减少余额（difference < 0），主要生成 sent 交易
    # 但无论如何，都要满足 min_sent_count 的要求
    
    total_amount = abs(difference)
    min_tx_amount = 0.01
    
    # 计算需要生成的收入和支出交易
    if difference > 0:
        # 需要增加余额，主要是收入交易
        # 但要生成至少 min_sent_count 笔支出
        sent_amounts = []
        received_amounts = []
        
        # 先生成支出交易
        sent_total = 0.0
        for _ in range(min_sent_count):
            amount = random.uniform(min_tx_amount, min(max_amount, total_amount * 0.3))
            amount = round(amount, 2)
            sent_amounts.append(amount)
            sent_total += amount
        
        # 收入交易需要覆盖：目标差额 + 支出总额
        received_total_needed = total_amount + sent_total
        
        # 生成收入交易
        remaining = received_total_needed
        received_count = max(1, min_count - min_sent_count)
        
        while remaining > min_tx_amount and len(received_amounts) < received_count:
            remaining_txs_needed = max(1, received_count - len(received_amounts))
            max_this_tx = min(max_amount, remaining - min_tx_amount * (remaining_txs_needed - 1))
            
            if max_this_tx < min_tx_amount:
                max_this_tx = min(max_amount, remaining)
            
            amount = random.uniform(min_tx_amount, max_this_tx)
            amount = round(amount, 2)
            
            if amount > remaining:
                amount = remaining
            
            received_amounts.append(amount)
            remaining -= amount
        
        # 如果还有剩余，需要继续拆分
        while remaining > min_tx_amount:
            if remaining <= max_amount:
                received_amounts.append(round(remaining, 2))
                remaining = 0
            else:
                # 继续生成不超过 max_amount 的交易
                amount = random.uniform(max_amount * 0.5, max_amount)
                amount = round(amount, 2)
                received_amounts.append(amount)
                remaining -= amount
        
        # 处理最后的零头
        if remaining > 0 and received_amounts:
            # 如果最后一笔加上零头不超过 max_amount，就加上去
            if received_amounts[-1] + remaining <= max_amount:
                received_amounts[-1] = round(received_amounts[-1] + remaining, 2)
            else:
                # 否则作为新的一笔
                received_amounts.append(round(remaining, 2))
        
    else:
        # 需要减少余额，主要是支出交易
        sent_amounts = []
        received_amounts = []
        
        # 生成支出交易
        remaining = total_amount
        sent_count = max(min_sent_count, min_count)
        
        while remaining > min_tx_amount and len(sent_amounts) < sent_count:
            remaining_txs_needed = max(1, sent_count - len(sent_amounts))
            max_this_tx = min(max_amount, remaining - min_tx_amount * (remaining_txs_needed - 1))
            
            if max_this_tx < min_tx_amount:
                max_this_tx = min(max_amount, remaining)
            
            amount = random.uniform(min_tx_amount, max_this_tx)
            amount = round(amount, 2)
            
            if amount > remaining:
                amount = remaining
            
            sent_amounts.append(amount)
            remaining -= amount
        
        # 如果还有剩余，需要继续拆分
        while remaining > min_tx_amount:
            if remaining <= max_amount:
                sent_amounts.append(round(remaining, 2))
                remaining = 0
            else:
                # 继续生成不超过 max_amount 的交易
                amount = random.uniform(max_amount * 0.5, max_amount)
                amount = round(amount, 2)
                sent_amounts.append(amount)
                remaining -= amount
        
        # 处理最后的零头
        if remaining > 0 and sent_amounts:
            # 如果最后一笔加上零头不超过 max_amount，就加上去
            if sent_amounts[-1] + remaining <= max_amount:
                sent_amounts[-1] = round(sent_amounts[-1] + remaining, 2)
            else:
                # 否则作为新的一笔
                sent_amounts.append(round(remaining, 2))
    
    # 创建交易列表
    all_transactions = []
    
    # 添加收入交易
    for amount in received_amounts:
        # 随机时间：从earliest_time到当前时间之间
        time_range = (now_us - earliest_time).total_seconds()
        if time_range <= 0:
            # 如果时间范围无效，使用当前时间
            tx_time = now_us
        else:
            random_seconds = random.randint(0, int(time_range))
            tx_time = earliest_time + timedelta(seconds=random_seconds)
            # 对齐到分钟（去掉秒和微秒）
            tx_time = tx_time.replace(second=0, microsecond=0)
        
        # 随机地址 - 以 T 开头，T后面前四位必须是字母，后四位字母数字混合
        addr_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        prefix = "T" + ''.join(secrets.choice(letters) for _ in range(4))
        # 确保后四位至少包含一个字母和一个数字
        suffix_list = [secrets.choice(letters), secrets.choice(digits)]
        suffix_list.extend([secrets.choice(addr_chars) for _ in range(2)])
        secrets.SystemRandom().shuffle(suffix_list)
        suffix = ''.join(suffix_list)
        counterparty = f"{prefix}...{suffix}"
        
        # 格式化日期
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        date_str = f"{tx_time.day:02d} {month_names[tx_time.month-1]} - {tx_time.strftime('%I:%M %p')}"
        
        tx = Transaction(
            tx_type="received",
            amount=amount,
            currency=account.currency,
            counterparty=counterparty,
            date=date_str,
            description="Received",
            created_at=tx_time.isoformat(),
        )
        all_transactions.append(tx)
    
    # 添加支出交易
    for amount in sent_amounts:
        # 随机时间：从earliest_time到当前时间之间
        time_range = (now_us - earliest_time).total_seconds()
        if time_range <= 0:
            # 如果时间范围无效，使用当前时间
            tx_time = now_us
        else:
            random_seconds = random.randint(0, int(time_range))
            tx_time = earliest_time + timedelta(seconds=random_seconds)
            # 对齐到分钟（去掉秒和微秒）
            tx_time = tx_time.replace(second=0, microsecond=0)
        
        # 随机地址 - 以 T 开头，T后面前四位必须是字母，后四位字母数字混合
        addr_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        prefix = "T" + ''.join(secrets.choice(letters) for _ in range(4))
        # 确保后四位至少包含一个字母和一个数字
        suffix_list = [secrets.choice(letters), secrets.choice(digits)]
        suffix_list.extend([secrets.choice(addr_chars) for _ in range(2)])
        secrets.SystemRandom().shuffle(suffix_list)
        suffix = ''.join(suffix_list)
        counterparty = f"{prefix}...{suffix}"
        
        # 格式化日期
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        date_str = f"{tx_time.day:02d} {month_names[tx_time.month-1]} - {tx_time.strftime('%I:%M %p')}"
        
        tx = Transaction(
            tx_type="sent",
            amount=amount,
            currency=account.currency,
            counterparty=counterparty,
            date=date_str,
            description="Sent",
            created_at=tx_time.isoformat(),
        )
        all_transactions.append(tx)
    
    # 按时间排序（可选，让交易看起来更自然）
    all_transactions.sort(key=lambda x: x.created_at)
    
    # 保存到数据库
    for tx in all_transactions:
        session.add(tx)
    
    session.commit()
    
    return {
        "message": f"Generated {len(all_transactions)} transactions",
        "generated": len(all_transactions),
        "received_count": len(received_amounts),
        "sent_count": len(sent_amounts),
        "total_received": sum(received_amounts),
        "total_sent": sum(sent_amounts),
    }


@app.post("/api/transactions", status_code=201)
def create_transaction(data: TransactionCreate, session: Session = Depends(get_session)):
    tx = Transaction(**data.model_dump())
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@app.put("/api/transactions/{tx_id}")
def update_transaction(tx_id: int, data: TransactionUpdate, session: Session = Depends(get_session)):
    tx = session.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(404, "Transaction not found")

    update_fields = data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(tx, key, value)

    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int, session: Session = Depends(get_session)):
    tx = session.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(404, "Transaction not found")

    session.delete(tx)
    session.commit()
    return {"ok": True}


# ---------- Dashboard (combined for frontend) ----------

@app.get("/api/dashboard")
def dashboard(session: Session = Depends(get_session)):
    account = session.exec(select(Account)).first()
    txs = session.exec(select(Transaction).order_by(Transaction.created_at.desc())).all()
    return {
        "account": account,
        "transactions": txs,
    }


# ============================================================
#  Admin UI  –  /admin
# ============================================================

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    try:
        return templates.TemplateResponse("admin_login.html", {"request": request})
    except Exception as e:
        import traceback
        error_msg = f"Error rendering login page: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><pre>{error_msg}</pre></body></html>",
            status_code=500
        )


@app.post("/admin/login")
def admin_login(username: str = Form(...), password: str = Form(...)):
    # 简单的硬编码验证
    if username == "Nnn" and password == "Nnn":
        # 生成 session token
        session_token = secrets.token_urlsafe(32)
        active_sessions.add(session_token)
        
        # 设置 cookie
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key="admin_session",
            value=session_token,
            httponly=True,
            max_age=86400,  # 24小时
            samesite="lax"
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/admin/logout")
def admin_logout(response: Response, admin_session: str = Cookie(None)):
    if admin_session:
        active_sessions.discard(admin_session)
    
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, admin_session: str = Cookie(None)):
    try:
        # 检查是否已登录
        # Note: In serverless, active_sessions may not persist across invocations
        # For now, we'll allow access if session cookie exists (simple check)
        # In production, use proper session storage (Redis, database, etc.)
        if not admin_session:
            return RedirectResponse(url="/admin/login", status_code=303)
        
        # In serverless, we can't rely on in-memory sessions
        # For now, just check if cookie exists (not secure, but works for demo)
        # TODO: Implement proper session storage for production
        
        return templates.TemplateResponse("admin.html", {"request": request})
    except Exception as e:
        import traceback
        error_msg = f"Error rendering admin page: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        # Return a simple error page instead of crashing
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><pre>{error_msg}</pre></body></html>",
            status_code=500
        )


# ============================================================
#  Entry point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
