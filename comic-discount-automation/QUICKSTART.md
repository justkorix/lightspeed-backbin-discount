# Quick Start Guide - Strange Adventures Comic Discount Automation

## 🚀 5-Minute Setup

### Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `comic-discount-automation`
3. Make it **Private** (recommended)
4. Click "Create repository"

### Step 2: Upload These Files
1. Click "uploading an existing file"
2. Drag ALL files from the `comic-discount-automation` folder
3. Click "Commit changes"

### Step 3: Add Your API Credentials
1. In your repository, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these two secrets:
   ```
   Name: LIGHTSPEED_API_KEY
   Value: [paste your API key here]
   
   Name: LIGHTSPEED_ACCOUNT_ID  
   Value: [paste your account ID here]
   ```

### Step 4: Test It!
1. Go to **Actions** tab
2. Click "Apply Comic Book Discounts"
3. Click "Run workflow" → "Run workflow"
4. Wait 30-60 seconds
5. Click on the running workflow to see logs

## ✅ Success Checklist

- [ ] Repository created on GitHub
- [ ] All files uploaded
- [ ] Both secrets added (API key and Account ID)
- [ ] Workflow runs successfully (green checkmark)
- [ ] Can see clearance prices in Lightspeed

## 📋 Daily Workflow

### When Adding New Comics:
1. Import comics to Lightspeed as usual
2. Add tag: `new release-2025-10-15` (use actual date)
3. That's it! The automation handles the rest

### At the Register:
1. Scan comic book
2. If multiple prices show, select clearance price if appropriate
3. Complete sale

## 🔧 Common Changes

### Change discount from 20% to 25%:
Edit `.github/workflows/apply-discounts.yml`
```yaml
DISCOUNT_PERCENT: "0.25"  # Change from 0.20 to 0.25
```

### Change from 14 days to 21 days:
Edit `.github/workflows/apply-discounts.yml`
```yaml
DISCOUNT_DAYS: "21"  # Change from 14 to 21
```

### Run daily instead of weekly:
Edit `.github/workflows/apply-discounts.yml`
```yaml
schedule:
  - cron: '0 9 * * *'  # Change from '0 9 * * 0' to '0 9 * * *'
```

## 🆘 Getting Help

**Script not working?**
1. Check Actions tab for error messages
2. Verify secrets are set correctly
3. Check README.md troubleshooting section

**Need to update settings?**
1. Edit `.github/workflows/apply-discounts.yml`
2. Commit the changes
3. Next run will use new settings

**Questions about Lightspeed API?**
- Contact Lightspeed support
- Check: https://developers.lightspeedhq.com/retail/

## 📞 Support Checklist

When contacting support, have ready:
- [ ] Link to your GitHub Actions run (with errors)
- [ ] Your Lightspeed Account ID
- [ ] Example item that should be discounted but isn't
- [ ] Screenshot of the issue

---

**That's it! You're all set. The script will run every Sunday at 2 AM automatically.**
