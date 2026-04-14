#!/usr/bin/env python3
"""
MASSIVE COMPREHENSIVE TESTING
==============================
1000, 2000, 3000 tests across:
- Multiple scenarios (bull, bear, sideways, crash, recovery, mixed)
- Different time periods (30, 60, 90, 180 days)
- Mixed scenarios (half bull + half bear, etc.)
- Various configurations (TP, SL, position size, leverage)

Outputs detailed statistics and recommendations.
"""

import json
import numpy as np
import sys
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict

sys.path.insert(0, 'scripts')
from unified_bot import UnifiedBot, BotConfig


# ============================================================
# SCENARIO GENERATORS
# ============================================================

def generate_bull_market(n: int, start_price: float = 50000, seed: int = 42) -> List[float]:
    """Strong uptrend."""
    np.random.seed(seed)
    prices = [start_price]
    for i in range(n - 1):
        trend = 0.0008
        vol = 0.015
        change = np.random.normal(trend, vol)
        prices.append(prices[-1] * (1 + change))
    return prices


def generate_bear_market(n: int, start_price: float = 70000, seed: int = 43) -> List[float]:
    """Strong downtrend."""
    np.random.seed(seed)
    prices = [start_price]
    for i in range(n - 1):
        trend = -0.001
        vol = 0.02
        change = np.random.normal(trend, vol)
        prices.append(max(prices[-1] * (1 + change), 1000))
    return prices


def generate_sideways(n: int, start_price: float = 60000, seed: int = 44) -> List[float]:
    """Mean reversion / chop."""
    np.random.seed(seed)
    prices = [start_price]
    mean = start_price
    for i in range(n - 1):
        deviation = (prices[-1] - mean) / mean
        trend = -deviation * 0.002
        change = np.random.normal(trend, 0.012)
        prices.append(prices[-1] * (1 + change))
    return prices


def generate_crash(n: int, start_price: float = 65000, seed: int = 45) -> List[float]:
    """Sharp crash then slow recovery."""
    np.random.seed(seed)
    prices = [start_price]
    # 30% normal, 20% crash, 50% recovery
    n1, n2 = int(n * 0.3), int(n * 0.2)
    
    for i in range(n1):
        prices.append(prices[-1] * (1 + np.random.normal(0.0001, 0.01)))
    for i in range(n2):
        prices.append(max(prices[-1] * (1 + np.random.normal(-0.005, 0.04)), 10000))
    for i in range(n - n1 - n2):
        prices.append(prices[-1] * (1 + np.random.normal(0.0005, 0.018)))
    return prices


def generate_recovery(n: int, start_price: float = 40000, seed: int = 46) -> List[float]:
    """V-bottom recovery."""
    np.random.seed(seed)
    prices = [start_price]
    n1 = n // 2
    
    for i in range(n1):
        prices.append(max(prices[-1] * (1 + np.random.normal(-0.0015, 0.025)), 15000))
    for i in range(n - n1):
        prices.append(prices[-1] * (1 + np.random.normal(0.002, 0.02)))
    return prices


def generate_pump_and_dump(n: int, start_price: float = 55000, seed: int = 47) -> List[float]:
    """Gradual pump then sharp dump."""
    np.random.seed(seed)
    prices = [start_price]
    n1, n2 = int(n * 0.4), int(n * 0.25)
    
    for i in range(n1):
        prices.append(prices[-1] * (1 + np.random.normal(0.0015, 0.018)))
    for i in range(n2):
        prices.append(max(prices[-1] * (1 + np.random.normal(-0.003, 0.035)), 10000))
    for i in range(n - n1 - n2):
        prices.append(prices[-1] * (1 + np.random.normal(0, 0.015)))
    return prices


def generate_mixed_scenario(n: int, seed: int = 48) -> List[float]:
    """Mixed: bull → crash → recovery → sideways."""
    np.random.seed(seed)
    prices = [50000]
    segments = [
        (int(n * 0.25), 0.001, 0.015),    # Bull
        (int(n * 0.15), -0.004, 0.04),    # Crash
        (int(n * 0.25), 0.002, 0.02),     # Recovery
        (n - int(n * 0.65), 0, 0.015),    # Sideways
    ]
    
    for count, trend, vol in segments:
        for i in range(count):
            change = np.random.normal(trend, vol)
            prices.append(max(prices[-1] * (1 + change), 1000))
    
    return prices[:n]


# ============================================================
# CONFIG VARIATIONS
# ============================================================

def get_config_variations() -> List[Tuple[str, BotConfig]]:
    """Get different config variations to test."""
    configs = []
    
    # Base config
    base = BotConfig()
    base.initial_capital = 150.0
    configs.append(("BASE", base))
    
    # Conservative
    cons = BotConfig()
    cons.initial_capital = 150.0
    cons.short_position_pct = 0.20
    cons.long_position_pct = 0.20
    cons.short_tp = 0.02
    cons.long_markup = 0.02
    cons.short_sl = 0.015
    configs.append(("CONSERVATIVE", cons))
    
    # Aggressive
    agg = BotConfig()
    agg.initial_capital = 150.0
    agg.short_position_pct = 0.40
    agg.long_position_pct = 0.40
    agg.short_leverage = 5.0
    configs.append(("AGGRESSIVE", agg))
    
    # High TP
    ht = BotConfig()
    ht.initial_capital = 150.0
    ht.short_tp = 0.03
    ht.long_markup = 0.03
    configs.append(("HIGH_TP", ht))
    
    # Tight SL
    tsl = BotConfig()
    tsl.initial_capital = 150.0
    tsl.short_sl = 0.015
    configs.append(("TIGHT_SL", tsl))
    
    # Wide SL
    wsl = BotConfig()
    wsl.initial_capital = 150.0
    wsl.short_sl = 0.03
    configs.append(("WIDE_SL", wsl))
    
    # Low leverage
    ll = BotConfig()
    ll.initial_capital = 150.0
    ll.short_leverage = 3.0
    configs.append(("LOW_LEV", ll))
    
    # High reserve
    hr = BotConfig()
    hr.initial_capital = 150.0
    hr.reserve_pct = 0.20
    configs.append(("HIGH_RESERVE", hr))
    
    # Strict circuit breaker
    scb = BotConfig()
    scb.initial_capital = 150.0
    scb.max_daily_loss_pct = 0.03
    configs.append(("STRICT_CB", scb))
    
    return configs


