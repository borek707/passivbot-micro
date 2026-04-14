#!/usr/bin/env python3
"""
COMPLETE TEST SUITE
===================
1000 tests per config:
- 3 periods: 30d, 90d, 180d
- 6 scenarios: BULL, BEAR, SIDEWAYS, CRASH, RECOVERY, MIXED, PUMP_DUMP
- 8 configs: BASE, CONSERVATIVE, AGGRESSIVE, HIGH_TP, TIGHT_SL, WIDE_SL, LOW_LEV, HIGH_RESERVE
"""

import json
import numpy as np
import sys
from datetime import datetime
from typing import List, Dict, Tuple

sys.path.insert(0, 'scripts')
from unified_bot import UnifiedBot, BotConfig


def generate_scenario(scenario_type: str, n: int, seed: int = 42) -> List[float]:
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
    elif scenario_type == 'PUMP_DUMP':
        prices = [55000]
        n1, n2 = int(n * 0.4), int(n * 0.25)
        for _ in range(n1): prices.append(prices[-1] * (1 + np.random.normal(0.0015, 0.018)))
        for _ in range(n2): prices.append(max(prices[-1] * (1 + np.random.normal(-0.003, 0.035)), 10000))
        for _ in range(n - n1 - n2): prices.append(prices[-1] * (1 + np.random.normal(0, 0.015)))
    else:
        prices = [50000] * n
    return prices


def get_configs() -> List[Tuple[str, Dict]]:
    """Get all 8 required configurations."""
    configs = []
    
    # 1. BASE
    base = {'initial_capital': 150.0}
    configs.append(("BASE", base))
    
    # 2. CONSERVATIVE
    cons = {
        'initial_capital': 150.0,
        'short_position_pct': 0.20,
        'long_position_pct': 0.20,
        'short_tp': 0.02,
        'long_markup': 0.02,
        'short_sl': 0.015
    }
    configs.append(("CONSERVATIVE", cons))
    
    # 3. AGGRESSIVE
    agg = {
        'initial_capital': 150.0,
        'short_position_pct': 0.40,
        'long_position_pct': 0.40,
        'short_leverage': 5.0,
        'short_tp': 0.02,
        'long_markup': 0.02
    }
    configs.append(("AGGRESSIVE", agg))
    
    # 4. HIGH_TP
    ht = {
        'initial_capital': 150.0,
        'short_tp': 0.04,
        'long_markup': 0.04
    }
    configs.append(("HIGH_TP", ht))
    
    # 5. TIGHT_SL
    tsl = {
        'initial_capital': 150.0,
        'short_sl': 0.015,
        'short_tp': 0.03,
        'long_markup': 0.03
    }
    configs.append(("TIGHT_SL", tsl))
    
    # 6. WIDE_SL
    wsl = {
        'initial_capital': 150.0,
        'short_sl': 0.04,
        'short_tp': 0.03,
        'long_markup': 0.03
    }
    configs.append(("WIDE_SL", wsl))
    
    # 7. LOW_LEV
    ll = {
        'initial_capital': 150.0,
        'short_leverage': 3.0,
        'short_tp': 0.03,
        'long_markup': 0.03
    }
    configs.append(("LOW_LEV", ll))
    
    # 8. HIGH_RESERVE
    hr = {
        'initial_capital': 150.0,
        'reserve_pct': 0.20,
        'short_position_pct': 0.25,
        'long_position_pct': 0.25
    }
    configs.append(("HIGH_RESERVE", hr))
    
    return configs


def run_test(prices: List[float], config_dict: Dict, seed: int) -> Dict:
    """Run single test."""
    np.random.seed(seed)
    noisy_prices = [p * (1 + np.random.normal(0, 0.0001)) for p in prices]
    
    config = BotConfig()
    for key, value in config_dict.items():
        setattr(config, key, value)
    
    bot = UnifiedBot(config)
    for price in noisy_prices:
        bot.run_cycle(price)
    
    return bot.get_stats()


def run_batch(scenario_type: str, n_hours: int, 
              config_name: str, config_dict: Dict, n_tests: int = 1000) -> Dict:
    """Run batch of 1000 tests."""
    prices = generate_scenario(scenario_type, n_hours, seed=42)
    
    results = []
    for i in range(n_tests):
        result = run_test(prices, config_dict, i)
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
    print("🧪 COMPLETE TEST SUITE - 1000 TESTS PER CONFIG")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # 3 periods: 30d, 90d, 180d (in hours)
    periods = {
        '30d': 30 * 24,
        '90d': 90 * 24,
        '180d': 180 * 24
    }
    
    # 7 scenarios
    scenarios = ['BULL', 'BEAR', 'SIDEWAYS', 'CRASH', 'RECOVERY', 'MIXED', 'PUMP_DUMP']
    
    # 8 configs
    configs = get_configs()
    
    print(f"📊 Configuration:")
    print(f"   Periods: {list(periods.keys())}")
    print(f"   Scenarios: {scenarios}")
    print(f"   Configs: {[c[0] for c in configs]}")
    print(f"   Total tests: {len(periods) * len(scenarios) * len(configs) * 1000:,}")
    print("")
    
    all_results = {}
    
    for period_name, n_hours in periods.items():
        print(f"{'='*80}")
        print(f"📅 PERIOD: {period_name} ({n_hours} hours)")
        print(f"{'='*80}")
        
        period_results = {}
        
        for scenario in scenarios:
            print(f"\n  🔄 Scenario: {scenario}")
            scen_results = {}
            
            for config_name, config_dict in configs:
                print(f"    {config_name} x1000...", flush=True)
                result = run_batch(scenario, n_hours, config_name, config_dict, 1000)
                scen_results[config_name] = result
                
                print(f"       Return: {result['avg_return']:+.2%} (min:{result['min_return']:+.2%}, max:{result['max_return']:+.2%})")
                print(f"       Trades/month: {result['trades_per_month']:.1f}, WinRate: {result['avg_win_rate']:.1%}")
            
            period_results[scenario] = scen_results
        
        all_results[period_name] = period_results
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY - Best Performing Configurations")
    print("="*80)
    
    for period_name in periods.keys():
        print(f"\n{period_name}:")
        for scenario in ['BULL', 'BEAR', 'SIDEWAYS']:
            if scenario in all_results[period_name]:
                results = all_results[period_name][scenario]
                best = max(results.items(), key=lambda x: x[1]['avg_return'])
                print(f"  {scenario}: {best[0]} ({best[1]['avg_return']:+.2%}), "
                      f"{best[1]['trades_per_month']:.1f} trades/mo")
    
    # Best overall
    print("\n" + "="*80)
    print("🏆 TOP 5 CONFIGURATIONS OVERALL")
    print("="*80)
    
    all_configs_performance = {}
    for period_name, period_data in all_results.items():
        for scenario, scen_data in period_data.items():
            for config_name, result in scen_data.items():
                if config_name not in all_configs_performance:
                    all_configs_performance[config_name] = []
                all_configs_performance[config_name].append(result['avg_return'])
    
    avg_performance = [(name, np.mean(returns)) for name, returns in all_configs_performance.items()]
    avg_performance.sort(key=lambda x: x[1], reverse=True)
    
    for i, (name, avg_ret) in enumerate(avg_performance[:5], 1):
        print(f"  {i}. {name}: {avg_ret:+.2%} avg return")
    
    # Save
    with open('complete_test_results_1000.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to: complete_test_results_1000.json")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
