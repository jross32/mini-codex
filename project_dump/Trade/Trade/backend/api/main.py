from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import asyncio
import threading
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from backend.config import Config
from backend.logger import logger
from backend.database import Base, engine, get_db
from backend.models.user import User
from backend.schemas.auth import UserSignUp, UserLogin, UserResponse, AuthToken
from backend.auth import create_access_token, verify_token, hash_password, verify_password

# Safely import trading modules
try:
    from backend.data import DataFetcher
    from backend.strategy import get_strategy
    from backend.trading import TradingBot
    from backend.backtest import Backtester
except ImportError as e:
    logger.warning(f"Could not import trading modules: {e}")
    DataFetcher = None
    get_strategy = None
    TradingBot = None
    Backtester = None

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Crypto Trading Bot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot_instance = None
bot_thread = None
bot_running = False

# Request/Response models
class BotConfig(BaseModel):
    strategy: str = "ma_crossover"
    symbol: str = Config.TARGET_CRYPTO
    initial_balance: float = Config.INITIAL_BALANCE
    use_paper_trading: bool = True
    amount_per_trade: float = 0.001

class BacktestRequest(BaseModel):
    strategy: str = "ma_crossover"
    symbol: str = Config.TARGET_CRYPTO
    timeframe: str = "1h"
    candles: int = 500

class TradeResponse(BaseModel):
    timestamp: datetime
    type: str
    price: float
    amount: float
    balance: float

class BotStatsResponse(BaseModel):
    initial_balance: float
    current_balance: float
    portfolio_value: float
    total_pnl: float
    total_pnl_percent: float
    open_positions: int
    closed_positions: int
    win_rate: float
    total_trades: int

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now()}

@app.post("/bot/start")
async def start_bot(config: BotConfig):
    """Start the trading bot"""
    global bot_instance, bot_running
    
    try:
        if bot_running:
            raise HTTPException(status_code=400, detail="Bot is already running")
        
        logger.info(f"Starting bot with strategy: {config.strategy}")
        
        # Initialize components
        data_fetcher = DataFetcher()
        strategy = get_strategy(config.strategy)
        
        # Create bot
        bot_instance = TradingBot(
            strategy=strategy,
            data_fetcher=data_fetcher,
            use_paper_trading=config.use_paper_trading,
            initial_balance=config.initial_balance,
            symbol=config.symbol
        )
        
        bot_running = True
        
        return {
            "status": "started",
            "strategy": config.strategy,
            "symbol": config.symbol,
            "balance": config.initial_balance,
            "mode": "paper_trading" if config.use_paper_trading else "live_trading"
        }
    
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    global bot_instance, bot_running
    
    try:
        if not bot_running:
            raise HTTPException(status_code=400, detail="Bot is not running")
        
        bot_running = False
        bot_instance = None
        
        logger.info("Bot stopped")
        return {"status": "stopped"}
    
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bot/run-iteration")
async def run_bot_iteration(amount: float = 0.001):
    """Run a single bot iteration"""
    global bot_instance
    
    try:
        if not bot_instance or not bot_running:
            raise HTTPException(status_code=400, detail="Bot is not running")
        
        success = bot_instance.run_iteration(amount)
        
        if not success:
            raise HTTPException(status_code=500, detail="Bot iteration failed")
        
        stats = bot_instance.get_stats()
        
        return {
            "status": "completed",
            "stats": stats
        }
    
    except Exception as e:
        logger.error(f"Error running bot iteration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bot/stats")
async def get_bot_stats():
    """Get current bot statistics"""
    global bot_instance
    
    try:
        if not bot_instance:
            raise HTTPException(status_code=400, detail="Bot not initialized")
        
        stats = bot_instance.get_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run strategy backtest"""
    try:
        logger.info(f"Starting backtest with {request.strategy} strategy")
        
        # Fetch data
        data_fetcher = DataFetcher()
        df = data_fetcher.fetch_ohlcv(
            symbol=request.symbol,
            timeframe=request.timeframe,
            limit=request.candles
        )
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No data available for backtest")
        
        # Create strategy
        strategy = get_strategy(request.strategy)
        
        # Run backtest
        backtester = Backtester(initial_balance=Config.INITIAL_BALANCE, symbol=request.symbol)
        results = backtester.run(df, strategy)
        
        logger.info(f"Backtest completed: P&L={results['total_pnl']:.2f}")
        
        return {
            "strategy": request.strategy,
            "symbol": request.symbol,
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/price/{symbol}")
async def get_market_price(symbol: str = "BTC/USDT"):
    """Get current market price"""
    try:
        data_fetcher = DataFetcher()
        price_data = data_fetcher.fetch_current_price(symbol)
        
        if not price_data:
            raise HTTPException(status_code=400, detail=f"Could not fetch price for {symbol}")
        
        return price_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/data/{symbol}")
async def get_market_data(symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 100):
    """Get OHLCV data"""
    try:
        data_fetcher = DataFetcher()
        df = data_fetcher.fetch_ohlcv(symbol, timeframe, limit)
        
        if df.empty:
            raise HTTPException(status_code=400, detail=f"No data for {symbol}")
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": len(df),
            "data": df.to_dict(orient='records')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies")
async def get_available_strategies():
    """Get list of available strategies"""
    return {
        "strategies": [
            "ma_crossover",
            "rsi",
            "ml",
            "hybrid"
        ]
    }


# ===== AUTH ENDPOINTS =====

@app.post("/api/auth/signup", response_model=AuthToken)
def signup(user_data: UserSignUp, db: Session = Depends(get_db)):
    """Sign up a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token
    token = create_access_token({"sub": new_user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(new_user)
    }


@app.post("/api/auth/login", response_model=AuthToken)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login a user"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_access_token({"sub": user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user(token: str = None, db: Session = Depends(get_db)):
    """Get current user info (requires token in header or query)"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.from_orm(user)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
