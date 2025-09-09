# Socket-Agent Benchmark Suite

A comprehensive multi-service benchmark demonstrating complex agentic behavior using socket-agent for API discovery and interaction.

## Overview

This benchmark suite consists of four independent services that work together to enable realistic agent scenarios:

1. **Grocery Store API** (port 8001) - Online grocery shopping with inventory management
2. **Recipe Service API** (port 8002) - Recipe discovery, nutrition info, and meal planning
3. **Banking API** (port 8003) - Account management, payments, and budget tracking
4. **E-Commerce API** (port 8004) - Full-featured online shopping platform with 25+ products

## Architecture

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Grocery Store  │  │ Recipe Service  │  │   Banking API   │  │  E-Commerce API │
│      :8001      │  │      :8002      │  │      :8003      │  │      :8004      │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                     │                     │                     │
         └─────────────────────┴─────────────────────┴─────────────────────┘
                                           │
                                   ┌───────┴────────┐
                                   │  Agent Client  │
                                   │  (Benchmark)   │
                                   └────────────────┘
```

## Test Scenarios

### Grocery + Recipe + Banking Scenarios

#### 1. Dinner Party Planning
- Find recipes suitable for 6 people
- Generate shopping list with scaled ingredients
- Check bank balance and spending limits
- Create grocery order
- Process payment
- Demonstrates: Multi-service coordination, budget awareness

#### 2. Healthy Eating on Budget
- Check daily spending limits
- Find recipes under calorie threshold
- Calculate meal costs
- Find affordable healthy options
- Save favorites for future use
- Demonstrates: Constraint satisfaction, optimization

#### 3. Payday Pantry Stocking
- Deposit paycheck
- Retrieve favorite recipes
- Generate bulk shopping list
- Stock up on pantry staples
- Update spending limits
- Demonstrates: State management, planning

### E-Commerce Scenarios

#### 4. Smart Shopping with Budget
- Browse current deals and discounts
- Search products by category and price
- Build cart within budget constraints
- Apply optimal shipping method
- Demonstrates: Deal optimization, budget management

#### 5. Wishlist to Cart Conversion
- Check wishlist items for availability
- Move in-stock items to cart
- Handle out-of-stock scenarios
- Demonstrates: Inventory awareness, user preferences

#### 6. Review and Reorder
- Find popular products by rating
- Read and write product reviews
- Quick reorder of favorites
- Demonstrates: Social proof, repeat purchases

#### 7. Bulk Order Processing
- Browse product categories
- Create bulk orders across categories
- Calculate bulk pricing with express shipping
- Demonstrates: Volume purchasing, shipping optimization

## Running the Benchmark

### 1. Start all services (in separate terminals):

```bash
# Terminal 1 - Grocery Store
cd examples/benchmark/grocery_api
python main.py

# Terminal 2 - Recipe Service
cd examples/benchmark/recipe_api
python main.py

# Terminal 3 - Banking
cd examples/benchmark/banking_api
python main.py

# Terminal 4 - E-Commerce
cd examples/benchmark/ecommerce_api
python main.py
```

### 2. Run the benchmarks:

```bash
# Run multi-service benchmark (Grocery + Recipe + Banking)
cd examples/benchmark
python agent_benchmark.py

# Run e-commerce benchmark
cd examples/benchmark
python ecommerce_benchmark.py
```

### 3. Check results:

The benchmark will output real-time progress and save detailed metrics to `benchmark_results.json`.

## Metrics Collected

- **API Calls**: Total number of API calls made
- **Token Usage**: Estimated tokens used (descriptor size + requests)
- **Errors**: Number of failed API calls
- **Duration**: Time taken for each scenario
- **Success Rate**: Which scenarios completed successfully
- **Token Efficiency**: Average tokens per API call

## Key Insights

1. **Discovery Overhead**: Each service descriptor is ~2-3KB, totaling ~10KB for all four services
2. **Token Efficiency**: After initial discovery, each API call uses ~50 tokens
3. **Complex Flows**: Scenarios require 15-30 API calls across services
4. **Error Handling**: Services validate constraints (stock, balance, limits)
5. **E-Commerce Scale**: The e-commerce API provides 25+ products across 5 categories with full shopping cart functionality

## Extending the Benchmark

### Add New Scenarios

```python
async def scenario_meal_prep_week(self):
    """Plan and shop for a week of meal prep."""
    # Your scenario logic here
```

### Add New Services

1. Create a new service directory
2. Implement with socket-agent decorators
3. Update the benchmark to discover and use it

### Modify Constraints

- Adjust bank balances in `banking_api/main.py`
- Change product prices/stock in `grocery_api/main.py`
- Add more recipes in `recipe_api/main.py`
- Modify product catalog in `ecommerce_api/main.py`

## Performance Considerations

- Services use in-memory storage (resets on restart)
- No authentication (simplified for benchmarking)
- Synchronous operations (could be parallelized)
- Local network calls only

## Future Enhancements

1. **Stub Generation**: After N successful calls, generate optimized stubs
2. **Parallel Execution**: Run scenarios concurrently
3. **Load Testing**: Multiple agents hitting services
4. **Real LLM Integration**: Use actual LLM for decision making
5. **Persistence**: Add database backing for state
