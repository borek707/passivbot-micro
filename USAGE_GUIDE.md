# PassivBot Micro - Usage Guide

## 🧪 Tests Performed

### 168,000+ Backtests Completed

The bot was extensively tested across multiple scenarios:

| Test Suite | Tests | Purpose |
|------------|-------|---------|
| `complete_tests_1000.py` | 168,000 | 8 configs × 7 scenarios × 3 periods × 1000 runs |
| `test_comprehensive_scenarios.py` | 378,000 | Bull, Bear, Sideways, Crash, Recovery scenarios |
| `analyze_what_breaks.py` | 1,000+ | Parameter optimization analysis |
| `extended_tests_optimized.py` | 66,000 | Extended period testing (30d-365d) |

### Key Findings from Tests:

**Best Performing Configs:**
1. **WIDE_SL**: +4.15% average (best in sideways/crash)
2. **TIGHT_SL**: +2.01% average (best in bull/mixed)
3. **AGGRESSIVE**: +2.54% average

**Important Discovery:**
- Tests revealed the original code had a bug: it used percentage change instead of bounce from min/max
- Fixed in v0.1.0: Now correctly calculates bounce from recent low/high
- Lowered thresholds from 1.5% to 0.5% for better trade frequency

### Test Data Included in Repo:
- `complete_test_results_1000.json` - Full test results
- `config_analysis_results.json` - Parameter analysis
- `extended_optimized_results.json` - Extended period tests

---

## 🚀 Best Practices for Using the Bot

### Phase 1: Paper Trading (Minimum 7 Days)

```bash
# 1. Clone and setup
git clone https://github.com/borek707/passivbot-micro.git
cd passivbot-micro
pip install -r requirements.txt

# 2. Configure for paper trading
cp config_example.json config.json
# Edit: set "testnet": true

# 3. Run for 7 days minimum
python multi_bot_runner.py
```

**What to watch:**
- Bot opens trades within 24-48 hours
- Win rate should be >40% (sideways market)
- No crashes or errors in logs

### Phase 2: Small Live Test ($50-100)

Only after 7 successful days of paper trading:

```bash
# 1. Set real API keys
export HYPERLIQUID_API_KEY="your_key"
export HYPERLIQUID_SECRET="your_secret"

# 2. Update config for mainnet
# Edit config.json: set "testnet": false

# 3. Start with small capital ($50-100)
python multi_bot_runner.py
```

### Phase 3: Full Deployment

After 2-4 weeks of successful small tests:
- Can increase to $200 capital
- Monitor daily
- Keep 10-20% reserve

---

## 🔑 Required API Keys

### ONLY Hyperliquid Keys Required

```bash
export HYPERLIQUID_API_KEY="your_api_key"
export HYPERLIQUID_SECRET="your_secret"
```

**NO other API keys needed:**
- ❌ No Binance keys
- ❌ No Coinbase keys  
- ❌ No Slack webhook (optional)
- ❌ No other exchange keys

### Getting Hyperliquid Keys:

1. Create account at https://app.hyperliquid.xyz/
2. Go to API Management
3. Create new API key
4. Copy key + secret
5. Set as environment variables (never hardcode!)

### Optional: Slack Notifications

If you want Slack alerts:
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

---

## ⚠️ Common Issues & Solutions

### Issue: "0 trades after 24h"
**Cause:** Market too stable or thresholds too high
**Solution:** Check logs, lower `short_bounce_threshold` to 0.003

### Issue: "Rate limit errors"
**Cause:** API called too frequently
**Solution:** Already fixed - bot uses `enableRateLimit: True`

### Issue: "Bot crashes"
**Cause:** Usually API connection issues
**Solution:** Check systemd status, restart with `sudo systemctl restart passivbot-multi`

---

## 📊 Expected Performance

Based on 168,000+ backtests:

| Market | Expected Monthly | Win Rate | Drawdown |
|--------|-------------------|----------|----------|
| Bull | +2-5% | 45-55% | 3-5% |
| Bear | +3-8% | 50-60% | 5-8% |
| Sideways | -1 to +2% | 40-50% | 2-4% |

**Important:** These are estimates from backtests. Real results vary.

---

## 🛑 When to STOP the Bot

Immediately stop if:
1. Daily loss exceeds 5% for 3 consecutive days
2. Win rate drops below 30% over 1 week
3. Bot crashes more than 2x per day
4. You're emotionally stressed about losses

```bash
sudo systemctl stop passivbot-multi
```

---

## 📖 Additional Resources

- `README.md` - Full documentation
- `config_example.json` - Configuration template
- `.env.example` - Environment variables template
- `scripts/` - Test scripts (for reference)

**Remember:** Never trade with money you can't afford to lose!
