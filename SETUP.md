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

# Stability AI API Key (for Instagram carousel images)
STABILITY_API_KEY = "sk-your-stability-api-key"
```

## How to Get Each API Key

### 1. Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key and add it to secrets as `GEMINI_API_KEY`
4. **Important:** Enable billing to avoid rate limits

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

### 4. Stability AI API Setup
1. Go to https://platform.stability.ai/
2. Sign up for an account
3. Add credits to your account (pay-as-you-go)
   - Cost: ~$0.002-$0.01 per image
   - Recommended: $10 starting credits
4. Go to "API Keys" section
5. Create a new API key
6. Copy the key (starts with `sk-`) and add it to secrets as `STABILITY_API_KEY`

**Cost Estimates:**
- 7-slide carousel: ~$0.014-$0.07
- 100 carousels/month: ~$1.40-$7.00
- Very affordable for $17/mo Visual Pack pricing

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

### Phase 1: X Thread Generation ✅
- [x] AI thread generation with Gemini
- [x] Free tier (3/day limit)
- [x] Pro tier ($12/mo) verification via Stripe
- [x] X OAuth connection
- [x] Auto-posting to X
- [x] Download threads as .txt
- [x] Multiple tone options
- [x] Adjustable thread length
- [x] Thread history (last 10)
- [x] Edit before posting

### Phase 2: Instagram Carousel Generation ✅
- [x] Visual Pack tier ($17/mo) detection
- [x] Platform selector (X Thread | Instagram Carousel)
- [x] Instagram carousel caption generation
- [x] AI image generation with Stability AI
- [x] Carousel preview with images
- [x] Download ZIP (images + captions)
- [x] Usage tracking (100 carousels/month soft cap)
- [x] Monthly usage reset

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

### Instagram images not generating
- Verify `STABILITY_API_KEY` is set in secrets
- Check Stability AI account has credits
- Look for API errors in Streamlit logs
- Test with smaller carousel (5 slides) first

### Carousel limit showing incorrect count
- Limit resets on the 1st of each month
- Check `st.session_state.carousel_count` value
- Clear browser cache if persistent

## API Cost Breakdown

### Gemini AI (Text Generation)
- X threads: ~$0.001 per thread
- Instagram captions: ~$0.001 per carousel
- Monthly cost for heavy user: ~$3-5

### Stability AI (Image Generation)
- Standard quality: ~$0.002-$0.01 per image
- 7-slide carousel: ~$0.014-$0.07
- 100 carousels/month: ~$1.40-$7.00

### Total API Costs
- Pro user ($12/mo): ~$3-5/month
- Visual Pack user ($17/mo): ~$4.40-$12/month
- **Profit margins**: $7-9 (Pro), $5-12.60 (Visual Pack)

## Support

For issues, check the Streamlit logs or contact support.
