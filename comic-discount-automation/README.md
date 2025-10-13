# Strange Adventures - Comic Book Discount Automation

Automatically applies clearance pricing to comic books that are older than 14 days based on date tags.

## How It Works

1. **Tagging**: When you import new comics, tag them with `new release-YYYY-MM-DD` (e.g., `new release-2025-10-15`)
2. **Automation**: Every Sunday at 2 AM, GitHub Actions runs this script
3. **Processing**: The script finds all comics tagged with dates older than 14 days
4. **Pricing**: Adds a "Comics Clearance - 20% Off" price to those items
5. **Staff Action**: Your staff can manually select the clearance price at the POS

## Setup Instructions

### 1. Set Up in Lightspeed (One-Time)

Nothing to do! The script automatically creates the "Comics Clearance - 20% Off" price level if it doesn't exist.

### 2. Set Up GitHub Repository

1. Create a new repository on GitHub called `comic-discount-automation`
2. Upload all the files from this folder to your repository
3. Or use command line:
   ```bash
   cd comic-discount-automation
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/comic-discount-automation.git
   git push -u origin main
   ```

### 3. Add GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these two secrets:
   - Name: `LIGHTSPEED_API_KEY`
     - Value: Your Lightspeed API key
   - Name: `LIGHTSPEED_ACCOUNT_ID`
     - Value: Your Lightspeed account ID

**How to get your Lightspeed credentials:**
1. Log into Lightspeed Retail
2. Go to Setup → API → Personal Token (or API Clients)
3. Create a new token/client if needed
4. Copy your Account ID and API Key

### 4. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, enable GitHub Actions
3. You should see the "Apply Comic Book Discounts" workflow

## Running the Script

### Automatic (Recommended)
The script runs automatically every Sunday at 2 AM MST (9 AM UTC).

### Manual Run (For Testing)
1. Go to **Actions** tab in your repository
2. Click "Apply Comic Book Discounts" workflow
3. Click "Run workflow" button
4. Select branch (main)
5. Click green "Run workflow" button
6. Watch it run and check the logs!

## Configuration

You can adjust these settings in `.github/workflows/apply-discounts.yml`:

### Change Schedule
Edit the cron expression in the workflow file:
- **Current**: `0 9 * * 0` (Every Sunday at 2 AM MST)
- **Daily at 3 AM MST**: `0 10 * * *`
- **Every Wednesday at 2 AM MST**: `0 9 * * 3`
- **Twice a week (Sun & Wed)**: 
  ```yaml
  schedule:
    - cron: '0 9 * * 0'
    - cron: '0 9 * * 3'
  ```

### Change Discount Settings
Edit these environment variables in the workflow file:
- **Discount Days**: Change `DISCOUNT_DAYS: "14"` to different number
- **Discount Percent**: Change `DISCOUNT_PERCENT: "0.20"` (0.20 = 20%)
- **Price Name**: Change `CLEARANCE_PRICE_NAME: "Comics Clearance - 20% Off"`
- **Tag Prefix**: Change `TAG_PREFIX: "new release-"` if you use different tags

## Viewing Logs

After each run:
1. Go to **Actions** tab
2. Click on the latest workflow run
3. Click on "apply-discounts" job
4. Expand steps to see detailed logs
5. You'll see exactly which items were processed

Example log output:
```
LIGHTSPEED COMIC DISCOUNT AUTOMATION
Date: 2025-10-20 09:00:00
======================================================================

Fetching items from Lightspeed...
  Page 1: Fetched 100 items (Total: 100)
  Page 2: Fetched 45 items (Total: 145)
Total items fetched: 145

Analyzing items for clearance eligibility...

Analysis Complete:
  Total items scanned: 145
  Items without date tags: 89
  Items eligible for discount: 12

Applying clearance prices...
----------------------------------------------------------------------

Batman #1
  Tag: new release-2025-09-15
  Age: 35 days
  Default Price: $4.99
  Clearance Price: $3.99 (20% off)
  ✓ Clearance price applied successfully
```

## At the POS

When ringing up a comic that has been discounted:

1. **Scan or add the item** to the sale
2. **POS shows multiple prices** available:
   - Default: $4.99
   - Comics Clearance - 20% Off: $3.99
3. **Staff selects** "Comics Clearance - 20% Off" price
4. **Customer pays** the discounted price ($3.99)

### Training Your Staff

Make sure your staff knows:
- Look for comics with the clearance price available
- Always check if a clearance price is available when selling comics
- The clearance price preserves the original price (it doesn't change the default)
- They manually select which price to charge

## Troubleshooting

### Script isn't running automatically
**Check:**
- GitHub Actions is enabled (Settings → Actions → General)
- The workflow file is in the correct location (`.github/workflows/`)
- The cron schedule is correct for your timezone

### Script runs but no items are discounted
**Possible reasons:**
1. Items don't have tags in format `new release-YYYY-MM-DD`
2. Items aren't older than 14 days yet
3. Items are archived in Lightspeed
4. Items don't have a default price set

**How to debug:**
- Look at the workflow logs (Actions tab)
- Check "Items without date tags" count
- Manually verify a few items in Lightspeed have proper tags

### Can't see clearance price at POS
**Solutions:**
1. Verify the script ran successfully (check Actions logs for green checkmark)
2. Check that the item has the clearance price in Lightspeed:
   - Go to Inventory → Search for item
   - Look at Pricing section
   - Should see "Comics Clearance - 20% Off" price
3. Ensure staff user has permission to view/select multiple price levels
4. If using Lightspeed desktop app, sync the POS

### API Key or Account ID errors
**Error message**: `FATAL ERROR: 401 Unauthorized` or `403 Forbidden`

**Solutions:**
1. Verify your API key is correct in GitHub Secrets
2. Check that your API key hasn't expired
3. Ensure your API key has proper permissions (read/write items)
4. Regenerate API key in Lightspeed if needed

### Items are being processed multiple times
**This is expected behavior!** The script:
- Updates existing clearance prices each time it runs
- Ensures prices stay at 20% off even if default price changes
- This is safe and won't create duplicate price levels

## Testing Locally (Optional)

If you want to test the script on your computer before using GitHub Actions:

1. Install Python 3.11 or higher
2. Clone the repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file (copy from `.env.example`) with your credentials
5. Run the script:
   ```bash
   python src/discount_manager.py
   ```

## Support

For issues with:
- **This script**: Check the Actions logs and troubleshooting section above
- **Lightspeed API**: Contact Lightspeed support or check their documentation
- **GitHub Actions**: Check [GitHub's documentation](https://docs.github.com/en/actions)

## File Structure

```
comic-discount-automation/
├── .github/
│   └── workflows/
│       └── apply-discounts.yml    # GitHub Actions workflow
├── src/
│   └── discount_manager.py        # Main Python script
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## What Gets Updated

The script:
- ✅ **Adds** clearance price level to eligible items
- ✅ **Updates** existing clearance prices if default price changed
- ✅ **Preserves** original default prices
- ❌ **Does NOT** modify default prices
- ❌ **Does NOT** archive items
- ❌ **Does NOT** remove tags

## Security Notes

- Your API credentials are stored securely in GitHub Secrets
- They are never visible in logs or code
- Only this repository's workflows can access them
- You can revoke/change them anytime in GitHub Settings

---

**Store**: Strange Adventures Comic Book Shop  
**Location**: Halifax, Nova Scotia  
**Created**: October 2025  
**Version**: 1.0