# ============================================================
# TEST RUNNER
# ============================================================

def run_single_test(prices: List[float], config: BotConfig) -> Dict:
    """Run a single backtest."""
    bot = UnifiedBot(config)
    
    for price in prices:
        bot.run_cycle(price)
    
    stats = bot.get_stats()
    
    # Calculate max drawdown
    balance_history = []
    peak = config.initial_capital
    max_dd = 0
    
    # Reconstruct approximate balance history
    balance = config.initial_capital
    for i, price in enumerate(prices):
        if i < 50:
            continue
        # Simplified - actual balance tracking would need full simulation
        balance_history.append(balance)
    
    return stats


def run_scenario_tests(scenario_name: str, prices: List[float], 
                       configs: List[Tuple[str, BotConfig]], n_tests: int) -> Dict:
    """Run multiple tests on a scenario."""
    print(f"  Running {n_tests} tests for {scenario_name}...")
    
    results_by_config = {}
    
    for config_name, config in configs:
        results = []
        for i in range(n_tests):
            # Add some randomness to prices
            noisy_prices = [p * (1 + np.random.normal(0, 0.0001)) for p in prices]
            result = run_single_test(noisy_prices, config)
            results.append(result)
        
        # Calculate statistics
        returns = [r['total_return'] for r in results]
        trades = [r['total_trades'] for r in results]
        win_rates = [r['win_rate'] for r in results]
        
        results_by_config[config_name] = {
            'avg_return': np.mean(returns),
            'std_return': np.std(returns),
            'min_return': np.min(returns),
            'max_return': np.max(returns),
            'avg_trades': np.mean(trades),
            'avg_win_rate': np.mean(win_rates),
            'profitable_pct': sum(1 for r in returns if r > 0) / len(returns) * 100
        }
    
    return results_by_config


# ============================================================
# MAIN
# ============================================================

def main():
    print("="*80)
    print("🧪 MASSIVE COMPREHENSIVE TESTING")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Time periods (in hours)
    periods = {
        '30d': 30 * 24,
        '60d': 60 * 24,
        '90d': 90 * 24,
        '180d': 180 * 24
    }
    
    # Test counts
    test_counts = [1000, 2000, 3000]
    
    # Get config variations
    configs = get_config_variations()
    print(f"\n📊 Testing {len(configs)} config variations:")
    for name, _ in configs:
        print(f"   • {name}")
    
    all_results = {}
    
    for period_name, n_hours in periods.items():
        print(f"\n{'='*80}")
        print(f"📅 TIME PERIOD: {period_name} ({n_hours} hours)")
        print(f"{'='*80}")
        
        # Generate scenarios
        scenarios = {
            'BULL': generate_bull_market(n_hours),
            'BEAR': generate_bear_market(n_hours),
            'SIDEWAYS': generate_sideways(n_hours),
            'CRASH': generate_crash(n_hours),
            'RECOVERY': generate_recovery(n_hours),
            'PUMP_DUMP': generate_pump_and_dump(n_hours),
            'MIXED': generate_mixed_scenario(n_hours)
        }
        
        print(f"\n📊 Generated {len(scenarios)} scenarios")
        for scen_name, prices in scenarios.items():
            change = (prices[-1] / prices[0] - 1) * 100
            print(f"   • {scen_name}: ${prices[0]:.0f} → ${prices[-1]:.0f} ({change:+.1f}%)")
        
        period_results = {}
        
        for scen_name, prices in scenarios.items():
            print(f"\n🔄 Scenario: {scen_name}")
            
            scen_results = {}
            for n_tests in test_counts:
                print(f"\n  Testing with {n_tests} runs...")
                results = run_scenario_tests(scen_name, prices, configs, n_tests)
                scen_results[f'{n_tests}_tests'] = results
            
            period_results[scen_name] = scen_results
        
        all_results[period_name] = period_results
    
    # Print summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    
    for period_name in periods.keys():
        print(f"\n📅 {period_name}:")
        for scen_name in ['BULL', 'BEAR', 'SIDEWAYS', 'MIXED']:
            if scen_name in all_results[period_name]:
                # Get results for 1000 tests
                results_1000 = all_results[period_name][scen_name]['1000_tests']
                # Find best config
                best_config = max(results_1000.items(), key=lambda x: x[1]['avg_return'])
                worst_config = min(results_1000.items(), key=lambda x: x[1]['avg_return'])
                
                print(f"  {scen_name}:")
                print(f"    Best: {best_config[0]} ({best_config[1]['avg_return']:.2%})")
                print(f"    Worst: {worst_config[0]} ({worst_config[1]['avg_return']:.2%})")
    
    # Save results
    output_file = 'massive_test_results.json'
    with open(output_file, 'w') as f:
        # Convert numpy types
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        json.dump(all_results, f, indent=2, default=convert)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == '__main__':
    main()
