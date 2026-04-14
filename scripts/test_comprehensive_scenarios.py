#!/usr/bin/env python3
"""
COMPREHENSIVE SCENARIO TESTING
==============================
Test bots on multiple market conditions:
- Bull market (strong uptrend)
- Bear market (strong downtrend)
- Sideways (chop)
- Recovery (V-bottom)
- Crash (sharp drop)

Uses real historical data or generates realistic scenarios.
"""

import json
import numpy as np
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Tuple

sys.path.insert(0, 'scripts')
from unified_bot_risk_scaling import UnifiedConfig, UnifiedBotRiskScaling
from unified_bot_enhanced import UnifiedConfig as EnhancedConfig, UnifiedBotEnhanced


def generate_bull_market(days: int = 60, start_price: float = 50000, volatility: float = 0.02) -> List[float]:
    """Generate bull market with trend up."""
    np.random.seed(42)
    prices = [start_price]
    for i in range(days * 24):
        trend = 0.0008  # Strong upward trend
        change = np.random.normal(trend, volatility)
        prices.append(prices[-1] * (1 + change))
    return prices


def generate_bear_market(days: int = 60, start_price: float = 70000, volatility: float = 0.025) -> List[float]:
    """Generate bear market with trend down."""
    np.random.seed(43)
    prices = [start_price]
    for i in range(days * 24):
        trend = -0.0010  # Strong downward trend
        change = np.random.normal(trend, volatility)
        prices.append(max(prices[-1] * (1 + change), 1000))
    return prices


def generate_sideways(days: int = 60, start_price: float = 60000, volatility: float = 0.015) -> List[float]:
    """Generate sideways market (mean reversion)."""
    np.random.seed(44)
    prices = [start_price]
    mean = start_price
    for i in range(days * 24):
        # Pull back to mean
        deviation = (prices[-1] - mean) / mean
        trend = -deviation * 0.001  # Mean reversion
        change = np.random.normal(trend, volatility)
        prices.append(prices[-1] * (1 + change))
    return prices


def generate_recovery(days: int = 60, start_price: float = 40000, volatility: float = 0.03) -> List[float]:
    """Generate V-bottom recovery (crash then recovery)."""
    np.random.seed(45)
    prices = [start_price]
    # First half - crash
    for i in range(days * 12):
        trend = -0.0015
        change = np.random.normal(trend, volatility)
        prices.append(max(prices[-1] * (1 + change), 15000))
    # Second half - recovery
    for i in range(days * 12):
        trend = 0.0020
        change = np.random.normal(trend, volatility)
        prices.append(prices[-1] * (1 + change))
    return prices


def generate_crash_scenario(days: int = 30, start_price: float = 65000, volatility: float = 0.04) -> List[float]:
    """Generate sharp crash scenario (like March 2020 or May 2021)."""
    np.random.seed(46)
    prices = [start_price]
    # Normal for first 1/3
    for i in range(days * 8):
        change = np.random.normal(0.0001, 0.015)
        prices.append(prices[-1] * (1 + change))
    # Sharp crash
    for i in range(days * 7):
        trend = -0.005  # -0.5% per hour
        change = np.random.normal(trend, volatility)
        prices.append(max(prices[-1] * (1 + change), 10000))
    # Slow recovery
    for i in range(days * 15):
        trend = 0.0005
        change = np.random.normal(trend, 0.02)
        prices.append(prices[-1] * (1 + change))
    return prices


def generate_pump_and_dump(days: int = 45, start_price: float = 55000, volatility: float = 0.03) -> List[float]:
    """Generate pump and dump scenario."""
    np.random.seed(47)
    prices = [start_price]
    # Gradual pump
    for i in range(days * 15):
        trend = 0.0015
        change = np.random.normal(trend, volatility * 0.8)
        prices.append(prices[-1] * (1 + change))
    # Sharp dump
    for i in range(days * 10):
        trend = -0.003
        change = np.random.normal(trend, volatility * 1.2)
        prices.append(max(prices[-1] * (1 + change), 10000))
    # Chop
    for i in range(days * 20):
        change = np.random.normal(0, volatility * 0.7)
        prices.append(prices[-1] * (1 + change))
    return prices


