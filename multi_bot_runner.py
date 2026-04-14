#!/usr/bin/env python3
"""
MULTI-BOT RUNNER - LIVE TRADING
===============================
Run 3 bots: LOW, MEDIUM, HIGH risk on Hyperliquid testnet.
"""

import sys
sys.path.insert(0, 'scripts')

from unified_bot import UnifiedBot, BotConfig
import json
import time
from datetime import datetime
import logging

# Setup logging for each bot
def setup_logger(name, log_file):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
    logger.addHandler(handler)
    return logger


def run_bot(config_file, log_file, bot_name):
    """Run single bot with live trading."""
    logger = setup_logger(bot_name, log_file)
    
    logger.info("="*70)
    logger.info(f"🚀 {bot_name} BOT STARTED - LIVE TRADING")
    logger.info("="*70)
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load config
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    config = BotConfig()
    for key, value in config_data.items():
        if not key.startswith('_') and hasattr(config, key):
            setattr(config, key, value)
    
    logger.info(f"Capital: ${config.initial_capital}")
    logger.info(f"Short TP/SL: {config.short_tp:.1%}/{config.short_sl:.1%}")
    logger.info(f"Position size: {config.short_position_pct:.0%}")
    logger.info(f"Leverage: {config.short_leverage}x")
    logger.info(f"Symbol: {config.symbol}")
    logger.info("="*70)
    
    bot = UnifiedBot(config)
    
    # Initialize exchange connection
    try:
        import ccxt
        import os
        # Use Hyperliquid with real API keys
        exchange = ccxt.hyperliquid({
            'enableRateLimit': True,
            'apiKey': os.getenv('HYPERLIQUID_API_KEY', ''),
            'secret': os.getenv('HYPERLIQUID_SECRET', ''),
            'testnet': False,  # Use mainnet for real trading
        })
        exchange.load_markets()
        logger.info("✅ Connected to Hyperliquid MAINNET")
        logger.info(f"   API Key: {os.getenv('HYPERLIQUID_API_KEY', '')[:20]}...")
    except Exception as e:
        logger.error(f"❌ Failed to connect to exchange: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    
    # Main loop with actual trading
    cycle = 0
    try:
        while True:
            try:
                # Fetch current price
                ticker = exchange.fetch_ticker(config.symbol)
                current_price = ticker['last']
                
                # Run trading cycle
                bot.run_cycle(current_price)
                
                cycle += 1
                if cycle % 10 == 0:  # Log every 10 cycles (10 min)
                    stats = bot.get_stats()
                    pnl_pct = (bot.current_balance - config.initial_capital) / config.initial_capital
                    
                    logger.info(
                        f"[Cycle {cycle}] Price: ${current_price:.0f} | "
                        f"Balance: ${bot.current_balance:.2f} | "
                        f"PnL: {pnl_pct:+.2%} | Trades: {stats['total_trades']} | "
                        f"WR: {stats['win_rate']:.0%} | Fees: ${stats['total_fees']:.2f}"
                    )
                
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            
            time.sleep(60)  # 1 minute between cycles
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
        stats = bot.get_stats()
        pnl_pct = (bot.current_balance - config.initial_capital) / config.initial_capital
        logger.info(f"FINAL: Balance=${bot.current_balance:.2f}, PnL={pnl_pct:+.2%}, Trades={stats['total_trades']}")


def main():
    """Run all 3 bots in parallel."""
    print("="*70)
    print("🚀 MULTI-BOT RUNNER - Starting 3 bots on Hyperliquid")
    print("="*70)
    
    import multiprocessing
    
    bots = [
        ('config/config_low_risk.json', 'bot_low_risk.log', 'LOW_RISK'),
        ('config/config_medium_risk.json', 'bot_medium_risk.log', 'MEDIUM_RISK'),
        ('config/config_high_risk.json', 'bot_high_risk.log', 'HIGH_RISK'),
    ]
    
    processes = []
    for config_file, log_file, bot_name in bots:
        p = multiprocessing.Process(target=run_bot, args=(config_file, log_file, bot_name))
        p.start()
        processes.append((bot_name, p))
        print(f"✅ {bot_name} started (PID: {p.pid})")
        time.sleep(2)
    
    print("="*70)
    print("All 3 bots running on Hyperliquid testnet!")
    print("Logs: bot_low_risk.log, bot_medium_risk.log, bot_high_risk.log")
    print("="*70)
    
    # Wait for all
    try:
        for name, p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all bots...")
        for name, p in processes:
            p.terminate()
            print(f"  {name} stopped")


if __name__ == '__main__':
    main()
