#!/usr/bin/env python3
"""
REAL DATA BOT ANALYSIS
======================
Test both original and fixed bot on real historical data.
Identify what breaks the results.
"""

import json
import numpy as np
import sys
from datetime import datetime
from typing import List, Dict

try:
    import ccxt
    CCXT_AVAILABLE = True
except:
    CCXT_AVAILABLE = False

sys.path.insert(0, 'scripts')
from unified_bot_fixed import UnifiedBotFixed, BotConfig


def fetch_real_btc_data(days: int = 90) -> List[float]:
    """Fetch real BTC price data from Binance."""
    if not CCXT_AVAILABLE:
        print("⚠️  ccxt not available, using synthetic data")
        return generate_synthetic_data(days * 24)
    
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        
        # Get 4h candles
        limit = min(days * 6, 1000)  # 4h candles
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='4h', limit=limit)
        prices = [c[4] for c in ohlcv]
        
        print(f"✅ Fetched {len(prices)} real price points ({days} days)")
        print(f"   Range: ${min(prices):.0f} - ${max(prices):.0f}")
        print(f"   Change: {(prices[-1]/prices[0] - 1):.2%}")
        
        return prices
    except Exception as e:
        print(f"⚠️  Error fetching data: {e}")
        return generate_synthetic_data(days * 24)


def generate_synthetic_data(n: int) -> List[float]:
    """Generate realistic synthetic data."""
    np.random.seed(42)
    prices = [50000.0]
    for i in range(n - 1):
        change = np.random.normal(0.0001, 0.008)
        prices.append(max(prices[-1] * (1 + change), 1000))
    return prices


def analyze_market_conditions(prices: List[float]) -> Dict:
    """Analyze market conditions in the data."""
    returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
    
    # Volatility
    volatility = np.std(returns)
    
    # Trend
    total_change = (prices[-1] / prices[0] - 1)
    
    # Max moves
    max_up = max(returns)
    max_down = min(returns)
    
    # Consecutive up/down
    streaks = []
    current_streak = 1
    current_dir = 'up' if returns[0] > 0 else 'down'
    
    for r in returns[1:]:
        if (r > 0 and current_dir == 'up') or (r < 0 and current_dir == 'down'):
            current_streak += 1
        else:
            streaks.append((current_dir, current_streak))
            current_dir = 'up' if r > 0 else 'down'
            current_streak = 1
    
    max_up_streak = max([s[1] for s in streaks if s[0] == 'up'], default=0)
    max_down_streak = max([s[1] for s in streaks if s[0] == 'down'], default=0)
    
    return {
        'volatility': volatility,
        'total_change': total_change,
        'max_up': max_up,
        'max_down': max_down,
        'max_up_streak': max_up_streak,
        'max_down_streak': max_down_streak,
        'avg_return': np.mean(returns)
    }


def run_detailed_test(prices: List[float], config: BotConfig, label: str) -> Dict:
    """Run detailed test and collect metrics."""
    bot = UnifiedBotFixed(config)
    
    balance_history = [config.initial_capital]
    trades_log = []
    position_log = []
    
    for i, price in enumerate(prices):
        # Track positions before cycle
        pos_before = len(bot.tracker.positions_long) + len(bot.tracker.positions_short)
        
        bot.run_cycle(price)
        
        # Track positions after cycle
        pos_after = len(bot.tracker.positions_long) + len(bot.tracker.positions_short)
        
        # Log trade if position count changed
        if pos_after != pos_before:
            trades_log.append({
                'time': i,
                'price': price,
                'positions_before': pos_before,
                'positions_after': pos_after,
                'balance': bot.current_balance
            })
        
        balance_history.append(bot.current_balance)
        position_log.append(pos_after)
    
    stats = bot.get_stats()
    
    # Calculate max drawdown
    peak = config.initial_capital
    max_dd = 0
    dd_periods = []
    
    for b in balance_history:
        if b > peak:
            peak = b
        dd = (peak - b) / peak
        if dd > max_dd:
            max_dd = dd
        dd_periods.append(dd)
    
    stats['max_drawdown'] = max_dd
    stats['balance_history'] = balance_history
    stats['trades_log'] = trades_log
    stats['position_log'] = position_log
    stats['label'] = label
    
    return stats


def analyze_what_breaks(results: List[Dict]):
    """Analyze what breaks the results."""
    print("\n" + "="*70)
    print("🔍 ANALYSIS: WHAT BREAKS THE RESULTS?")
    print("="*70)
    
    profitable = [r for r in results if r['total_return'] > 0]
    unprofitable = [r for r in results if r['total_return'] <= 0]
    
    print(f"\n📊 Profitable configs: {len(profitable)}/{len(results)}")
    print(f"📊 Unprofitable configs: {len(unprofitable)}/{len(results)}")
    
    if profitable and unprofitable:
        print(f"\n✅ Profitable avg return: {np.mean([r['total_return'] for r in profitable]):.2%}")
        print(f"❌ Unprofitable avg return: {np.mean([r['total_return'] for r in unprofitable]):.2%}")
        
        # Compare metrics
        print(f"\n📈 Key differences:")
        print(f"  Profitable avg trades: {np.mean([r['total_trades'] for r in profitable]):.1f}")
        print(f"  Unprofitable avg trades: {np.mean([r['total_trades'] for r in unprofitable]):.1f}")
        
        print(f"  Profitable avg win rate: {np.mean([r['win_rate'] for r in profitable]):.1%}")
        print(f"  Unprofitable avg win rate: {np.mean([r['win_rate'] for r in unprofitable]):.1%}")
        
        print(f"  Profitable avg fees: ${np.mean([r['total_fees'] for r in profitable]):.4f}")
        print(f"  Unprofitable avg fees: ${np.mean([r['total_fees'] for r in unprofitable]):.4f}")


