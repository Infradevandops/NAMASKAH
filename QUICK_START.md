# ⚡ Quick Start Guide

## 🎯 What This Is

**Namaskah SMS** - Simple SMS verification service using TextVerified API.

Get temporary phone numbers for verifying accounts on WhatsApp, Telegram, Google, Discord, and 100+ other services.

## 🚀 Get Running in 3 Steps

### Step 1: Configure
```bash
cp .env.example .env
nano .env  # Add your TextVerified credentials
```

### Step 2: Install & Run
```bash
./start.sh
```

### Step 3: Use It
Open browser: `http://localhost:8000`

### Step 4: Login
**Default credentials:**
```
Admin:  admin@namaskah.app / admin123
User:   user@namaskah.app / user123  
Demo:   test@example.com / test123
```

## 📱 How to Use

1. **Login** - Use credentials above or register new account
2. **Select Service** - Choose WhatsApp, Telegram, etc.
3. **Get Number** - Receive temporary phone number
4. **Verify** - Use number on the service
5. **Get Code** - Check messages for verification code

## 🔑 Get TextVerified API Key

1. Go to [textverified.com](https://www.textverified.com)
2. Create account
3. Add funds ($1 minimum)
4. Get API key from dashboard
5. Add to `.env` file

## 📊 Project Structure

```
Namaskah.app/
├── main.py           # Backend (200 lines)
├── static/           # CSS & JavaScript
├── templates/        # HTML interface
├── requirements.txt  # Dependencies
└── .env             # Your config
```

## 🎨 Features

- ✅ Clean web interface
- ✅ User authentication
- ✅ 100+ services supported
- ✅ Real-time message checking
- ✅ Copy phone numbers
- ✅ Mobile responsive

## 🐛 Common Issues

**Port already in use?**
```bash
# Change port in main.py (last line)
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Missing dependencies?**
```bash
pip install -r requirements.txt
```

**Database errors?**
```bash
rm sms.db  # Delete and restart
```

## 📖 More Info

- Full docs: `README.md`
- API docs: `http://localhost:8000/docs`
- Test API: `./test_api.sh`

## 🚢 Deploy to Cloud

**Railway (Easiest)**
```bash
railway login
railway init
railway up
```

**Render**
1. Connect GitHub
2. Add env vars
3. Deploy

**Docker**
```bash
docker build -t namaskah .
docker run -p 8000:8000 --env-file .env namaskah
```

---

**That's it! You're ready to go.** 🎉
