# Strange Adventures - Comic Book Discount Automation

Automatically applies clearance pricing to comic books that are older than 14 days based on date tags.

**Compatible with Lightspeed X-Series (Retail POS)**

## How It Works

1. **Tagging**: When you import new comics, tag them with `new release-YYYY-MM-DD` (e.g., `new release-2025-10-15`)
2. **Automation**: Every Sunday at 2 AM, GitHub Actions runs this script
3. **Processing**: The script finds all comics tagged with dates older than 14 days (only affects products with tags)
4. **Pricing**: Adds items to a "Comics Clearance - 20% Off" price book with discounted prices
5. **Staff Action**: Your staff can manually select the clearance price book at the POS

## Setup Instructions

### 1. Set Up in Lightspeed (One-Time)

Nothing to do! The script automatically creates the "Comics Clearance - 20% Off" price book if it doesn't exist.

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
   - Name: `LIGHTSPEED_API_TOKEN`
     - Value: Your Lightspeed Personal Access Token
   - Name: `LIGHTSPEED_DOMAIN_PREFIX`
     - Value: Your store's domain prefix (e.g., `strangeadventures` from the URL)

**How to get your Lightspeed credentials:**
1. Log into Lightspeed Retail POS (X-Series)
2. Go to **Setup** → **Personal Tokens**
3. Click **Create Personal Token**
4. Give it a name like "GitHub Automation"
5. Copy the generated token (this is your `LIGHTSPEED_API_TOKEN`)
6. Your domain prefix is the first part of your Lightspeed URL:
   - Example: If your URL is `https://strangeadventures.retail.lightspeed.app`
   - Your domain prefix is: `strangeadventures`

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
- **Price Book Name**: Change `PRICE_BOOK_NAME: "Comics Clearance - 20% Off"`
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
LIGHTSPEED X-SERIES COMIC DISCOUNT AUTOMATION
Date: 2025-10-20 09:00:00
======================================================================

Fetching products from Lightspeed X-Series...
  Page 1: Fetched 200 products (Total: 200)
  Page 2: Fetched 145 products (Total: 345)
Total products fetched: 345

Analyzing products for clearance eligibility...
(Only checking products with tags)

Analysis Complete:
  Total products scanned: 345
  Products without any tags: 289
  Products with tags but no date tag: 44
  Products eligible for discount: 12

Products to receive clearance pricing:
----------------------------------------------------------------------

Batman #1
  Tag: new release-2025-09-15
  Age: 35 days
  Retail Price: $4.99
  Clearance Price: $3.99 (20% off)

======================================================================
Updating price book...

  Successfully updated batch of 12 products

======================================================================
SUMMARY
======================================================================
Successfully added 12 products to price book 'Comics Clearance - 20% Off'

Staff can now select the clearance price book at the POS.
======================================================================
```

## At the POS

When ringing up a comic that has been discounted:

1. **Scan or add the item** to the sale
2. **Select the price book** from the POS:
   - Look for "Comics Clearance - 20% Off" price book
   - Or ask the customer if they want the clearance price
3. **Staff activates** the clearance price book for that sale
4. **Customer pays** the discounted price ($3.99 instead of $4.99)

### Training Your Staff

Make sure your staff knows:
- How to activate price books at the POS
- Check for comics that are in the clearance price book
- The clearance price book doesn't change the regular retail price
- They can switch between regular pricing and clearance pricing

## Troubleshooting

### Script isn't running automatically
**Check:**
- GitHub Actions is enabled (Settings → Actions → General)
- The workflow file is in the correct location (`.github/workflows/`)
- The cron schedule is correct for your timezone

### Script runs but no products are discounted
**Possible reasons:**
1. Products don't have any tags at all (script only processes tagged products)
2. Products don't have tags in format `new release-YYYY-MM-DD`
3. Products aren't older than 14 days yet
4. Products don't have a retail price set

**How to debug:**
- Look at the workflow logs (Actions tab)
- Check "Products without any tags" count
- Check "Products with tags but no date tag" count
- Manually verify a few products in Lightspeed have proper tags

### Can't see clearance price at POS
**Solutions:**
1. Verify the script ran successfully (check Actions logs for green checkmark)
2. Check that the price book exists in Lightspeed:
   - Go to **Setup** → **Price Books**
   - Look for "Comics Clearance - 20% Off"
   - Click it to see which products are included
3. Ensure staff know how to activate price books at the POS
4. Check that staff have permission to use price books

### API Token or Domain errors
**Error message**: `FATAL ERROR: 401 Unauthorized` or `403 Forbidden`

**Solutions:**
1. Verify your Personal Access Token is correct in GitHub Secrets
2. Check that your token hasn't been revoked
3. Ensure your token has proper permissions (requires Plus plan)
4. Verify your domain prefix is correct (e.g., `strangeadventures`)
5. Regenerate token in Lightspeed if needed

### Products are being processed multiple times
**This is expected behavior!** The script:
- Updates the price book each time it runs
- Ensures prices stay at 20% off even if retail price changes
- This is safe and won't create duplicate price books

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
- ✅ **Adds** products to clearance price book
- ✅ **Updates** price book with new clearance prices if retail prices changed
- ✅ **Preserves** original retail prices
- ✅ **Only processes** products that have tags
- ❌ **Does NOT** modify retail prices
- ❌ **Does NOT** archive products
- ❌ **Does NOT** remove tags
- ❌ **Does NOT** affect products without tags

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
