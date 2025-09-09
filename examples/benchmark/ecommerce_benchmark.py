#!/usr/bin/env python3
"""
E-Commerce Benchmark Scenarios
Tests complex shopping scenarios with the e-commerce API.
"""

import asyncio
import json
import time
from typing import Dict, List, Any
import httpx
from datetime import datetime

# Service URL
ECOMMERCE_URL = "http://localhost:8004"

class EcommerceBenchmark:
    """Test agent for e-commerce scenarios."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.descriptor = None
        self.metrics = {
            "api_calls": 0,
            "tokens_used": 0,
            "errors": 0,
            "start_time": None,
            "scenarios": {}
        }
    
    async def discover_service(self):
        """Discover the e-commerce service via socket-agent."""
        try:
            response = await self.client.get(f"{ECOMMERCE_URL}/.well-known/socket-agent")
            self.descriptor = response.json()
            print(f"✓ Discovered service: {self.descriptor['name']}")
            # Simulate token usage for descriptor
            self.metrics["tokens_used"] += len(json.dumps(self.descriptor)) // 4
        except Exception as e:
            print(f"✗ Failed to discover service: {e}")
            self.metrics["errors"] += 1
    
    async def api_call(self, method: str, path: str, **kwargs):
        """Make an API call and track metrics."""
        self.metrics["api_calls"] += 1
        
        # Simulate token usage for request
        self.metrics["tokens_used"] += 50
        
        try:
            if method == "GET":
                response = await self.client.get(f"{ECOMMERCE_URL}{path}", **kwargs)
            elif method == "POST":
                response = await self.client.post(f"{ECOMMERCE_URL}{path}", **kwargs)
            elif method == "PUT":
                response = await self.client.put(f"{ECOMMERCE_URL}{path}", **kwargs)
            elif method == "DELETE":
                response = await self.client.delete(f"{ECOMMERCE_URL}{path}", **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.text else None
        except Exception as e:
            self.metrics["errors"] += 1
            print(f"  ✗ API call failed: {e}")
            raise
    
    async def scenario_smart_shopping(self):
        """Scenario 1: Smart shopping with budget constraints."""
        print("\n=== Scenario 1: Smart Shopping with Budget ===")
        scenario_start = time.time()
        budget = 500.00
        
        try:
            # Step 1: Browse deals
            print("1. Checking current deals...")
            deals = await self.api_call("GET", "/deals")
            print(f"   Found {len(deals)} products on sale")
            
            # Step 2: Search for specific items
            print("2. Searching for electronics...")
            electronics = await self.api_call("GET", "/products", params={
                "category": "electronics",
                "max_price": 300,
                "sort_by": "rating"
            })
            print(f"   Found {len(electronics)} electronics under $300")
            
            # Step 3: Create cart
            print("3. Creating shopping cart...")
            cart = await self.api_call("POST", "/cart", json={"user_id": "user-001"})
            cart_id = cart["id"]
            
            # Step 4: Add items to cart
            print("4. Adding items to cart...")
            total_spent = 0
            
            # Add a deal item
            if deals:
                deal_item = deals[0]
                await self.api_call("POST", f"/cart/{cart_id}/items", json={
                    "product_id": deal_item["id"],
                    "quantity": 1
                })
                total_spent += deal_item["price"]
                print(f"   Added {deal_item['name']} (${deal_item['price']:.2f} - {deal_item['discount_percent']:.0f}% off)")
            
            # Add top-rated electronics
            for product in electronics[:2]:
                if total_spent + product["price"] <= budget:
                    await self.api_call("POST", f"/cart/{cart_id}/items", json={
                        "product_id": product["id"],
                        "quantity": 1
                    })
                    total_spent += product["price"]
                    print(f"   Added {product['name']} (${product['price']:.2f}, rating: {product['rating']})")
            
            # Step 5: Get cart total
            cart = await self.api_call("GET", f"/cart/{cart_id}")
            print(f"5. Cart total: ${cart['total']:.2f} (including ${cart['tax']:.2f} tax)")
            
            # Step 6: Checkout
            print("6. Proceeding to checkout...")
            order = await self.api_call("POST", "/checkout", json={
                "cart_id": cart_id,
                "user_id": "user-001",
                "shipping_address": {
                    "name": "John Doe",
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip_code": "94102"
                },
                "shipping_method": "standard",
                "payment_method": "credit_card"
            })
            print(f"   Order created: {order['id']}")
            print(f"   Total: ${order['total']:.2f}")
            print(f"   Estimated delivery: {order['estimated_delivery']}")
            
            self.metrics["scenarios"]["smart_shopping"] = {
                "success": True,
                "duration": time.time() - scenario_start,
                "items_purchased": len(cart["items"]),
                "total_spent": order["total"]
            }
            
        except Exception as e:
            print(f"Scenario failed: {e}")
            self.metrics["scenarios"]["smart_shopping"] = {
                "success": False,
                "duration": time.time() - scenario_start,
                "error": str(e)
            }
    
    async def scenario_wishlist_to_cart(self):
        """Scenario 2: Convert wishlist items to cart when in stock."""
        print("\n=== Scenario 2: Wishlist to Cart ===")
        scenario_start = time.time()
        
        try:
            # Step 1: Get user's wishlist
            print("1. Fetching user's wishlist...")
            wishlist = await self.api_call("GET", "/users/user-001/wishlist")
            print(f"   {len(wishlist)} items in wishlist")
            
            # Step 2: Check stock availability
            print("2. Checking stock availability...")
            available_items = []
            for item in wishlist:
                if item["stock"] > 0:
                    available_items.append(item)
                    print(f"   ✓ {item['name']}: {item['stock']} in stock")
                else:
                    print(f"   ✗ {item['name']}: Out of stock")
            
            if available_items:
                # Step 3: Create cart
                print("3. Creating cart for available items...")
                cart = await self.api_call("POST", "/cart", json={"user_id": "user-001"})
                cart_id = cart["id"]
                
                # Step 4: Add available wishlist items to cart
                print("4. Adding available items to cart...")
                for item in available_items:
                    await self.api_call("POST", f"/cart/{cart_id}/items", json={
                        "product_id": item["id"],
                        "quantity": 1
                    })
                    print(f"   Added {item['name']} to cart")
                
                # Step 5: Get cart summary
                cart = await self.api_call("GET", f"/cart/{cart_id}")
                print(f"5. Cart ready with {len(cart['items'])} items")
                print(f"   Total: ${cart['total']:.2f}")
            
            self.metrics["scenarios"]["wishlist_to_cart"] = {
                "success": True,
                "duration": time.time() - scenario_start,
                "wishlist_items": len(wishlist),
                "available_items": len(available_items)
            }
            
        except Exception as e:
            print(f"Scenario failed: {e}")
            self.metrics["scenarios"]["wishlist_to_cart"] = {
                "success": False,
                "duration": time.time() - scenario_start,
                "error": str(e)
            }
    
    async def scenario_review_and_reorder(self):
        """Scenario 3: Review products and reorder favorites."""
        print("\n=== Scenario 3: Review and Reorder ===")
        scenario_start = time.time()
        
        try:
            # Step 1: Search for a popular product
            print("1. Finding popular products...")
            products = await self.api_call("GET", "/products", params={
                "sort_by": "rating",
                "category": "home"
            })
            
            if products:
                popular_product = products[0]
                print(f"   Most popular: {popular_product['name']} (rating: {popular_product['rating']})")
                
                # Step 2: Read reviews
                print("2. Reading product reviews...")
                reviews = await self.api_call("GET", f"/reviews/{popular_product['id']}")
                print(f"   {len(reviews)} reviews found")
                
                # Step 3: Add a review
                print("3. Adding a new review...")
                review_response = await self.api_call("POST", "/reviews", json={
                    "product_id": popular_product["id"],
                    "user_id": "user-002",
                    "rating": 5,
                    "title": "Excellent product!",
                    "comment": "Very satisfied with this purchase. High quality and great value."
                })
                print(f"   Review added: {review_response['review_id']}")
                
                # Step 4: Add to wishlist for future purchase
                print("4. Adding to wishlist...")
                await self.api_call("POST", f"/users/user-002/wishlist/{popular_product['id']}")
                print(f"   Added {popular_product['name']} to wishlist")
                
                # Step 5: Quick reorder
                print("5. Creating quick reorder...")
                cart = await self.api_call("POST", "/cart", json={"user_id": "user-002"})
                await self.api_call("POST", f"/cart/{cart['id']}/items", json={
                    "product_id": popular_product["id"],
                    "quantity": 2
                })
                
                cart_details = await self.api_call("GET", f"/cart/{cart['id']}")
                print(f"   Reorder cart created: ${cart_details['total']:.2f}")
            
            self.metrics["scenarios"]["review_and_reorder"] = {
                "success": True,
                "duration": time.time() - scenario_start
            }
            
        except Exception as e:
            print(f"Scenario failed: {e}")
            self.metrics["scenarios"]["review_and_reorder"] = {
                "success": False,
                "duration": time.time() - scenario_start,
                "error": str(e)
            }
    
    async def scenario_bulk_order(self):
        """Scenario 4: Bulk order with express shipping."""
        print("\n=== Scenario 4: Bulk Order with Express Shipping ===")
        scenario_start = time.time()
        
        try:
            # Step 1: Get categories
            print("1. Browsing categories...")
            categories = await self.api_call("GET", "/categories")
            print(f"   {len(categories)} categories available")
            for cat in categories:
                print(f"   - {cat['name']}: {cat['product_count']} products")
            
            # Step 2: Create bulk order cart
            print("2. Creating bulk order cart...")
            cart = await self.api_call("POST", "/cart", json={"user_id": "user-001"})
            cart_id = cart["id"]
            
            # Step 3: Add multiple items from different categories
            print("3. Adding bulk items...")
            bulk_items = [
                ("prod-006", 5),  # 5 t-shirts
                ("prod-011", 3),  # 3 LED bulb sets
                ("prod-021", 10), # 10 yoga mats
            ]
            
            for product_id, quantity in bulk_items:
                product = await self.api_call("GET", f"/products/{product_id}")
                await self.api_call("POST", f"/cart/{cart_id}/items", json={
                    "product_id": product_id,
                    "quantity": quantity
                })
                print(f"   Added {quantity}x {product['name']}")
            
            # Step 4: Get cart total
            cart = await self.api_call("GET", f"/cart/{cart_id}")
            print(f"4. Bulk order subtotal: ${cart['subtotal']:.2f}")
            
            # Step 5: Checkout with express shipping
            print("5. Checkout with express shipping...")
            order = await self.api_call("POST", "/checkout", json={
                "cart_id": cart_id,
                "user_id": "user-001",
                "shipping_address": {
                    "name": "John Doe",
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip_code": "94102"
                },
                "shipping_method": "express",
                "payment_method": "credit_card"
            })
            
            print(f"   Bulk order created: {order['id']}")
            print(f"   Total with express shipping: ${order['total']:.2f}")
            print(f"   Express delivery by: {order['estimated_delivery']}")
            
            self.metrics["scenarios"]["bulk_order"] = {
                "success": True,
                "duration": time.time() - scenario_start,
                "items_count": sum(q for _, q in bulk_items),
                "total": order["total"]
            }
            
        except Exception as e:
            print(f"Scenario failed: {e}")
            self.metrics["scenarios"]["bulk_order"] = {
                "success": False,
                "duration": time.time() - scenario_start,
                "error": str(e)
            }
    
    async def run_benchmark(self):
        """Run all benchmark scenarios."""
        print("=== E-Commerce API Benchmark ===")
        print(f"Started at: {datetime.now().isoformat()}")
        self.metrics["start_time"] = time.time()
        
        # Discover service
        await self.discover_service()
        
        # Run scenarios
        await self.scenario_smart_shopping()
        await self.scenario_wishlist_to_cart()
        await self.scenario_review_and_reorder()
        await self.scenario_bulk_order()
        
        # Print summary
        duration = time.time() - self.metrics["start_time"]
        print("\n=== Benchmark Summary ===")
        print(f"Total duration: {duration:.2f} seconds")
        print(f"API calls made: {self.metrics['api_calls']}")
        print(f"Tokens used (estimated): {self.metrics['tokens_used']}")
        print(f"Errors encountered: {self.metrics['errors']}")
        print(f"Token efficiency: {self.metrics['tokens_used'] / max(1, self.metrics['api_calls']):.1f} tokens/call")
        
        print("\nScenario Results:")
        for name, result in self.metrics["scenarios"].items():
            status = "✓" if result.get("success") else "✗"
            print(f"  {status} {name}: {result.get('duration', 0):.2f}s")
        
        await self.client.aclose()
        return self.metrics


async def main():
    """Run the e-commerce benchmark."""
    benchmark = EcommerceBenchmark()
    
    print("Make sure the e-commerce service is running:")
    print("  cd examples/benchmark/ecommerce_api && python main.py")
    print("\nPress Enter when ready...")
    input()
    
    try:
        metrics = await benchmark.run_benchmark()
        
        # Save metrics to file
        with open("ecommerce_benchmark_results.json", "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nResults saved to ecommerce_benchmark_results.json")
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted")
    except Exception as e:
        print(f"\nBenchmark failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
