#!/usr/bin/env python3
"""
UNIFIED BOT - FIXED FOR $100-200 CAPITAL
=========================================
Key fixes:
1. Fixed over-commitment (was 115%, now 90%)
2. Added SmartExecution to ALL order methods
3. Added minimum order size check ($10 minimum)
4. Reduced check_interval (600s -> 30s)
5. Disabled PPO for small capital (untrained model = random decisions)
6. Added reserve capital tracking
7. Fixed fee calculation (maker 0.015% not 0.06%)
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np

# Disable PPO for small capital - untrained model causes random trades
USE_PPO = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION - FIXED FOR $100-200
# ============================================================
@dataclass
class BotConfig:
    """Configuration optimized for $100-200 capital"""
    
    # Capital
    initial_capital: float = 150.0
    reserve_pct: float = 0.10  # 10% always kept in reserve
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = True
    max_daily_loss_pct: float = 0.05  # 5% daily loss limit (was 10%)
    max_drawdown_pct: float = 0.15    # 15% max drawdown (was 25%)
    max_consecutive_losses: int = 2   # Stop after 2 losses (was 3)
    circuit_cooldown_minutes: int = 240  # 4h cooldown (was 1h)
    
    # Position Sizing - Total = 90% (10% reserve)
    short_leverage: float = 5.0       # 5x leverage (was 3x)
    short_position_pct: float = 0.30  # 30% per short (was 40%)
    short_max_positions: int = 1      # Max 1 short (was 2)
    
    long_position_pct: float = 0.30   # 30% per long (was 35%)
    max_grid_positions: int = 2       # Max 2 grid levels (was 3)
    
    trend_follow_position_pct: float = 0.30  # 30% (was 40%)
    
    # Entry/Exit Thresholds
    short_bounce_threshold: float = 0.015  # 1.5% bounce to short
    short_tp: float = 0.015                # 1.5% TP (was 4%)
    short_sl: float = 0.02                 # 2% SL (was 2.5%)
    
    long_grid_spacing: float = 0.008       # 0.8% spacing (was 1.2%)
    long_markup: float = 0.008             # 0.8% markup
    
    # Timing
    check_interval: int = 30  # 30 seconds (was 600)
    
    # Fees
    maker_fee: float = 0.00015  # 0.015% maker fee
    taker_fee: float = 0.00045  # 0.045% taker fee
    use_maker_only: bool = True  # Only use maker orders
    
    # Exchange
    exchange: str = "hyperliquid"
    symbol: str = "BTC/USDC:USDC"
    testnet: bool = True
    
    # Minimum order size
    min_order_size_usd: float = 10.0  # Minimum $10 per order
    
    @property
    def max_allocated_pct(self) -> float:
        """Maximum capital that can be allocated"""
        return 1.0 - self.reserve_pct  # 90%


# ============================================================
# SMART EXECUTION - MAKER FEE OPTIMIZATION
# ============================================================
class SmartExecution:
    """Execute orders with maker fee optimization (0.015% vs 0.045%)"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.maker_fee = config.maker_fee  # 0.015%
        self.taker_fee = config.taker_fee  # 0.045%
    
    def calculate_fee(self, amount_usd: float, is_maker: bool = True) -> float:
        """Calculate trading fee"""
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        return amount_usd * fee_rate


# ============================================================
# POSITION TRACKER
# ============================================================
class PositionTracker:
    """Track positions and calculate available capital"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.positions_long: List[Dict] = []
        self.positions_short: List[Dict] = []
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        self.consecutive_losses: int = 0
        self.last_reset: datetime = datetime.now()
        self.total_fees: float = 0.0
        self.wins: int = 0
        self.losses: int = 0
        
    @property
    def used_capital(self) -> float:
        """Total capital currently in positions"""
        long_used = sum(p.get('size_usd', 0) for p in self.positions_long)
        short_used = sum(p.get('size_usd', 0) for p in self.positions_short)
        return long_used + short_used
    
    def available_capital(self, current_balance: float) -> float:
        """Capital available for new positions (respects reserve)"""
        max_allocatable = current_balance * self.config.max_allocated_pct
        return max(0, max_allocatable - self.used_capital)
    
    def can_open_position(self, size_usd: float, current_balance: float) -> bool:
        """Check if we can open a new position"""
        # Check minimum size
        if size_usd < self.config.min_order_size_usd:
            return False
        
        # Check available capital
        available = self.available_capital(current_balance)
        if size_usd > available:
            return False
        
        return True
    
    def add_position(self, position: Dict, is_short: bool = False):
        """Add a new position"""
        if is_short:
            self.positions_short.append(position)
        else:
            self.positions_long.append(position)
        self.daily_trades += 1
    
    def close_position(self, position_id: str, pnl: float, fee: float, is_short: bool = False):
        """Close a position and track PnL"""
        positions = self.positions_short if is_short else self.positions_long
        
        for i, p in enumerate(positions):
            if p.get('id') == position_id:
                positions.pop(i)
                break
        
        self.daily_pnl += pnl
        self.total_fees += fee
        
        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1
            self.consecutive_losses += 1
    
    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should trigger"""
        if not self.config.circuit_breaker_enabled:
            return False
        
        # Check daily loss
        daily_loss_pct = abs(self.daily_pnl) / self.config.initial_capital
        if daily_loss_pct >= self.config.max_daily_loss_pct:
            return True
        
        # Check consecutive losses
        if self.consecutive_losses >= self.config.max_consecutive_losses:
            return True
        
        return False
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.last_reset = datetime.now()


