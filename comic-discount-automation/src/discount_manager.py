import requests
import os
import re
from datetime import datetime
from typing import Optional, List, Dict

class LightspeedDiscountManager:
    def __init__(self):
        self.api_key = os.getenv('LIGHTSPEED_API_KEY')
        self.account_id = os.getenv('LIGHTSPEED_ACCOUNT_ID')
        self.base_url = f"https://api.lightspeedapp.com/API/V3/Account/{self.account_id}"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.tag_prefix = os.getenv('TAG_PREFIX', 'new release-')
        self.clearance_price_name = os.getenv('CLEARANCE_PRICE_NAME', 'Comics Clearance - 20% Off')
        self.discount_days = int(os.getenv('DISCOUNT_DAYS', '14'))
        self.discount_percent = float(os.getenv('DISCOUNT_PERCENT', '0.20'))
        
    def extract_date_from_tag(self, tag_name: str) -> Optional[datetime]:
        """
        Extract date from tag like 'new release-2025-10-15'
        Returns datetime object or None if format doesn't match
        """
        # Escape special characters in prefix for regex
        escaped_prefix = re.escape(self.tag_prefix)
        pattern = f'{escaped_prefix}(\\d{{4}})-(\\d{{2}})-(\\d{{2}})'
        match = re.search(pattern, tag_name)
        
        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None
        return None
    
    def get_all_items_with_tags(self) -> List[Dict]:
        """
        Fetch all active items with their tags loaded
        Handles pagination automatically
        """
        items = []
        url = f"{self.base_url}/Item.json"
        params = {
            'load_relations': '["ItemTags","Prices"]',
            'archived': 'false',
            'limit': 100
        }
        
        print("Fetching items from Lightspeed...")
        page = 1
        
        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Get items from this page
                page_items = data.get('Item', [])
                if isinstance(page_items, dict):
                    page_items = [page_items]
                
                items.extend(page_items)
                print(f"  Page {page}: Fetched {len(page_items)} items (Total: {len(items)})")
                
                # Check for next page
                attributes = data.get('@attributes', {})
                url = attributes.get('next')
                params = None  # Clear params for pagination URL
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching items: {e}")
                break
        
        print(f"Total items fetched: {len(items)}\n")
        return items
    
    def get_or_create_clearance_price_type(self) -> str:
        """
        Get existing clearance price type or create one
        Returns the useTypeID
        """
        try:
            response = requests.get(
                f"{self.base_url}/ItemPriceType.json",
                headers=self.headers
            )
            response.raise_for_status()
            
            price_types = response.json().get('ItemPriceType', [])
            if isinstance(price_types, dict):
                price_types = [price_types]
            
            # Look for existing clearance price type
            for pt in price_types:
                if pt.get('name') == self.clearance_price_name:
                    print(f"Found existing price type: {self.clearance_price_name} (ID: {pt.get('useTypeID')})")
                    return pt.get('useTypeID')
            
            # Create new price type if it doesn't exist
            print(f"Creating new price type: {self.clearance_price_name}")
            new_price_type = {
                "name": self.clearance_price_name,
                "useType": self.clearance_price_name
            }
            
            response = requests.post(
                f"{self.base_url}/ItemPriceType.json",
                headers=self.headers,
                json=new_price_type
            )
            response.raise_for_status()
            
            result = response.json()
            price_type_id = result.get('ItemPriceType', {}).get('useTypeID')
            print(f"Created price type ID: {price_type_id}")
            return price_type_id
            
        except requests.exceptions.RequestException as e:
            print(f"Error with price type: {e}")
            raise
    
    def update_item_clearance_price(self, item_id: str, original_price: float, 
                                   clearance_price_type_id: str, existing_prices: List[Dict]) -> bool:
        """
        Add or update clearance price for an item
        Returns True if successful
        """
        discounted_price = round(original_price * (1 - self.discount_percent), 2)
        
        # Check if clearance price already exists
        clearance_exists = False
        updated_prices = []
        
        for price in existing_prices:
            if price.get('useTypeID') == str(clearance_price_type_id):
                # Update existing clearance price
                price['amount'] = str(discounted_price)
                clearance_exists = True
            updated_prices.append(price)
        
        # Add new clearance price if it doesn't exist
        if not clearance_exists:
            updated_prices.append({
                "amount": str(discounted_price),
                "useTypeID": str(clearance_price_type_id),
                "useType": self.clearance_price_name
            })
        
        # Update item with new prices
        try:
            update_data = {
                "Prices": {
                    "ItemPrice": updated_prices
                }
            }
            
            response = requests.put(
                f"{self.base_url}/Item/{item_id}.json",
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"    Error updating item: {e}")
            return False
    
    def process_aged_items(self):
        """
        Main processing function: Find items with date tags and apply discounts
        """
        print("="*70)
        print("LIGHTSPEED COMIC DISCOUNT AUTOMATION")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        print()
        
        # Get or create clearance price type
        clearance_price_type_id = self.get_or_create_clearance_price_type()
        print()
        
        # Fetch all items
        items = self.get_all_items_with_tags()
        
        today = datetime.now()
        items_to_discount = []
        items_skipped = 0
        
        print("Analyzing items for clearance eligibility...")
        print()
        
        for item in items:
            item_id = item.get('itemID')
            description = item.get('description', 'Unknown')
            
            # Get item tags
            item_tags = item.get('ItemTags', {}).get('ItemTag', [])
            if isinstance(item_tags, dict):
                item_tags = [item_tags]
            
            # Look for date tags
            release_date = None
            date_tag = None
            for tag_data in item_tags:
                tag_name = tag_data.get('tag', '')
                if tag_name.startswith(self.tag_prefix):
                    release_date = self.extract_date_from_tag(tag_name)
                    if release_date:
                        date_tag = tag_name
                        break
            
            if not release_date:
                items_skipped += 1
                continue
            
            # Calculate age
            days_old = (today - release_date).days
            
            # Check if item should be discounted
            if days_old > self.discount_days:
                # Get default price
                prices = item.get('Prices', {}).get('ItemPrice', [])
                if isinstance(prices, dict):
                    prices = [prices]
                
                default_price = None
                for price in prices:
                    if price.get('useType') == 'Default':
                        default_price = float(price.get('amount', 0))
                        break
                
                if default_price and default_price > 0:
                    items_to_discount.append({
                        'id': item_id,
                        'description': description,
                        'days_old': days_old,
                        'original_price': default_price,
                        'release_date': release_date,
                        'date_tag': date_tag,
                        'existing_prices': prices
                    })
        
        print(f"Analysis Complete:")
        print(f"  Total items scanned: {len(items)}")
        print(f"  Items without date tags: {items_skipped}")
        print(f"  Items eligible for discount: {len(items_to_discount)}")
        print()
        
        if len(items_to_discount) == 0:
            print("No items need discounting at this time.")
            print()
            return
        
        # Apply discounts
        print("Applying clearance prices...")
        print("-"*70)
        
        success_count = 0
        error_count = 0
        
        for item in items_to_discount:
            discounted_price = item['original_price'] * (1 - self.discount_percent)
            
            print(f"\n{item['description']}")
            print(f"  Tag: {item['date_tag']}")
            print(f"  Age: {item['days_old']} days")
            print(f"  Default Price: ${item['original_price']:.2f}")
            print(f"  Clearance Price: ${discounted_price:.2f} ({int(self.discount_percent*100)}% off)")
            
            success = self.update_item_clearance_price(
                item['id'],
                item['original_price'],
                clearance_price_type_id,
                item['existing_prices']
            )
            
            if success:
                print("  ✓ Clearance price applied successfully")
                success_count += 1
            else:
                print("  ✗ Failed to apply clearance price")
                error_count += 1
        
        # Summary
        print()
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Successfully updated: {success_count} items")
        print(f"Errors: {error_count} items")
        print(f"Total processed: {len(items_to_discount)} items")
        print()
        print("Staff can now select the clearance price manually at the POS.")
        print("="*70)


def main():
    """Entry point for the script"""
    try:
        manager = LightspeedDiscountManager()
        manager.process_aged_items()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
