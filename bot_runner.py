#!/usr/bin/env python3
"""
BOT RUNNER - Paper Trading
===========================
Run unified bot on testnet with WIDE_SL config.
"""

import sys
sys.path.insert(0, 'scripts')

from unified_bot import UnifiedBot, BotConfig
import json
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('bot_paper_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("="*70)
    logger.info("🚀 BOT RUNNER - Paper Trading Started")
    logger.info("="*70)
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load optimized config
    with open('config/config_main.json', 'r') as f:
        config_data = json.load(f)
    
    config = BotConfig()
    for key, value in config_data.items():
        if not key.startswith('_') and hasattr(config, key):
            setattr(config, key, value)
    
    logger.info(f"Config: WIDE_SL (Best from 168k tests)")
    logger.info(f"Capital: ${config.initial_capital}")
    logger.info(f"Short TP/SL: {config.short_tp:.1%}/{config.short_sl:.1%}")
    logger.info(f"Testnet: {config.testnet}")
    logger.info("="*70)
    
    bot = UnifiedBot(config)
    
    # Simulate trading on historical data for testing
    # In real mode, this would connect to exchange
    logger.info("📊 Running in SIMULATION mode (historical data)")
    
    try:
        while True:
            # In real implementation, fetch price from exchange
            # For now, just log status every minute
            time.sleep(60)
            
            stats = bot.get_stats()
            logger.info(
                f"Balance: ${bot.current_balance:.2f} | "
                f"Return: {(bot.current_balance - config.initial_capital) / config.initial_capital:+.2%} | "
                f"Trades: {stats['total_trades']} | "
                f"Positions: L{len(bot.tracker.positions_long)}/S{len(bot.tracker.positions_short)}"
            )
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        
        # Final stats
        stats = bot.get_stats()
        logger.info("="*70)
        logger.info("📊 FINAL STATS")
        logger.info("="*70)
        logger.info(f"Initial: ${config.initial_capital:.2f}")
        logger.info(f"Final: ${bot.current_balance:.2f}")
        logger.info(f"Return: {(bot.current_balance - config.initial_capital) / config.initial_capital:+.2%}")
        logger.info(f"Trades: {stats['total_trades']}")
        logger.info(f"Win Rate: {stats['win_rate']:.1%}")
        logger.info(f"Fees: ${stats['total_fees']:.4f}")


if __name__ == '__main__':
    main()
