# PassivBot Micro

## Overview

PassivBot Micro is a lightweight cryptocurrency trading bot designed for small capital ($100-200). It implements a unified trading strategy that adapts to market conditions (bull, bear, sideways).

**⚠️ Warning:** This is an experimental trading bot. Use at your own risk. Always test thoroughly on paper trading before using real funds.

## Features

- **Small Capital Optimized**: Designed specifically for $100-200 accounts
- **Risk Management**: Built-in circuit breakers, position sizing, and reserve capital
- **Maker Fee Optimization**: Uses limit orders to minimize fees (0.015% vs 0.06%)
- **Multi-Strategy**: Automatically adapts to market conditions
- **Paper Trading Support**: Test safely before going live

## Requirements

- Python 3.8+
- ccxt library
- Hyperliquid account with API keys
- Minimum $100 capital recommended

## Installation

```bash
git clone https://github.com/borek707/passivbot-micro.git
cd passivbot-micro
pip install -r requirements.txt
```

## Configuration

1. Copy the example config:
```bash
cp config_example.json config.json
```

2. Edit `config.json` with your settings:
```json
{
  "initial_capital": 150.0,
  "reserve_pct": 0.10,
  "short_leverage": 3.0,
  "short_position_pct": 0.20,
  "long_position_pct": 0.20,
  "exchange": "hyperliquid",
  "symbol": "BTC/USDC:USDC"
}
```

3. Set your API keys as environment variables:
```bash
export HYPERLIQUID_API_KEY="your_api_key"
export HYPERLIQUID_SECRET="your_secret"
```

## Usage

### Paper Trading (Recommended for testing)

```python
python multi_bot_runner.py --testnet
```

### Live Trading

```python
python multi_bot_runner.py
```

### Systemd Service (Linux)

```bash
sudo cp passivbot.service /etc/systemd/system/
sudo systemctl enable --now passivbot
```

## Risk Management

The bot includes several safety mechanisms:

- **Reserve Capital**: 10% of balance kept in reserve
- **Circuit Breaker**: Stops trading after 5% daily loss
- **Position Limits**: Max 1 short + 2 long positions
- **Minimum Order Size**: $10 minimum to avoid rejected orders

## Strategy

The bot uses a unified strategy that adapts to market conditions:

1. **Bounce Detection**: Opens short positions when price bounces up from recent low
2. **Dip Detection**: Opens long positions when price dips from recent high
3. **Trend Following**: Adjusts position sizing based on detected trend

## Important Notes

- **This is not financial advice**
- Always test on paper trading first
- Never trade with money you can't afford to lose
- Past performance does not guarantee future results
- The bot may lose money in certain market conditions

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests welcome. Please test thoroughly before submitting.

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. THE AUTHORS OR COPYRIGHT HOLDERS SHALL NOT BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY.
