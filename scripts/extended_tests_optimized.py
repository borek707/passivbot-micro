#!/usr/bin/env python3
"""
EXTENDED TESTS WITH OPTIMIZED CONFIG
=====================================
Using the best performing configuration from initial tests.
More scenarios, more variations, longer periods.
"""

import json
import numpy as np
import sys
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, 'scripts')
from unified_bot import UnifiedBot, BotConfig


def generate_scenario(scenario_type: str, n: int, seed: int = 42) -> List[float]:
    """Generate price scenario with variations."""
    np.random.seed(seed)
    
    if scenario_type == 'BULL':
        prices = [50000]
        for _ in range(n-1):
            prices.append(prices[-1] * (1 + np.random.normal(0.0008, 0.015)))
    elif scenario_type == 'BEAR':
        prices = [70000]
        for _ in range(n-1):
            prices.append(max(prices[-1] * (1 + np.random.normal(-0.001, 0.02)), 1000))
    elif scenario_type == 'SIDEWAYS':
        prices = [60000]
        for _ in range(n-1):
            deviation = (prices[-1] - 60000) / 60000
            prices.append(prices[-1] * (1 + np.random.normal(-deviation*0.002, 0.012)))
    elif scenario_type == 'CRASH':
        prices = [65000]
        n1, n2 = int(n*0.3), int(n*0.2)
        for _ in range(n1): prices.append(prices[-1] * (1 + np.random.normal(0.0001, 0.01)))
        for _ in range(n2): prices.append(max(prices[-1] * (1 + np.random.normal(-0.005, 0.04)), 10000))
        for _ in range(n-n1-n2): prices.append(prices[-1] * (1 + np.random.normal(0.0005, 0.018)))
    elif scenario_type == 'RECOVERY':
        prices = [40000]
        n1 = n // 2
        for _ in range(n1): prices.append(max(prices[-1] * (1 + np.random.normal(-0.0015, 0.025)), 15000))
        for _ in range(n-n1): prices.append(prices[-1] * (1 + np.random.normal(0.002, 0.02)))
    elif scenario_type == 'MIXED':
        prices = [50000]
        segments = [(n//4, 0.001, 0.015), (n//6, -0.004, 0.04), (n//4, 0.002, 0.02), (n-n//4-n//6-n//4, 0, 0.015)]
        for count, trend, vol in segments:
            for _ in range(count):
                prices.append(max(prices[-1] * (1 + np.random.normal(trend, vol)), 1000))
        prices = prices[:n]
    elif scenario_type == 'PUMP_DUMP':
        prices = [55000]
        n1, n2 = int(n * 0.4), int(n * 0.25)
        for _ in range(n1): prices.append(prices[-1] * (1 + np.random.normal(0.0015, 0.018)))
        for _ in range(n2): prices.append(max(prices[-1] * (1 + np.random.normal(-0.003, 0.035)), 10000))
        for _ in range(n - n1 - n2): prices.append(prices[-1] * (1 + np.random.normal(0, 0.015)))
    elif scenario_type == 'SLOW_BULL':
        prices = [50000]
        for _ in range(n-1):
            prices.append(prices[-1] * (1 + np.random.normal(0.0004, 0.01)))
    elif scenario_type == 'FAST_CRASH':
        prices = [70000]
        for _ in range(n//3): prices.append(prices[-1] * (1 + np.random.normal(0.0001, 0.015)))
        for _ in range(n-n//3): prices.append(max(prices[-1] * (1 + np.random.normal(-0.008, 0.05)), 8000))
    elif scenario_type == 'CHOPPY':
        prices = [55000]
        for _ in range(n-1):
            prices.append(prices[-1] * (1 + np.random.normal(0, 0.025)))
    elif scenario_type == 'TRENDING':
        prices = [50000]
        for i in range(n-1):
            trend = 0.001 * np.sin(i * 0.01)
            prices.append(prices[-1] * (1 + np.random.normal(trend, 0.015)))
    else:
        prices = [50000] * n
    return prices


def get_optimized_config() -> BotConfig:
    """Get optimized configuration."""
    config = BotConfig()
    config.initial_capital = 150.0
    config.reserve_pct = 0.10
    
    config.short_leverage = 5.0
    config.short_position_pct = 0.35
    config.short_max_positions = 1
    config.short_bounce_threshold = 0.02
    config.short_tp = 0.03
    config.short_sl = 0.03
    
    config.long_position_pct = 0.35
    config.max_grid_positions = 2
    config.long_grid_spacing = 0.015
    config.long_markup = 0.03
    
    config.circuit_breaker_enabled = True
    config.max_daily_loss_pct = 0.05
    config.max_consecutive_losses = 2
    config.circuit_cooldown_minutes = 240
    
    config.maker_fee = 0.00015
    config.taker_fee = 0.00045
    config.use_maker_only = True
    
    config.check_interval = 30
    config.min_order_size_usd = 10.0
    
    return config


def run_test(prices: List[float], config: BotConfig, seed: int) -> Dict:
    """Run single test."""
    np.random.seed(seed)
    noisy_prices = [p * (1 + np.random.normal(0, 0.0001)) for p in prices]
    
    bot = UnifiedBot(config)
    for price in noisy_prices:
        bot.run_cycle(price)
    
    return bot.get_stats()


def run_extended_tests(scenario_type: str, n_hours: int, n_tests: int = 1000) -> Dict:
    """Run extended tests."""
    prices = generate_scenario(scenario_type, n_hours, seed=42)
    config = get_optimized_config()
    
    results = []
    for i in range(n_tests):
        result = run_test(prices, config, i)
        results.append(result)
    
    returns = [r['total_return'] for r in results]
    trades = [r['total_trades'] for r in results]
    win_rates = [r['win_rate'] for r in results]
    fees = [r['total_fees'] for r in results]
    
    return {
        'avg_return': float(np.mean(returns)),
        'std_return': float(np.std(returns)),
        'min_return': float(np.min(returns)),
        'max_return': float(np.max(returns)),
        'median_return': float(np.median(returns)),
        'avg_trades': float(np.mean(trades)),
        'trades_per_month': float(np.mean(trades) / (n_hours / (30 * 24))),
        'avg_win_rate': float(np.mean(win_rates)),
        'avg_fees': float(np.mean(fees)),
        'profitable_pct': float(sum(1 for r in returns if r > 0) / len(returns) * 100)
    }


def main():
    print("="*80)
    print("🧪 EXTENDED TESTS WITH OPTIMIZED CONFIG")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Extended periods
    periods = {
        '30d': 30 * 24,
        '60d': 60 * 24,
        '90d': 90 * 24,
        '120d': 120 * 24,
        '180d': 180 * 24,
        '365d': 365 * 24
    }
    
    # Extended scenarios
    scenarios = [
        'BULL', 'BEAR', 'SIDEWAYS', 'CRASH', 'RECOVERY', 
        'MIXED', 'PUMP_DUMP', 'SLOW_BULL', 'FAST_CRASH', 'CHOPPY', 'TRENDING'
    ]
    
    print(f"📊 Testing {len(scenarios)} scenarios across {len(periods)} periods")
    print(f"   Total: {len(scenarios) * len(periods) * 1000:,} tests")
    print("")
    
    all_results = {}
    
    for period_name, n_hours in periods.items():
        print(f"{'='*80}")
        print(f"📅 PERIOD: {period_name} ({n_hours} hours)")
        print(f"{'='*80}")
        
        period_results = {}
        
        for scenario in scenarios:
            print(f"  🔄 {scenario} x1000...", flush=True)
            result = run_extended_tests(scenario, n_hours, 1000)
            period_results[scenario] = result
            
            emoji = "✅" if result['avg_return'] > 0 else "❌"
            print(f"     {emoji} Return: {result['avg_return']:+.2%} (±{result['std_return']:.2%}), "
                  f"Trades/mo: {result['trades_per_month']:.1f}, "
                  f"WinRate: {result['avg_win_rate']:.1%}, "
                  f"Profitable: {result['profitable_pct']:.1f}%")
        
        all_results[period_name] = period_results
    
    # Summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY - OPTIMIZED CONFIG")
    print("="*80)
    
    # Calculate overall performance
    all_returns = []
    for period_data in all_results.values():
        for scenario_data in period_data.values():
            all_returns.append(scenario_data['avg_return'])
    
    print(f"\nOverall Statistics:")
    print(f"  Average Return: {np.mean(all_returns):+.2%}")
    print(f"  Median Return: {np.median(all_returns):+.2%}")
    print(f"  Best Scenario: {np.max(all_returns):+.2%}")
    print(f"  Worst Scenario: {np.min(all_returns):+.2%}")
    print(f"  Profitable Scenarios: {sum(1 for r in all_returns if r > 0)}/{len(all_returns)}")
    
    # Best by period
    print(f"\nBest by Period:")
    for period_name, period_data in all_results.items():
        best_scenario = max(period_data.items(), key=lambda x: x[1]['avg_return'])
        print(f"  {period_name}: {best_scenario[0]} ({best_scenario[1]['avg_return']:+.2%})")
    
    # Best by scenario
    print(f"\nBest by Scenario:")
    scenario_avg = {}
    for scenario in scenarios:
        returns = [all_results[p][scenario]['avg_return'] for p in periods.keys()]
        scenario_avg[scenario] = np.mean(returns)
    
    for scenario, avg_ret in sorted(scenario_avg.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {scenario}: {avg_ret:+.2%} avg")
    
    # Save
    with open('extended_optimized_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to: extended_optimized_results.json")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