def test_config_variations(prices: List[float], market_conditions: Dict):
    """Test different config variations."""
    results = []
    
    # Base config
    base = BotConfig()
    base.initial_capital = 150.0
    
    configs = [
        ('BASE (30% pos, 1.5% TP)', base),
        
        # Smaller positions
        ('SMALL_POS (20% pos, 1.5% TP)', 
         BotConfig(short_position_pct=0.20, long_position_pct=0.20, 
                  trend_follow_position_pct=0.20)),
        
        # Tighter stops
        ('TIGHT_SL (30% pos, 1.5% TP, 1% SL)',
         BotConfig(short_position_pct=0.30, short_sl=0.01, long_markup=0.01)),
        
        # Wider stops
        ('WIDE_SL (30% pos, 1.5% TP, 3% SL)',
         BotConfig(short_position_pct=0.30, short_sl=0.03, long_markup=0.015)),
        
        # Higher TP
        ('HIGH_TP (30% pos, 3% TP)',
         BotConfig(short_position_pct=0.30, short_tp=0.03, long_markup=0.03)),
        
        # Lower leverage
        ('LOW_LEV (30% pos, 1.5% TP, 3x lev)',
         BotConfig(short_position_pct=0.30, short_leverage=3.0)),
        
        # Higher reserve
        ('HIGH_RESERVE (20% pos, 20% reserve)',
         BotConfig(short_position_pct=0.20, long_position_pct=0.20, reserve_pct=0.20)),
        
        # More conservative circuit breaker
        ('SAFE_CB (30% pos, 3% daily loss limit)',
         BotConfig(short_position_pct=0.30, max_daily_loss_pct=0.03)),
    ]
    
    print("\n" + "="*70)
    print("🧪 TESTING CONFIG VARIATIONS")
    print("="*70)
    
    for name, config in configs:
        print(f"\n🔄 Testing: {name}")
        result = run_detailed_test(prices, config, name)
        results.append(result)
        
        emoji = "✅" if result['total_return'] > 0 else "❌"
        print(f"  {emoji} Return: {result['total_return']:.2%}, "
              f"Trades: {result['total_trades']}, "
              f"WinRate: {result['win_rate']:.1%}, "
              f"MaxDD: {result['max_drawdown']:.2%}")
    
    return results


def print_recommendations(results: List[Dict]):
    """Print recommendations based on results."""
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)
    
    # Sort by return
    sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)
    
    print("\n🏆 TOP 3 CONFIGURATIONS:")
    for i, r in enumerate(sorted_results[:3], 1):
        print(f"  {i}. {r['label']}: {r['total_return']:.2%} return, {r['total_trades']} trades")
    
    print("\n⚠️  WORST 3 CONFIGURATIONS:")
    for i, r in enumerate(sorted_results[-3:], 1):
        print(f"  {i}. {r['label']}: {r['total_return']:.2%} return, {r['total_trades']} trades")
    
    # Best risk-adjusted
    best_sharpe = max(results, key=lambda x: x['total_return'] / (x['max_drawdown'] + 0.001))
    print(f"\n📊 Best Risk-Adjusted: {best_sharpe['label']}")
    print(f"   Return/Drawdown ratio: {best_sharpe['total_return'] / (best_sharpe['max_drawdown'] + 0.001):.2f}")


def main():
    print("="*70)
    print("🔬 REAL DATA BOT ANALYSIS")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Fetch real data
    print("\n📊 Fetching real BTC data...")
    prices = fetch_real_btc_data(90)
    
    # Analyze market conditions
    print("\n📈 Market Analysis:")
    conditions = analyze_market_conditions(prices)
    print(f"  Volatility: {conditions['volatility']:.4f}")
    print(f"  Total change: {conditions['total_change']:.2%}")
    print(f"  Max up move: {conditions['max_up']:.2%}")
    print(f"  Max down move: {conditions['max_down']:.2%}")
    print(f"  Max up streak: {conditions['max_up_streak']} periods")
    print(f"  Max down streak: {conditions['max_down_streak']} periods")
    
    # Test config variations
    results = test_config_variations(prices, conditions)
    
    # Analyze what breaks
    analyze_what_breaks(results)
    
    # Print recommendations
    print_recommendations(results)
    
    # Save results
    with open('config_analysis_results.json', 'w') as f:
        clean_results = []
        for r in results:
            clean = {k: v for k, v in r.items() if k not in ['balance_history', 'trades_log', 'position_log']}
            clean_results.append(clean)
        json.dump(clean_results, f, indent=2, default=str)
    
    print("\n💾 Results saved to: config_analysis_results.json")


if __name__ == '__main__':
    main()