def run_bot_scenario(bot_class, config, prices: List[float], scenario_name: str) -> Dict:
    """Run a bot on a price series."""
    bot = bot_class(config)
    price_history = []
    
    for i, price in enumerate(prices):
        price_history.append(price)
        if len(price_history) > 200:
            price_history = price_history[-150:]
        
        if i < 50:
            continue
        
        trend = bot.detect_trend(price_history)
        bot.current_trend = trend
        
        # Execute strategy
        if hasattr(bot, 'should_enter_short'):  # Risk Scaling Bot
            if trend in ('strong_downtrend', 'downtrend'):
                for pos in bot.positions_short[:]:
                    exit_reason = bot.should_exit_short(pos, price)
                    if exit_reason:
                        asyncio.run(bot.close_short(pos, price, exit_reason))
                        bot.positions_short.remove(pos)
                
                if bot.should_enter_short(price, price_history):
                    pos = asyncio.run(bot.open_short(price))
                    if pos:
                        bot.positions_short.append(pos)
            
            elif trend in ('strong_uptrend', 'uptrend'):
                for pos in bot.positions_short[:]:
                    asyncio.run(bot.close_short(pos, price, 'trend_change'))
                    bot.positions_short.remove(pos)
                
                for pos in bot.positions_long[:]:
                    if pos['type'] == 'long_grid' and price >= pos['tp_price']:
                        asyncio.run(bot.close_long(pos, price, 'tp'))
                        bot.positions_long.remove(pos)
                
                if bot.should_enter_long(price, price_history):
                    pos = asyncio.run(bot.open_long(price))
                    if pos:
                        bot.positions_long.append(pos)
        
        else:  # Enhanced Bot
            if trend in ('strong_downtrend', 'bear_rally'):
                for pos in bot.positions_short[:]:
                    exit_reason = bot.should_exit_short(pos, price)
                    if exit_reason:
                        asyncio.run(bot.close_short(pos, price, exit_reason))
                        bot.positions_short.remove(pos)
                
                if bot.should_enter_short(price, price_history):
                    pos = asyncio.run(bot.open_short(price))
                    if pos:
                        bot.positions_short.append(pos)
            
            elif trend == 'strong_uptrend':
                for pos in bot.positions_short[:]:
                    asyncio.run(bot.close_short(pos, price, 'trend_change'))
                    bot.positions_short.remove(pos)
                
                for pos in bot.positions_long[:]:
                    if pos.get('type') == 'trend_follow':
                        exit_reason = bot.should_exit_trend_follow(pos, price)
                        if exit_reason and exit_reason != 'partial_tp':
                            asyncio.run(bot.close_trend_follow(pos, price, exit_reason))
                            bot.positions_long.remove(pos)
                
                if bot.should_enter_trend_follow(price, price_history):
                    pos = asyncio.run(bot.open_trend_follow(price))
                    if pos:
                        bot.positions_long.append(pos)
            
            elif trend == 'pullback_uptrend':
                for pos in bot.positions_short[:]:
                    asyncio.run(bot.close_short(pos, price, 'trend_change'))
                    bot.positions_short.remove(pos)
                
                for pos in bot.positions_long[:]:
                    if pos.get('type') == 'long_grid' and price >= pos['tp_price']:
                        asyncio.run(bot.close_long_grid(pos, price))
                        bot.positions_long.remove(pos)
                
                if bot.should_enter_long_grid(price, price_history):
                    pos = asyncio.run(bot.open_long_grid(price))
                    if pos:
                        bot.positions_long.append(pos)
    
    total_trades = bot.stats['trades_short'] + bot.stats['trades_long']
    return {
        'scenario': scenario_name,
        'initial': config.initial_capital,
        'final': bot.current_balance,
        'return_pct': (bot.current_balance - config.initial_capital) / config.initial_capital * 100,
        'trades': total_trades,
        'short_trades': bot.stats['trades_short'],
        'long_trades': bot.stats['trades_long'],
        'pnl': bot.stats['profit_total'],
        'price_start': prices[0],
        'price_end': prices[-1],
        'price_change_pct': (prices[-1] / prices[0] - 1) * 100
    }


def fetch_historical_data():
    """Try to fetch multiple historical datasets."""
    try:
        import ccxt
        exchange = ccxt.binance({'enableRateLimit': True})
        
        datasets = {}
        
        # Recent data (last 1000 hours)
        try:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=1000)
            datasets['Recent (1000h)'] = [c[4] for c in ohlcv]
        except:
            pass
        
        return datasets
    except:
        return {}


