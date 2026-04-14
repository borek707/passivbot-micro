# HEARTBEAT.md - PassivBot Crypto

## 📅 Raporty 2x dziennie:
- **09:00 UTC** - poranny raport (start dnia)
- **21:00 UTC** - wieczorny raport (podsumowanie)

## 📊 Co sprawdzać:
1. Status systemd: `systemctl status passivbot-multi`
2. Balance i PnL wszystkich 3 botów
3. Liczba trades
4. Czy są otwarte pozycje

## 🚨 Alerty:
- Crash bota (restart przez systemd)
- 0 trades przez 24h
- Błąd połączenia z HL

## 📁 Pliki:
- Logi: `bot_*_risk.log`
- Status: `bot_status_report.log`
