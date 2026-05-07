# AI Security Bot - Quota Management & Improvements

## 🔧 Quota Management Solutions

### Problem: Google Gemini Free Tier Quota Exceeded
The bot was failing with `429 Quota exceeded` errors because Google Gemini's free tier has strict limits:
- **Requests per day**: Limited
- **Requests per minute**: Limited
- **Input tokens per minute**: Limited

### ✅ Solutions Implemented

#### 1. **Progressive Retry with Backoff**
- **3 retry attempts** with increasing delays (30s, 60s, 90s)
- Automatically handles temporary quota issues
- Reduces API call frequency during quota pressure

#### 2. **OpenAI Fallback Integration**
- **Primary**: Google Gemini (`gemini-2.0-flash`)
- **Fallback**: OpenAI (`gpt-3.5-turbo`) when Google quota exceeded
- **Last Resort**: Basic automated analysis (no AI required)

#### 3. **Smart Error Detection**
- Detects quota errors by keywords: "quota", "429", "rate limit"
- Automatically switches to fallback providers
- Graceful degradation ensures reports are always generated

## 📊 Improved Scan Result Formatting

### Before (Raw Output)
```
Starting Nmap 7.80 ( https://nmap.org ) at 2024-01-01 12:00 UTC
Nmap scan report for testphp.vulnweb.com (123.45.67.89)
Host is up (0.12s latency).
PORT    STATE    SERVICE  VERSION
80/tcp  filtered http
443/tcp filtered https
```

### After (Structured Analysis)
```
=== NMAP SECURITY SCAN RESULTS ===
Target: https://testphp.vulnweb.com (testphp.vulnweb.com)
Scan Time: Mon May 6 14:30:00 UTC 2026

RAW OUTPUT:
[original nmap output]

ANALYSIS:
- Port 80 (HTTP) is FILTERED (firewall detected)
- Port 443 (HTTPS) is FILTERED (firewall detected)
```

## 🚀 Setup Instructions

### Required Environment Variables

#### For Telegram Bot (Render):
```bash
TELEGRAM_TOKEN=your_telegram_bot_token
GITHUB_TOKEN=your_github_personal_access_token
REPO_OWNER=your_github_username
REPO_NAME=ai-security-bot
WORKFLOW_FILE=security-scan.yml
```

#### For AI Analysis (GitHub Secrets):
```bash
# Primary AI (Google Gemini)
GOOGLE_API_KEY=your_google_api_key

# Optional Fallback AI (OpenAI)
OPENAI_API_KEY=your_openai_api_key
```

### Getting API Keys

#### Google Gemini API Key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to GitHub secrets as `GOOGLE_API_KEY`

#### OpenAI API Key (Optional):
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to GitHub secrets as `OPENAI_API_KEY`

## 💰 Cost Optimization Strategies

### 1. **Quota Management**
- **Free Tier**: Google Gemini (limited), OpenAI (not free)
- **Paid Tier**: Upgrade Google Gemini for higher limits
- **Hybrid**: Use Google for most scans, OpenAI for quota overflow

### 2. **Scan Frequency Control**
- Implement rate limiting in Telegram bot
- Add cooldown periods between scans
- Cache results for repeated targets

### 3. **Selective AI Usage**
- Use AI only for complex analysis
- Fallback to basic parsing for simple cases
- Batch multiple scans to reduce API calls

## 🔄 Workflow Architecture

```
User Request → Telegram Bot → GitHub Actions → Security Scans → AI Analysis → Report
                                                            ↓
                                               Quota Exceeded?
                                               ↓
                                     Google → OpenAI → Basic Analysis
```

## 📈 Performance Improvements

### Scan Result Quality:
- ✅ **Structured formatting** with headers and analysis sections
- ✅ **Protocol fallback** (HTTP → HTTPS) for better connectivity
- ✅ **Error handling** with meaningful status messages
- ✅ **Basic analysis** even when AI fails

### Reliability:
- ✅ **Retry logic** with exponential backoff
- ✅ **Multiple AI providers** for redundancy
- ✅ **Graceful degradation** ensures reports always generate
- ✅ **Comprehensive logging** for debugging

## 🧪 Testing

### Test Quota Handling:
```bash
# Test with quota exceeded scenario
export GOOGLE_API_KEY="invalid_key_to_force_quota_error"
python ai_security_agent.py https://example.com
```

### Test OpenAI Fallback:
```bash
# Remove Google key to force OpenAI usage
unset GOOGLE_API_KEY
export OPENAI_API_KEY="your_openai_key"
python ai_security_agent.py https://example.com
```

### Test Basic Fallback:
```bash
# Remove all AI keys to test basic analysis
unset GOOGLE_API_KEY OPENAI_API_KEY
python ai_security_agent.py https://example.com
```

## 📋 Migration Guide

### For Existing Users:
1. **Update secrets**: Add `OPENAI_API_KEY` to GitHub if desired
2. **Deploy changes**: Push updated code to trigger new workflow
3. **Test**: Run a scan to verify quota handling works

### For New Users:
1. **Follow setup instructions** above
2. **Start with Google Gemini** (free tier available)
3. **Add OpenAI** when you need higher reliability

## 🎯 Expected Behavior

### Normal Operation:
- Uses Google Gemini for AI analysis
- Generates comprehensive security reports
- Handles network issues gracefully

### Quota Exceeded:
- Automatically retries with backoff
- Falls back to OpenAI if available
- Uses basic analysis as last resort
- Always generates a report (never fails completely)

### Network Issues:
- Tries multiple protocols (HTTP/HTTPS)
- Uses realistic user agents
- Provides clear status in reports

---
*Last updated: May 2026*
*Version: 2.0 - Quota Management & Multi-Provider Support*