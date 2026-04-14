#!/usr/bin/env python3
"""
FAST COMPREHENSIVE TESTING
==========================
Quick version with fewer iterations but same coverage.
"""

import json
import numpy as np
import sys
from datetime import datetime
from typing import List, Dict, Tuple
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, 'scripts')
from unified_bot import UnifiedBot, BotConfig


def generate_scenario(scenario_type: str, n: int, seed: int) -> List[float]:
    """Generate price scenario."""
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
    else:
        prices = [50000] * n
    
    return prices


def run_test(args) -> Dict:
    """Run single test."""
    prices, config_params, seed = args
    np.random.seed(seed)
    
    # Add noise
    noisy_prices = [p * (1 + np.random.normal(0, 0.0001)) for p in prices]
    
    config = BotConfig()
    for key, value in config_params.items():
        setattr(config, key, value)
    
    bot = UnifiedBot(config)
    for price in noisy_prices:
        bot.run_cycle(price)
    
    return bot.get_stats()


def run_batch_tests(scenario_type: str, n_hours: int, config_name: str, 
                    config_params: Dict, n_tests: int) -> Dict:
    """Run batch of tests."""
    print(f"    {config_name} x{n_tests}...", flush=True)
    
    prices = generate_scenario(scenario_type, n_hours, seed=42)
    
    args_list = [(prices, config_params, i) for i in range(n_tests)]
    
    results = []
    for args in args_list:
        results.append(run_test(args))
    
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
        'avg_win_rate': float(np.mean(win_rates)),
        'avg_fees': float(np.mean(fees)),
        'profitable_pct': float(sum(1 for r in returns if r > 0) / len(returns) * 100)
    }


def main():
    print("="*80)
    print("🧪 FAST COMPREHENSIVE TESTING")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    periods = {'30d': 720, '90d': 2160, '180d': 4320}
    scenarios = ['BULL', 'BEAR', 'SIDEWAYS', 'CRASH', 'RECOVERY', 'MIXED']
    test_counts = [100, 200, 300]  # Smaller for speed
    
    configs = {
        'BASE': {'initial_capital': 150.0, 'short_position_pct': 0.30, 'long_position_pct': 0.30, 'short_tp': 0.015, 'long_markup': 0.015},
        'CONSERVATIVE': {'initial_capital': 150.0, 'short_position_pct': 0.20, 'long_position_pct': 0.20, 'short_tp': 0.02, 'long_markup': 0.02, 'short_sl': 0.015},
        'AGGRESSIVE': {'initial_capital': 150.0, 'short_position_pct': 0.40, 'long_position_pct': 0.40, 'short_leverage': 5.0},
        'HIGH_TP': {'initial_capital': 150.0, 'short_tp': 0.03, 'long_markup': 0.03},
        'TIGHT_SL': {'initial_capital': 150.0, 'short_sl': 0.015},
        'WIDE_SL': {'initial_capital': 150.0, 'short_sl': 0.03},
        'LOW_LEV': {'initial_capital': 150.0, 'short_leverage': 3.0},
        'HIGH_RESERVE': {'initial_capital': 150.0, 'reserve_pct': 0.20},
    }
    
    all_results = {}
    
    for period_name, n_hours in periods.items():
        print(f"\n{'='*80}")
        print(f"📅 {period_name} ({n_hours}h)")
        print(f"{'='*80}")
        
        period_results = {}
        
        for scenario in scenarios:
            print(f"\n  🔄 {scenario}")
            scen_results = {}
            
            for n_tests in test_counts:
                test_key = f'{n_tests}_tests'
                scen_results[test_key] = {}
                
                for config_name, config_params in configs.items():
                    result = run_batch_tests(scenario, n_hours, config_name, config_params, n_tests)
                    scen_results[test_key][config_name] = result
            
            period_results[scenario] = scen_results
        
        all_results[period_name] = period_results
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    for period_name in periods.keys():
        print(f"\n{period_name}:")
        for scenario in ['BULL', 'BEAR', 'MIXED']:
            results_100 = all_results[period_name][scenario]['100_tests']
            best = max(results_100.items(), key=lambda x: x[1]['avg_return'])
            print(f"  {scenario}: Best={best[0]} ({best[1]['avg_return']:+.2%}), WinRate={best[1]['avg_win_rate']:.1%}")
    
    # Save
    with open('fast_test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Saved to: fast_test_results.json")


if __name__ == '__main__':
    main()
