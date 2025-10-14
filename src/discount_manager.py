import requests
import os
import re
from datetime import datetime
from typing import Optional, List, Dict

class LightspeedXSeriesDiscountManager:
    def __init__(self):
        self.api_token = os.getenv('LIGHTSPEED_API_TOKEN')
        self.domain_prefix = os.getenv('LIGHTSPEED_DOMAIN_PREFIX')
        self.base_url = f"https://{self.domain_prefix}.retail.lightspeed.app/api/2.0"

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        self.tag_prefix = os.getenv('TAG_PREFIX', 'new release-')
        self.price_book_name = os.getenv('PRICE_BOOK_NAME', 'Comics Clearance - 20% Off')
        self.discount_days = int(os.getenv('DISCOUNT_DAYS', '14'))
        self.discount_percent = float(os.getenv('DISCOUNT_PERCENT', '0.20'))

    def extract_date_from_tag(self, tag_name: str) -> Optional[datetime]:
        """
        Extract date from tag like 'new release-2025-10-15'
        Returns datetime object or None if format doesn't match
        """
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

    def get_all_products(self) -> List[Dict]:
        """
        Fetch all active products
        Handles pagination automatically
        """
        products = []
        url = f"{self.base_url}/products"
        params = {
            'page_size': 200,
            'after': 0
        }

        print("Fetching products from Lightspeed X-Series...")
        page = 1

        while True:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                page_products = data.get('data', [])
                if not page_products:
                    break

                products.extend(page_products)
                print(f"  Page {page}: Fetched {len(page_products)} products (Total: {len(products)})")

                version = data.get('version', {})
                if version.get('max') == version.get('min'):
                    break

                params['after'] = version.get('max', 0)
                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching products: {e}")
                break

        print(f"Total products fetched: {len(products)}\n")
        return products

    def get_product_tags(self, product_id: str) -> List[Dict]:
        """
        Fetch tags for a specific product
        """
        try:
            url = f"{self.base_url}/products/{product_id}/tags"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching tags for product {product_id}: {e}")
            return []

    def get_outlets_and_groups(self):
        """
        Fetch outlet and customer group IDs
        Returns (outlet_ids, customer_group_ids)
        """
        outlet_ids = []
        customer_group_ids = []

        try:
            # Fetch outlets
            response = requests.get(f"{self.base_url}/outlets", headers=self.headers)
            response.raise_for_status()
            outlets = response.json().get('data', [])
            outlet_ids = [o['id'] for o in outlets]

            # Fetch customer groups
            response = requests.get(f"{self.base_url}/customer_groups", headers=self.headers)
            response.raise_for_status()
            groups = response.json().get('data', [])
            customer_group_ids = [g['id'] for g in groups]

        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not fetch outlets/groups: {e}")

        return outlet_ids, customer_group_ids

    def get_or_create_price_book(self) -> Optional[str]:
        """
        Get existing clearance price book or create one
        Returns the price_book_id
        """
        # Use API 3.0 for price books
        base_url_v3 = self.base_url.replace('/api/2.0', '/api/3.0')

        try:
            # Check for existing price book
            response = requests.get(
                f"{base_url_v3}/price_books",
                headers=self.headers
            )
            response.raise_for_status()

            price_books = response.json().get('data', [])

            for pb in price_books:
                if pb.get('name') == self.price_book_name:
                    print(f"Found existing price book: {self.price_book_name} (ID: {pb.get('id')})")
                    return pb.get('id')

            # Create new price book if it doesn't exist
            print(f"Creating new price book: {self.price_book_name}")

            # Get outlet and customer group IDs
            outlet_ids, customer_group_ids = self.get_outlets_and_groups()
            print(f"  Outlet IDs: {outlet_ids}")
            print(f"  Customer Group IDs: {customer_group_ids}")

            new_price_book = {
                "name": self.price_book_name,
                "outlet_ids": outlet_ids,
                "customer_group_ids": customer_group_ids
            }
            print(f"  Request payload: {new_price_book}")

            response = requests.post(
                f"{base_url_v3}/price_books",
                headers=self.headers,
                json=new_price_book
            )
            response.raise_for_status()

            result = response.json()
            price_book_id = result.get('data', {}).get('id')
            print(f"Created price book ID: {price_book_id}")
            return price_book_id

        except requests.exceptions.RequestException as e:
            print(f"Error with price book: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def update_price_book_products(self, price_book_id: str, products_to_add: List[Dict]) -> bool:
        """
        Add or update products in the price book with clearance prices
        Processes in batches of 100 (API limit)
        """
        if not products_to_add:
            return True

        # Process in batches of 100
        batch_size = 100
        success = True

        for i in range(0, len(products_to_add), batch_size):
            batch = products_to_add[i:i + batch_size]

            try:
                # Format products for price book API
                price_book_products = []
                for product in batch:
                    price_book_products.append({
                        "product_id": product['id'],
                        "retail_price": product['clearance_price']
                    })

                response = requests.patch(
                    f"{self.base_url}/price_books/{price_book_id}/products",
                    headers=self.headers,
                    json={"price_book_products": price_book_products}
                )
                response.raise_for_status()
                print(f"  Successfully updated batch of {len(batch)} products")

            except requests.exceptions.RequestException as e:
                print(f"  Error updating price book batch: {e}")
                if hasattr(e.response, 'text'):
                    print(f"  Response: {e.response.text}")
                success = False

        return success

    def process_aged_items(self):
        """
        Main processing function: Find items with date tags and apply discounts
        Only processes products that have tags
        """
        print("="*70)
        print("LIGHTSPEED X-SERIES COMIC DISCOUNT AUTOMATION")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        print()

        # Get or create clearance price book
        price_book_id = self.get_or_create_price_book()
        print()

        # Fetch all products
        products = self.get_all_products()

        today = datetime.now()
        items_to_discount = []
        items_without_tags = 0
        items_without_date_tags = 0

        print("Analyzing products for clearance eligibility...")
        print("(Only checking products with tags)")
        print()

        # Debug: Show first few product tags
        debug_count = 0

        for product in products:
            product_id = product.get('id')
            product_name = product.get('name', 'Unknown')
            retail_price = float(product.get('retail_price', 0))

            # Skip products without a retail price
            if retail_price <= 0:
                continue

            # Get product tags
            tags = self.get_product_tags(product_id)

            if not tags:
                items_without_tags += 1
                continue

            # Debug: Show first 5 products with tags
            if debug_count < 5:
                print(f"DEBUG - Product: {product_name}")
                print(f"  Tags: {[t.get('name', 'NO_NAME') for t in tags]}")
                debug_count += 1

            # Look for date tags
            release_date = None
            date_tag = None
            for tag_data in tags:
                tag_name = tag_data.get('name', '')
                if tag_name.startswith(self.tag_prefix):
                    release_date = self.extract_date_from_tag(tag_name)
                    if release_date:
                        date_tag = tag_name
                        break

            if not release_date:
                items_without_date_tags += 1
                continue

            # Calculate age
            days_old = (today - release_date).days

            # Check if item should be discounted
            if days_old > self.discount_days:
                clearance_price = round(retail_price * (1 - self.discount_percent), 2)

                items_to_discount.append({
                    'id': product_id,
                    'name': product_name,
                    'days_old': days_old,
                    'retail_price': retail_price,
                    'clearance_price': clearance_price,
                    'release_date': release_date,
                    'date_tag': date_tag
                })

        print(f"Analysis Complete:")
        print(f"  Total products scanned: {len(products)}")
        print(f"  Products without any tags: {items_without_tags}")
        print(f"  Products with tags but no date tag: {items_without_date_tags}")
        print(f"  Products eligible for discount: {len(items_to_discount)}")
        print()

        if len(items_to_discount) == 0:
            print("No products need discounting at this time.")
            print()
            return

        # Display products to be discounted
        print("Products to receive clearance pricing:")
        print("-"*70)

        for item in items_to_discount:
            print(f"\n{item['name']}")
            print(f"  Tag: {item['date_tag']}")
            print(f"  Age: {item['days_old']} days")
            print(f"  Retail Price: ${item['retail_price']:.2f}")
            print(f"  Clearance Price: ${item['clearance_price']:.2f} ({int(self.discount_percent*100)}% off)")

        # Update price book
        print()
        print("="*70)
        print("Updating price book...")
        print()

        success = self.update_price_book_products(price_book_id, items_to_discount)

        # Summary
        print()
        print("="*70)
        print("SUMMARY")
        print("="*70)
        if success:
            print(f"Successfully added {len(items_to_discount)} products to price book '{self.price_book_name}'")
            print()
            print("Staff can now select the clearance price book at the POS.")
        else:
            print(f"Some products may not have been updated. Check logs above.")
        print("="*70)


def main():
    """Entry point for the script"""
    try:
        manager = LightspeedXSeriesDiscountManager()
        manager.process_aged_items()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
