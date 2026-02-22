from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    holder_name: str = "AMY VANESSA DAVIS"
    account_number: str = "215979558875"
    routing_number: str = "101019644"
    holder_address: str = "PTB 24692, Jalan Senyum, Johor Bahru, Johor 80300"
    bank_name: str = "Lead Bank in the USA"
    bank_address: str = "1801 Main St., Kansas City, MO 64108"
    country: str = "USA"
    balance: float = 0.95
    currency: str = "USD"
    # Personal details
    first_name: str = ""
    last_name: str = ""
    date_of_birth: str = ""
    email: str = ""
    phone_number: str = ""
    address: str = ""


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tx_type: str = "sent"  # sent / received / fee
    amount: float = 0.0
    currency: str = "USD"
    counterparty: str = ""
    date: str = ""
    description: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- Pydantic schemas for API ---

class AccountUpdate(SQLModel):
    holder_name: Optional[str] = None
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    holder_address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_address: Optional[str] = None
    country: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class TransactionCreate(SQLModel):
    tx_type: str = "sent"
    amount: float = 0.0
    currency: str = "USD"
    counterparty: str = ""
    date: str = ""
    description: str = ""


class TransactionUpdate(SQLModel):
    tx_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    counterparty: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