def print_results_table(results: List[Dict], title: str):
    """Print formatted results table."""
    print(f"\n{'='*90}")
    print(f"{title}")
    print(f"{'='*90}")
    print(f"{'Scenario':<20} {'Price Δ':<10} {'Return':<10} {'Trades':<8} {'Short':<6} {'Long':<6} {'PnL $':<10}")
    print(f"{'-'*90}")
    
    for r in results:
        print(f"{r['scenario']:<20} {r['price_change_pct']:>+7.1f}%  {r['return_pct']:>+7.1f}%  {r['trades']:>6}  {r['short_trades']:>5}  {r['long_trades']:>5}  ${r['pnl']:>+8.2f}")
    
    print(f"{'='*90}")
    
    # Summary stats
    returns = [r['return_pct'] for r in results]
    pnls = [r['pnl'] for r in results]
    total_trades = sum(r['trades'] for r in results)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Avg Return: {np.mean(returns):+.2f}%")
    print(f"   Best: {max(returns):+.2f}% | Worst: {min(returns):+.2f}%")
    print(f"   Total PnL: ${sum(pnls):+.2f}")
    print(f"   Total Trades: {total_trades}")


def main():
    print("="*90)
    print("🧪 COMPREHENSIVE SCENARIO TESTING")
    print("="*90)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configs
    config_100 = UnifiedConfig.load('config/config_100usd.json')
    config_100.testnet = True
    
    config_200 = EnhancedConfig.load('config/config_200usd_enhanced.json')
    config_200.testnet = True
    
    # Generate scenarios
    scenarios = {
        'BULL (60d)': generate_bull_market(60, 50000, 0.02),
        'BEAR (60d)': generate_bear_market(60, 70000, 0.025),
        'SIDEWAYS (60d)': generate_sideways(60, 60000, 0.015),
        'RECOVERY (60d)': generate_recovery(60, 40000, 0.03),
        'CRASH (30d)': generate_crash_scenario(30, 65000, 0.04),
        'PUMP&DUMP (45d)': generate_pump_and_dump(45, 55000, 0.03),
    }
    
    # Add real data if available
    historical = fetch_historical_data()
    scenarios.update(historical)
    
    print(f"\n📊 Generated {len(scenarios)} scenarios for testing")
    
    # Test Risk Scaling Bot ($100)
    print("\n\n" + "="*90)
    print("🤖 TESTING: Risk Scaling Bot ($100)")
    print("="*90)
    
    results_100 = []
    for name, prices in scenarios.items():
        print(f"  Testing {name}...", end=' ')
        result = run_bot_scenario(UnifiedBotRiskScaling, config_100, prices, name)
        results_100.append(result)
        print(f"Return: {result['return_pct']:+.1f}%, Trades: {result['trades']}")
    
    print_results_table(results_100, "📊 RISK SCALING BOT ($100) - ALL SCENARIOS")
    
    # Test Enhanced Bot ($200)
    print("\n\n" + "="*90)
    print("🤖 TESTING: Enhanced Bot ($200)")
    print("="*90)
    
    results_200 = []
    for name, prices in scenarios.items():
        print(f"  Testing {name}...", end=' ')
        result = run_bot_scenario(UnifiedBotEnhanced, config_200, prices, name)
        results_200.append(result)
        print(f"Return: {result['return_pct']:+.1f}%, Trades: {result['trades']}")
    
    print_results_table(results_200, "📊 ENHANCED BOT ($200) - ALL SCENARIOS")
    
    # Comparison
    print("\n\n" + "="*90)
    print("📊 HEAD-TO-HEAD COMPARISON")
    print("="*90)
    print(f"{'Scenario':<20} {'$100 Return':<12} {'$200 Return':<12} {'Winner':<10}")
    print(f"{'-'*90}")
    
    for r100, r200 in zip(results_100, results_200):
        winner = '$200' if r200['return_pct'] > r100['return_pct'] else '$100'
        print(f"{r100['scenario']:<20} {r100['return_pct']:>+10.1f}%  {r200['return_pct']:>+10.1f}%  {winner:<10}")
    
    print(f"{'='*90}")
    
    # Overall summary
    total_100 = sum(r['return_pct'] for r in results_100)
    total_200 = sum(r['return_pct'] for r in results_200)
    
    print(f"\n🏆 OVERALL WINNER: {'Enhanced ($200)' if total_200 > total_100 else 'Risk Scaling ($100)'}")
    print(f"   Total $100 returns: {total_100:+.1f}%")
    print(f"   Total $200 returns: {total_200:+.1f}%")
    print(f"   Difference: {total_200 - total_100:+.1f}%")
    
    # Save results
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'scenarios_tested': len(scenarios),
        'risk_scaling_100': results_100,
        'enhanced_200': results_200
    }
    
    with open('comprehensive_test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: comprehensive_test_results.json")


if __name__ == '__main__':
    main()