# ============================================================
# UNIFIED BOT - FIXED VERSION (BACKTEST MODE)
# ============================================================
class UnifiedBot:
    """Trading bot optimized for $100-200 capital"""
    
    def __init__(self, config: BotConfig = None):
        self.config = config or BotConfig()
        self.tracker = PositionTracker(self.config)
        self.execution = SmartExecution(self.config)
        
        # Market data
        self.prices: List[float] = []
        self.highs: List[float] = []
        self.lows: List[float] = []
        
        # Circuit breaker state
        self.circuit_breaker_active: bool = False
        self.circuit_breaker_until: Optional[datetime] = None
        
        # Balance tracking
        self.current_balance: float = self.config.initial_capital
    
    def calculate_position_size(self, pct_of_capital: float, current_price: float) -> tuple:
        """Calculate position size with minimum check"""
        size_usd = self.current_balance * pct_of_capital
        
        # Check minimum
        if size_usd < self.config.min_order_size_usd:
            return 0, 0
        
        size_coin = size_usd / current_price
        return size_coin, size_usd
    
    def open_short(self, price: float) -> Optional[Dict]:
        """Open short position"""
        if self.circuit_breaker_active:
            return None
        
        # Check position limit
        if len(self.tracker.positions_short) >= self.config.short_max_positions:
            return None
        
        # Calculate size
        size_coin, size_usd = self.calculate_position_size(
            self.config.short_position_pct, price
        )
        
        if size_usd == 0:
            return None
        
        # Check if we can open
        if not self.tracker.can_open_position(size_usd, self.current_balance):
            return None
        
        # Calculate fee
        fee = self.execution.calculate_fee(size_usd, is_maker=True)
        
        position = {
            'id': f"short_{time.time()}_{np.random.randint(1000)}",
            'side': 'short',
            'entry': price,
            'size': size_coin,
            'size_usd': size_usd,
            'leverage': self.config.short_leverage,
            'opened_at': datetime.now(),
            'fee': fee
        }
        self.tracker.add_position(position, is_short=True)
        self.tracker.total_fees += fee
        return position
    
    def open_long_grid(self, price: float) -> Optional[Dict]:
        """Open long grid position"""
        if self.circuit_breaker_active:
            return None
        
        # Check position limit
        if len(self.tracker.positions_long) >= self.config.max_grid_positions:
            return None
        
        # Calculate size
        size_coin, size_usd = self.calculate_position_size(
            self.config.long_position_pct, price
        )
        
        if size_usd == 0:
            return None
        
        # Check if we can open
        if not self.tracker.can_open_position(size_usd, self.current_balance):
            return None
        
        # Calculate fee
        fee = self.execution.calculate_fee(size_usd, is_maker=True)
        
        position = {
            'id': f"long_{time.time()}_{np.random.randint(1000)}",
            'side': 'long',
            'entry': price,
            'size': size_coin,
            'size_usd': size_usd,
            'opened_at': datetime.now(),
            'fee': fee
        }
        self.tracker.add_position(position, is_short=False)
        self.tracker.total_fees += fee
        return position
    
    def check_tp_sl(self, current_price: float):
        """Check take profit and stop loss"""
        # Check long positions
        for pos in self.tracker.positions_long[:]:
            entry = pos['entry']
            tp_price = entry * (1 + self.config.long_markup)
            sl_price = entry * (1 - self.config.short_sl)
            
            # Take profit
            if current_price >= tp_price:
                pnl = (current_price - entry) / entry * pos['size_usd']
                fee = self.execution.calculate_fee(pos['size_usd'], is_maker=True)
                net_pnl = pnl - fee
                
                self.current_balance += net_pnl
                self.tracker.close_position(pos['id'], net_pnl, fee, is_short=False)
            
            # Stop loss
            elif current_price <= sl_price:
                pnl = (current_price - entry) / entry * pos['size_usd']
                fee = self.execution.calculate_fee(pos['size_usd'], is_maker=True)
                net_pnl = pnl - fee
                
                self.current_balance += net_pnl
                self.tracker.close_position(pos['id'], net_pnl, fee, is_short=False)
        
        # Check short positions
        for pos in self.tracker.positions_short[:]:
            entry = pos['entry']
            tp_price = entry * (1 - self.config.short_tp)
            sl_price = entry * (1 + self.config.short_sl)
            
            # Take profit (price went down)
            if current_price <= tp_price:
                pnl = (entry - current_price) / entry * pos['size_usd'] * self.config.short_leverage
                fee = self.execution.calculate_fee(pos['size_usd'] * self.config.short_leverage, is_maker=True)
                net_pnl = pnl - fee
                
                self.current_balance += net_pnl
                self.tracker.close_position(pos['id'], net_pnl, fee, is_short=True)
            
            # Stop loss (price went up)
            elif current_price >= sl_price:
                pnl = (entry - current_price) / entry * pos['size_usd'] * self.config.short_leverage
                fee = self.execution.calculate_fee(pos['size_usd'] * self.config.short_leverage, is_maker=True)
                net_pnl = pnl - fee
                
                self.current_balance += net_pnl
                self.tracker.close_position(pos['id'], net_pnl, fee, is_short=True)
    
    def check_entry_signals(self, current_price: float):
        """Check for entry signals - FIXED: bounce from min/max"""
        if len(self.prices) < 24:
            return
        
        # Get last 24 prices for context
        recent_prices = self.prices[-24:]
        
        # SHORT signal: price bounced UP from recent low
        recent_low = min(recent_prices)
        bounce = (current_price - recent_low) / recent_low if recent_low > 0 else 0
        
        if bounce >= self.config.short_bounce_threshold:
            self.open_short(current_price)
        
        # LONG signal: price dipped from recent high
        recent_high = max(recent_prices)
        dip = (recent_high - current_price) / recent_high if recent_high > 0 else 0
        
        if dip >= self.config.long_grid_spacing:
            self.open_long_grid(current_price)
    
    def check_circuit_breaker(self):
        """Check and manage circuit breaker"""
        # Check if we should activate
        if not self.circuit_breaker_active:
            if self.tracker.check_circuit_breaker():
                self.circuit_breaker_active = True
                self.circuit_breaker_until = datetime.now() + timedelta(
                    minutes=self.config.circuit_cooldown_minutes
                )
        
        # Check if we should deactivate
        else:
            if datetime.now() >= self.circuit_breaker_until:
                self.circuit_breaker_active = False
                self.circuit_breaker_until = None
                self.tracker.reset_daily_stats()
    
    def run_cycle(self, current_price: float):
        """Single trading cycle"""
        # Update prices
        self.prices.append(current_price)
        if len(self.prices) > 200:
            self.prices = self.prices[-150:]
        
        # Check circuit breaker
        self.check_circuit_breaker()
        
        # Check TP/SL for existing positions
        self.check_tp_sl(current_price)
        
        # Check entry signals
        self.check_entry_signals(current_price)
    
    def get_stats(self) -> Dict:
        """Get trading statistics"""
        total_trades = self.tracker.wins + self.tracker.losses
        win_rate = self.tracker.wins / total_trades if total_trades > 0 else 0
        
        # Calculate profit factor
        gross_profit = sum(p.get('pnl', 0) for p in self.tracker.positions_long + self.tracker.positions_short if p.get('pnl', 0) > 0)
        gross_loss = abs(sum(p.get('pnl', 0) for p in self.tracker.positions_long + self.tracker.positions_short if p.get('pnl', 0) < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Calculate return
        total_return = (self.current_balance - self.config.initial_capital) / self.config.initial_capital
        
        return {
            'initial_capital': self.config.initial_capital,
            'final_balance': self.current_balance,
            'total_return': total_return,
            'total_trades': total_trades,
            'wins': self.tracker.wins,
            'losses': self.tracker.losses,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_fees': self.tracker.total_fees,
            'consecutive_losses': self.tracker.consecutive_losses
        }


# ============================================================
# BACKTEST RUNNER
# ============================================================
def run_backtest(prices: List[float], config: BotConfig = None) -> Dict:
    """Run backtest with fixed bot"""
    bot = UnifiedBot(config)
    
    for i, price in enumerate(prices):
        bot.run_cycle(price)
    
    return bot.get_stats()


if __name__ == "__main__":
    # Example usage
    config = BotConfig()
    print(f"Bot initialized with ${config.initial_capital} capital")
