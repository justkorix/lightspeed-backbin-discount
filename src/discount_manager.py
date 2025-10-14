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
        debug_printed = False

        while True:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                page_products = data.get('data', [])
                if not page_products:
                    break

                # Debug: Print first product structure to see available fields
                if not debug_printed and page_products:
                    import json
                    print(f"\n  DEBUG: Sample product from list API:")
                    sample = page_products[0]
                    print(f"  All fields: {list(sample.keys())}")
                    print(f"  Price-related fields:")
                    price_fields = {k: v for k, v in sample.items() if 'price' in k.lower() or 'tax' in k.lower()}
                    print(f"  {json.dumps(price_fields, indent=4)}")
                    print()
                    debug_printed = True

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

    def get_all_tags(self) -> Dict[str, Dict]:
        """
        Fetch all tags and return as a dictionary keyed by tag ID
        """
        try:
            response = requests.get(f"{self.base_url}/tags", headers=self.headers)
            response.raise_for_status()
            tags_list = response.json().get('data', [])
            # Create a dictionary for fast lookup
            return {tag['id']: tag for tag in tags_list}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tags: {e}")
            return {}

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

        import json

        # Test with just ONE product first
        print("  DEBUG: Testing with SINGLE product first...")
        test_product = products_to_add[0]

        # Use default tax_id if product doesn't have one
        default_tax_id = "06a3b11e-224f-11f0-ecdc-893f1c70d9b9"
        product_tax_id = test_product.get('tax_id') or default_tax_id

        print(f"  DEBUG: Test product details:")
        print(f"    ID: {test_product['id']}")
        print(f"    Name: {test_product['name']}")
        print(f"    Clearance Price: {test_product['clearance_price']}")
        print(f"    Tax ID: {product_tax_id} {'(default)' if not test_product.get('tax_id') else '(from product)'}")

        # Try 1: Using product's tax_id (with fallback to default)
        payload1 = {
            "data": [{
                "product_id": test_product['id'],
                "price_book_id": price_book_id,
                "price": test_product['clearance_price'],
                "tax_id": product_tax_id
            }]
        }

        print(f"\n  DEBUG: Test 1 - With price_book_id (snake_case):")
        print(f"  {json.dumps(payload1, indent=2)}")

        try:
            response = requests.post(
                f"{self.base_url}/price_books/{price_book_id}/products",
                headers=self.headers,
                json=payload1
            )

            print(f"  Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"  Response body: {response.text[:500]}")

            response.raise_for_status()
            print(f"  ✓ Test 1 worked!")

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Test 1 failed: {e}")
            if hasattr(e, 'response') and e.response is not None and e.response.status_code != 500:
                print(f"  Response body: {e.response.text[:300]}")

            # Try 2: camelCase field names
            print(f"\n  DEBUG: Test 2 - camelCase field names:")
            payload2 = {
                "data": [{
                    "productId": test_product['id'],
                    "priceBookId": price_book_id,
                    "price": test_product['clearance_price'],
                    "taxId": product_tax_id
                }]
            }
            print(f"  {json.dumps(payload2, indent=2)}")

            try:
                response = requests.post(
                    f"{self.base_url}/price_books/{price_book_id}/products",
                    headers=self.headers,
                    json=payload2
                )

                print(f"  Response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"  Response body: {response.text[:500]}")

                response.raise_for_status()
                print(f"  ✓ Test 2 worked!")

            except requests.exceptions.RequestException as e:
                print(f"  ✗ Test 2 failed: {e}")
                if hasattr(e, 'response') and e.response is not None and e.response.status_code != 500:
                    print(f"  Response body: {e.response.text[:300]}")

                # Try 3: Without price_book_id
                print(f"\n  DEBUG: Test 3 - Without price_book_id in payload:")
                payload3 = {
                    "data": [{
                        "product_id": test_product['id'],
                        "price": test_product['clearance_price'],
                        "tax_id": product_tax_id
                    }]
                }
                print(f"  {json.dumps(payload3, indent=2)}")

                try:
                    response = requests.post(
                        f"{self.base_url}/price_books/{price_book_id}/products",
                        headers=self.headers,
                        json=payload3
                    )

                    print(f"  Response status: {response.status_code}")
                    if response.status_code != 200:
                        print(f"  Response body: {response.text[:500]}")

                    response.raise_for_status()
                    print(f"  ✓ Test 3 worked!")

                except requests.exceptions.RequestException as e:
                    print(f"  ✗ Test 3 also failed: {e}")
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"  Response body: {e.response.text[:300]}")

                    print("\n  All three tests failed!")
                    print("  The API documentation may have different requirements.")
                    print("  Check: https://x-series-api.lightspeedhq.com/reference")
                    return False

        # If we get here, one of the formats worked
        print("\n  Test successful! Now processing all products in batches...")
        batch_size = 100
        success = True

        for i in range(0, len(products_to_add), batch_size):
            batch = products_to_add[i:i + batch_size]

            try:
                batch_products = []
                for product in batch:
                    product_entry = {
                        "product_id": product['id'],
                        "price": product['clearance_price'],
                        "tax_id": product.get('tax_id') or default_tax_id
                    }
                    batch_products.append(product_entry)

                response = requests.post(
                    f"{self.base_url}/price_books/{price_book_id}/products",
                    headers=self.headers,
                    json={"data": batch_products}
                )
                response.raise_for_status()
                print(f"  Successfully updated batch {i//batch_size + 1} ({len(batch)} products)")

            except requests.exceptions.RequestException as e:
                print(f"  Error updating batch {i//batch_size + 1}: {e}")
                if hasattr(e.response, 'text'):
                    print(f"  Response: {e.response.text[:200]}")
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

        # Fetch all tags once
        print("Fetching all tags...")
        all_tags = self.get_all_tags()
        print(f"Total tags fetched: {len(all_tags)}\n")

        today = datetime.now()
        items_to_discount = []
        items_without_tags = 0
        items_without_date_tags = 0
        items_skipped_no_price = 0

        print("Analyzing products for clearance eligibility...")
        print("(Only checking products with tags)")
        print()

        for product in products:
            product_id = product.get('id')
            product_name = product.get('name', 'Unknown')

            # X-Series stores price and tax_id in price_standard object
            price_standard = product.get('price_standard', {})

            # Use tax_inclusive first (what customer pays), fall back to tax_exclusive
            retail_price = price_standard.get('tax_inclusive') or price_standard.get('tax_exclusive') or 0
            if retail_price:
                retail_price = float(retail_price)
            else:
                retail_price = 0.0

            # Skip products without a retail price
            if retail_price <= 0:
                items_skipped_no_price += 1
                continue

            # Get tax_id from price_standard
            tax_id = price_standard.get('tax_id')

            # Get product tag IDs from product data
            tag_ids = product.get('tag_ids', [])

            if not tag_ids:
                items_without_tags += 1
                continue

            # Look for date tags using tag IDs
            release_date = None
            date_tag = None
            for tag_id in tag_ids:
                tag_data = all_tags.get(tag_id)
                if tag_data:
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
                # Use the same price format that was in the original product
                clearance_price = round(retail_price * (1 - self.discount_percent), 2)

                items_to_discount.append({
                    'id': product_id,
                    'name': product_name,
                    'days_old': days_old,
                    'retail_price': retail_price,
                    'clearance_price': clearance_price,
                    'release_date': release_date,
                    'date_tag': date_tag,
                    'tax_id': tax_id
                })

        print(f"Analysis Complete:")
        print(f"  Total products scanned: {len(products)}")
        print(f"  Products skipped (no retail price): {items_skipped_no_price}")
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
