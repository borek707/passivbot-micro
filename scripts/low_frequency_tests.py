#!/usr/bin/env python3
"""
LOW-FREQUENCY TRADING TESTS
===========================
Target: <30 trades per month
Intervals: daily (1d) and 6h
Tests: 1000 runs
Various configs with higher thresholds to reduce trade frequency.
"""

import json
import numpy as np
import sys
from datetime import datetime
from typing import List, Dict, Tuple

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


def get_low_freq_configs() -> List[Tuple[str, Dict]]:
    """Configs optimized for low trade frequency (<30/month)."""
    configs = []
    
    # Higher thresholds = fewer trades
    base = {
        'initial_capital': 150.0,
        'short_position_pct': 0.30,
        'long_position_pct': 0.30,
        'short_tp': 0.025,      # 2.5% TP (was 1.5%)
        'long_markup': 0.025,    # 2.5% markup
        'short_sl': 0.02,        # 2% SL
        'short_bounce_threshold': 0.025,  # 2.5% bounce needed (was 1.5%)
        'long_grid_spacing': 0.025,       # 2.5% dip needed
    }
    configs.append(("BASE_2.5%", base))
    
    # Even higher thresholds
    high = base.copy()
    high.update({
        'short_tp': 0.04,       # 4% TP
        'long_markup': 0.04,
        'short_bounce_threshold': 0.04,   # 4% bounce
        'long_grid_spacing': 0.04,
    })
    configs.append(("HIGH_4%", high))
    
    # Conservative with tight SL
    cons = base.copy()
    cons.update({
        'short_position_pct': 0.20,
        'long_position_pct': 0.20,
        'short_sl': 0.015,      # 1.5% SL
        'short_tp': 0.03,       # 3% TP
        'long_markup': 0.03,
    })
    configs.append(("CONSERVATIVE", cons))
    
    # Aggressive but rare
    agg = base.copy()
    agg.update({
        'short_position_pct': 0.40,
        'long_position_pct': 0.40,
        'short_leverage': 5.0,
        'short_tp': 0.05,       # 5% TP
        'long_markup': 0.05,
    })
    configs.append(("AGGRESSIVE_RARE", agg))
    
    # Wide SL for trends
    trend = base.copy()
    trend.update({
        'short_sl': 0.04,       # 4% SL
        'short_tp': 0.05,       # 5% TP
        'long_markup': 0.05,
    })
    configs.append(("TREND_FOLLOW", trend))
    
    # With reserve
    reserve = base.copy()
    reserve.update({
        'reserve_pct': 0.20,
        'short_position_pct': 0.25,
        'long_position_pct': 0.25,
    })
    configs.append(("HIGH_RESERVE", reserve))
    
    # Low leverage safer
    safe = base.copy()
    safe.update({
        'short_leverage': 3.0,
        'short_tp': 0.03,
        'long_markup': 0.03,
    })
    configs.append(("SAFE_3x", safe))
    
    # Very high thresholds (ultra rare)
    ultra = base.copy()
    ultra.update({
        'short_tp': 0.06,       # 6% TP
        'long_markup': 0.06,
        'short_bounce_threshold': 0.05,   # 5% bounce
        'long_grid_spacing': 0.05,
    })
    configs.append(("ULTRA_RARE", ultra))
    
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


def run_batch(scenario_type: str, interval: str, n_periods: int, 
              config_name: str, config_dict: Dict, n_tests: int = 1000) -> Dict:
    """Run batch of tests."""
    prices = generate_scenario(scenario_type, n_periods, seed=42)
    
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
        'avg_trades': float(np.mean(trades)),
        'trades_per_month': float(np.mean(trades) / (n_periods / (30 * 24 if interval == '1h' else 30 * 4 if interval == '6h' else 30))),
        'avg_win_rate': float(np.mean(win_rates)),
        'avg_fees': float(np.mean(fees)),
        'profitable_pct': float(sum(1 for r in returns if r > 0) / len(returns) * 100)
    }


def main():
    print("="*80)
    print("🧪 LOW-FREQUENCY TRADING TESTS")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: <30 trades/month")
    print("")
    
    # 6h intervals (4 candles per day)
    # 30d = 120 candles, 90d = 360, 180d = 720
    periods_6h = {
        '30d_6h': 120,
        '90d_6h': 360,
        '180d_6h': 720
    }
    
    # Daily intervals (1 candle per day)
    periods_daily = {
        '30d_1d': 30,
        '90d_1d': 90,
        '180d_1d': 180
    }
    
    scenarios = ['BULL', 'BEAR', 'SIDEWAYS', 'CRASH', 'RECOVERY', 'MIXED']
    configs = get_low_freq_configs()
    
    all_results = {}
    
    # Test 6h intervals
    print("📊 Testing 6h intervals...")
    for period_name, n_periods in periods_6h.items():
        print(f"\n{'='*80}")
        print(f"⏱️  {period_name} ({n_periods} candles)")
        print(f"{'='*80}")
        
        period_results = {}
        for scen in scenarios:
            print(f"\n  🔄 {scen}")
            scen_results = {}
            for cfg_name, cfg_dict in configs:
                print(f"    {cfg_name} x1000...", flush=True)
                result = run_batch(scen, '6h', n_periods, cfg_name, cfg_dict, 1000)
                scen_results[cfg_name] = result
                
                # Check if meets <30 trades/month target
                target_met = "✅" if result['trades_per_month'] < 30 else "❌"
                print(f"       Return: {result['avg_return']:+.2%}, "
                      f"Trades/month: {result['trades_per_month']:.1f} {target_met}")
            
            period_results[scen] = scen_results
        
        all_results[period_name] = period_results
    
    # Test daily intervals
    print("\n\n📊 Testing daily intervals...")
    for period_name, n_periods in periods_daily.items():
        print(f"\n{'='*80}")
        print(f"⏱️  {period_name} ({n_periods} candles)")
        print(f"{'='*80}")
        
        period_results = {}
        for scen in scenarios:
            print(f"\n  🔄 {scen}")
            scen_results = {}
            for cfg_name, cfg_dict in configs:
                print(f"    {cfg_name} x1000...", flush=True)
                result = run_batch(scen, '1d', n_periods, cfg_name, cfg_dict, 1000)
                scen_results[cfg_name] = result
                
                target_met = "✅" if result['trades_per_month'] < 30 else "❌"
                print(f"       Return: {result['avg_return']:+.2%}, "
                      f"Trades/month: {result['trades_per_month']:.1f} {target_met}")
            
            period_results[scen] = scen_results
        
        all_results[period_name] = period_results
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY - Best configs with <30 trades/month")
    print("="*80)
    
    for period_name in list(periods_6h.keys()) + list(periods_daily.keys()):
        print(f"\n{period_name}:")
        for scen in ['BULL', 'BEAR', 'MIXED']:
            if scen in all_results[period_name]:
                # Filter configs with <30 trades/month
                valid = [(n, r) for n, r in all_results[period_name][scen].items() 
                        if r['trades_per_month'] < 30]
                if valid:
                    best = max(valid, key=lambda x: x[1]['avg_return'])
                    print(f"  {scen}: {best[0]} ({best[1]['avg_return']:+.2%}), "
                          f"{best[1]['trades_per_month']:.1f} trades/mo, "
                          f"{best[1]['avg_win_rate']:.1%} WR")
                else:
                    print(f"  {scen}: No config met <30 trades/month target")
    
    # Save
    with open('low_freq_test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Saved to: low_freq_test_results.json")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
