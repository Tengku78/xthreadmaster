# XThreadMaster Setup Guide

## Required Secrets Configuration

Add these to your Streamlit secrets (`.streamlit/secrets.toml` locally or in Streamlit Cloud dashboard):

```toml
# Gemini AI API Key
GEMINI_API_KEY = "your-gemini-api-key-here"

# Stripe Configuration
STRIPE_SECRET_KEY = "sk_test_..." # or sk_live_...
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/your-actual-payment-link"

# X/Twitter OAuth Credentials
X_CONSUMER_KEY = "your-x-consumer-key"
X_CONSUMER_SECRET = "your-x-consumer-secret"
```

## How to Get Each API Key

### 1. Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key and add it to secrets as `GEMINI_API_KEY`

### 2. Stripe Setup
1. Go to https://dashboard.stripe.com/
2. Create a product for "XThreadMaster Pro"
3. Set up pricing (e.g., $9/month)
4. Create a Payment Link:
   - Go to "Payment Links" in Stripe Dashboard
   - Click "New"
   - Select your product
   - Copy the link (looks like: `https://buy.stripe.com/XXXXX`)
5. Get your Secret Key:
   - Go to "Developers" > "API keys"
   - Copy the "Secret key" (starts with `sk_test_` or `sk_live_`)

### 3. X/Twitter API Setup
1. Go to https://developer.twitter.com/
2. Create a new app (or use existing)
3. Enable "OAuth 1.0a" in app settings
4. Set callback URL to: `https://xthreadmaster.streamlit.app`
5. Get credentials:
   - API Key = `X_CONSUMER_KEY`
   - API Key Secret = `X_CONSUMER_SECRET`

## Deployment

### Local Testing
```bash
streamlit run app.py
```

### Deploy to Streamlit Cloud
1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Deploy from your repository
4. Add secrets in the app settings
5. Make sure callback URL matches your deployed URL

## Features Checklist

- [x] AI thread generation
- [x] Free tier (3/day)
- [x] Pro tier verification via Stripe
- [x] X OAuth connection
- [x] Auto-posting to X
- [x] Download threads as .txt
- [x] Multiple tone options
- [x] Adjustable thread length

## Troubleshooting

### "Access Denied" on payment link
- Make sure `STRIPE_PAYMENT_LINK` is set in secrets
- The link should be a valid Stripe Payment Link

### OAuth not working
- Verify callback URL matches exactly
- Check X API credentials are correct
- Ensure OAuth 1.0a is enabled in X app settings

### Stripe verification not working
- Check `STRIPE_SECRET_KEY` is correct
- Test with your own email first
- Make sure subscription is active in Stripe dashboard

## Support

For issues, check the Streamlit logs or contact support.
