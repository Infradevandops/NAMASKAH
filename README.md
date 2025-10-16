# Namaskah SMS

**Enterprise SMS Verification Platform**

Namaskah SMS provides instant phone number verification services for 1,807+ online platforms. Our infrastructure delivers temporary phone numbers for SMS and voice verification with guaranteed delivery and automatic refunds.

---

## Services

### SMS Verification
Instant temporary phone numbers for receiving SMS verification codes across 1,807+ supported services including:

- **Social Media**: Instagram, Facebook, Twitter/X, TikTok, Snapchat, LinkedIn
- **Messaging**: WhatsApp, Telegram, Discord, Signal, WeChat, Viber
- **Dating**: Tinder, Bumble, Hinge, OkCupid, Match, POF
- **Finance**: PayPal, Venmo, CashApp, Revolut, Wise, Coinbase
- **E-commerce**: Amazon, eBay, Alibaba, Etsy, Shopify
- **Food Delivery**: Uber Eats, DoorDash, Grubhub, Postmates
- **Gaming**: Steam, Roblox, Twitch, Epic Games
- **Cryptocurrency**: Binance, Kraken, Crypto.com, Gemini
- **General Use**: Any unlisted service

### Voice Verification
Voice call verification with transcription and audio recording for services requiring phone call confirmation.

### Number Rentals
Long-term phone number rentals (minimum 7 days) for sustained verification needs:

**Rental Modes:**
- **Always Ready**: Number remains active 24/7 for instant SMS reception
- **Manual Mode**: 30% discount, requires manual activation before use

**Duration Options:**
- 7 days
- 14 days
- 30 days
- Custom durations available

---

## Pricing

### Verification Services

| Plan | Price per Verification | Discount | Minimum Purchase |
|------|----------------------|----------|------------------|
| **Pay-as-You-Go** | 85¢ | — | None |
| **Developer** | 65¢ | 24% | $50 total funded |
| **Enterprise** | 55¢ | 35% | $200 total funded |

*All prices in USD cents. 1 USD = 1 Namaskah Coin (₵)*

### Number Rentals

**Base Pricing (General Use - Always Ready Mode):**

| Duration | Price |
|----------|-------|
| 7 days | $50.00 |
| 14 days | $90.00 |
| 30 days | $180.00 |

**Service-Specific Pricing Multipliers:**

| Service | Multiplier | 7-Day Price |
|---------|-----------|-------------|
| WhatsApp | 0.6× | $30.00 |
| Telegram | 0.7× | $35.00 |
| Instagram | 0.75× | $37.50 |
| Facebook | 0.75× | $37.50 |
| Google | 0.8× | $40.00 |
| General Use | 1.0× | $50.00 |

*Manual Mode: Apply 30% discount to all rental prices*

---

## Features

### Core Platform
- 🔐 Secure authentication (JWT + Google OAuth)
- 💰 Multi-currency wallet system (Paystack, Bitcoin, Ethereum, Solana, USDT)
- 📊 Real-time analytics dashboard
- 🔔 Webhook notifications for SMS delivery
- 🎁 Referral program (1 free verification per referral)
- 🔑 API access for developers
- 📱 Responsive web interface with dark/light themes

### Security & Compliance
- End-to-end encryption
- HTTPS enforcement
- Rate limiting (100 requests/minute)
- Email verification
- Secure password reset
- Request ID tracking
- GDPR compliant

### Developer Tools
- RESTful API
- API key management
- Webhook integration
- Comprehensive documentation
- Code examples (Python, JavaScript, cURL)

---

## API Overview

### Authentication
```
POST /auth/register    - Create account
POST /auth/login       - User login
POST /auth/google      - Google OAuth
GET  /auth/me          - Get user profile
```

### Verification
```
POST   /verify/create           - Create verification
GET    /verify/{id}             - Check status
GET    /verify/{id}/messages    - Retrieve SMS
DELETE /verify/{id}             - Cancel & refund
```

### Rentals
```
POST /rentals/create        - Rent number
GET  /rentals/active        - List active rentals
POST /rentals/{id}/extend   - Extend duration
POST /rentals/{id}/release  - Early release (50% refund)
```

### Wallet
```
POST /wallet/fund                    - Add funds
POST /wallet/paystack/initialize     - Payment gateway
GET  /wallet/paystack/verify/{ref}   - Verify payment
```

**Full API Documentation**: Available at `/docs` endpoint

---

## Service Guarantees

### Delivery Assurance
- **SMS Delivery**: 60-120 seconds average
- **Automatic Refunds**: Full refund if SMS not received
- **Success Rate**: 95%+ across all services
- **Uptime**: 99.9% platform availability

### Support
- **Response Time**: Within 24 hours
- **Channels**: Email, in-app support tickets
- **Coverage**: 24/7 automated systems, business hours for human support

---

## Payment Methods

- **Paystack**: Bank transfer, card, USSD
- **Cryptocurrency**: Bitcoin (BTC), Ethereum (ETH), Solana (SOL), Tether (USDT)

*All payments are final. Funded balances are for service usage only and cannot be withdrawn.*

---

## Getting Started

1. **Create Account**: Register at the platform
2. **Fund Wallet**: Minimum $5 deposit
3. **Select Service**: Choose from 1,807+ services
4. **Receive Number**: Get temporary phone number instantly
5. **Get Code**: SMS delivered within 60-120 seconds

**New User Bonus**: 1 free verification on signup

### Admin Access

For administrative functions, use the admin panel at `/admin`:

```
Email: admin@namaskah.app
Password: Admin@2024!
```

**Admin Features:**
- View platform statistics (users, revenue, verifications)
- Filter data by time period (7/14/30/60/90 days or all time)
- Monitor most used services
- Manage user accounts
- Add credits to user wallets
- View support tickets and respond to users

---

## Business Inquiries

### Enterprise Solutions
Custom pricing and dedicated support available for high-volume users.

### Partnership Opportunities
API reseller and white-label solutions available.

### Contact
- **Email**: support@namaskah.app
- **Website**: https://namaskah.app
- **Documentation**: https://namaskah.app/docs

---

## License

MIT License

Copyright (c) 2024 Namaskah

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

**Namaskah SMS** • Enterprise-Grade Verification Platform • Version 2.0.0
