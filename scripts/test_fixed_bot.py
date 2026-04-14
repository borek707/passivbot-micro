#!/usr/bin/env python3
"""
SIMPLIFIED BOT COMPARISON
=========================
Compare key metrics between original and fixed bot.
"""

import json
import numpy as np
import sys
from datetime import datetime

sys.path.insert(0, 'scripts')
from unified_bot_fixed import UnifiedBotFixed, BotConfig


def generate_price_scenarios():
    """Generate different market scenarios."""
    np.random.seed(42)
    scenarios = {}
    
    # Bull market
    prices = [50000.0]
    for i in range(1000):
        prices.append(prices[-1] * (1 + np.random.normal(0.0008, 0.02)))
    scenarios['BULL'] = prices
    
    # Bear market
    prices = [70000.0]
    for i in range(1000):
        prices.append(max(prices[-1] * (1 + np.random.normal(-0.001, 0.025)), 10000))
    scenarios['BEAR'] = prices
    
    # Sideways
    prices = [60000.0]
    for i in range(1000):
        deviation = (prices[-1] - 60000) / 60000
        prices.append(prices[-1] * (1 + np.random.normal(-deviation * 0.001, 0.015)))
    scenarios['SIDEWAYS'] = prices
    
    # Crash
    prices = [65000.0]
    for i in range(300):
        prices.append(prices[-1] * (1 + np.random.normal(0.0001, 0.015)))
    for i in range(200):
        prices.append(max(prices[-1] * (1 + np.random.normal(-0.005, 0.04)), 15000))
    for i in range(500):
        prices.append(prices[-1] * (1 + np.random.normal(0.0005, 0.02)))
    scenarios['CRASH'] = prices
    
    return scenarios


def run_fixed_bot_simulation(prices, initial_capital=150.0):
    """Run fixed bot simulation."""
    config = BotConfig()
    config.initial_capital = initial_capital
    
    bot = UnifiedBotFixed(config)
    trades = []
    balance_history = [initial_capital]
    
    for price in prices:
        bot.run_cycle(price)
        balance_history.append(bot.current_balance)
    
    stats = bot.get_stats()
    
    # Calculate max drawdown
    peak = initial_capital
    max_dd = 0
    for b in balance_history:
        if b > peak:
            peak = b
        dd = (peak - b) / peak
        max_dd = max(max_dd, dd)
    
    stats['max_drawdown'] = max_dd
    stats['balance_history'] = balance_history
    
    return stats


def print_scenario_results(scenario_name, stats):
    """Print results for a scenario."""
    print(f"\n📊 {scenario_name}:")
    print(f"  Final Balance: ${stats['final_balance']:.2f}")
    print(f"  Return: {stats['total_return']:.2%}")
    print(f"  Trades: {stats['total_trades']} (W:{stats['wins']}/L:{stats['losses']})")
    print(f"  Win Rate: {stats['win_rate']:.1%}")
    print(f"  Max DD: {stats['max_drawdown']:.2%}")
    print(f"  Total Fees: ${stats['total_fees']:.4f}")


def main():
    print("="*70)
    print("🧪 FIXED BOT COMPREHENSIVE TEST")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate scenarios
    print("\n📊 Generating market scenarios...")
    scenarios = generate_price_scenarios()
    
    all_results = {}
    
    # Run tests
    print("\n" + "="*70)
    print("🤖 TESTING FIXED BOT ON DIFFERENT SCENARIOS")
    print("="*70)
    
    for name, prices in scenarios.items():
        print(f"\n🔄 Running {name} scenario ({len(prices)} prices)...")
        stats = run_fixed_bot_simulation(prices)
        all_results[name] = stats
        print_scenario_results(name, stats)
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    returns = [s['total_return'] for s in all_results.values()]
    win_rates = [s['win_rate'] for s in all_results.values()]
    max_dds = [s['max_drawdown'] for s in all_results.values()]
    fees = [s['total_fees'] for s in all_results.values()]
    
    print(f"\nReturns: {[f'{r:.1%}' for r in returns]}")
    print(f"  Avg: {np.mean(returns):.2%}")
    print(f"  Best: {max(returns):.2%}")
    print(f"  Worst: {min(returns):.2%}")
    
    print(f"\nWin Rates: {[f'{wr:.1%}' for wr in win_rates]}")
    print(f"  Avg: {np.mean(win_rates):.1%}")
    
    print(f"\nMax Drawdowns: {[f'{dd:.1%}' for dd in max_dds]}")
    print(f"  Avg: {np.mean(max_dds):.2%}")
    print(f"  Worst: {max(max_dds):.2%}")
    
    print(f"\nTotal Fees: {[f'${f:.4f}' for f in fees]}")
    print(f"  Avg: ${np.mean(fees):.4f}")
    
    # Count profitable scenarios
    profitable = sum(1 for r in returns if r > 0)
    print(f"\n✅ Profitable scenarios: {profitable}/{len(returns)}")
    
    # Save results
    with open('fixed_bot_test_results.json', 'w') as f:
        # Remove balance_history for cleaner JSON
        clean_results = {k: {kk: vv for kk, vv in v.items() if kk != 'balance_history'} 
                        for k, v in all_results.items()}
        json.dump(clean_results, f, indent=2, default=str)
    
    print("\n💾 Results saved to: fixed_bot_test_results.json")


if __name__ == '__main__':
    main()
