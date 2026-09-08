#include "orderbook/Order.hpp"
#include "orderbook/PriceLevel.hpp"

#include <cassert>
#include <iostream>
#include <memory>
#include <stdexcept>

using namespace engine;

static std::shared_ptr<Order> make_order(
    const std::string &id,
    double price,
    std::int64_t quantity,
    std::int64_t sequence)
{
    return std::make_shared<Order>(
        id,
        "SIM",
        Side::BUY,
        OrderType::LIMIT,
        price,
        quantity,
        sequence);
}

static void test_empty_price_level()
{
    PriceLevel level(100.0);

    assert(level.price() == 100.0);
    assert(level.total_quantity() == 0);
    assert(level.order_count() == 0);
    assert(level.empty());
}

static void test_add_single_order()
{
    PriceLevel level(100.0);

    auto order = make_order(
        "ord-1",
        100.0,
        100,
        1);

    level.add_order(order);

    assert(!level.empty());
    assert(level.order_count() == 1);
    assert(level.total_quantity() == 100);
    assert(level.front() == order);
}

static void test_multiple_orders_preserve_fifo()
{
    PriceLevel level(100.0);

    auto first = make_order(
        "ord-1",
        100.0,
        100,
        1);

    auto second = make_order(
        "ord-2",
        100.0,
        50,
        2);

    auto third = make_order(
        "ord-3",
        100.0,
        25,
        3);

    level.add_order(first);
    level.add_order(second);
    level.add_order(third);

    assert(level.order_count() == 3);
    assert(level.total_quantity() == 175);

    assert(level.front() == first);

    level.remove_front();

    assert(level.front() == second);
    assert(level.total_quantity() == 75);

    level.remove_front();

    assert(level.front() == third);
    assert(level.total_quantity() == 25);

    level.remove_front();

    assert(level.empty());
    assert(level.total_quantity() == 0);
}

static void test_wrong_price_is_rejected()
{
    PriceLevel level(100.0);

    auto order = make_order(
        "ord-1",
        101.0,
        100,
        1);

    bool threw = false;

    try
    {
        level.add_order(order);
    }
    catch (const std::invalid_argument &)
    {
        threw = true;
    }

    assert(threw);
    assert(level.empty());
}

static void test_null_order_is_rejected()
{
    PriceLevel level(100.0);

    bool threw = false;

    try
    {
        level.add_order(nullptr);
    }
    catch (const std::invalid_argument &)
    {
        threw = true;
    }

    assert(threw);
}

static void test_inactive_order_is_rejected()
{
    PriceLevel level(100.0);

    auto order = make_order(
        "ord-1",
        100.0,
        100,
        1);

    order->cancel();

    bool threw = false;

    try
    {
        level.add_order(order);
    }
    catch (const std::invalid_argument &)
    {
        threw = true;
    }

    assert(threw);
}

static void test_empty_front_throws()
{
    PriceLevel level(100.0);

    bool threw = false;

    try
    {
        level.front();
    }
    catch (const std::out_of_range &)
    {
        threw = true;
    }

    assert(threw);
}

static void test_empty_remove_throws()
{
    PriceLevel level(100.0);

    bool threw = false;

    try
    {
        level.remove_front();
    }
    catch (const std::out_of_range &)
    {
        threw = true;
    }

    assert(threw);
}

static void test_partial_fill_quantity_consistency()
{
    PriceLevel level(100.0);

    auto order = make_order(
        "ord-1",
        100.0,
        100,
        1);

    level.add_order(order);

    order->fill(40);

    /*
     * The order now has 60 remaining.
     *
     * The price level total is intentionally not automatically
     * changed here because PriceLevel currently owns queue
     * membership, while matching logic owns fills.
     *
     * MatchingEngine will update the level aggregate when
     * the matching implementation is introduced.
     */
    assert(order->remaining_quantity() == 60);
    assert(level.order_count() == 1);
}

int main()
{
    test_empty_price_level();
    test_add_single_order();
    test_multiple_orders_preserve_fifo();
    test_wrong_price_is_rejected();
    test_null_order_is_rejected();
    test_inactive_order_is_rejected();
    test_empty_front_throws();
    test_empty_remove_throws();
    test_partial_fill_quantity_consistency();

    std::cout
        << "All PriceLevel tests passed (9/9).\n";

    return 0;
}