#include "orderbook/Order.hpp"
#include "orderbook/PriceLevel.hpp"

#include "../TestCheck.hpp"

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

    CHECK(level.price() == 100.0);
    CHECK(level.total_quantity() == 0);
    CHECK(level.order_count() == 0);
    CHECK(level.empty());
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

    CHECK(!level.empty());
    CHECK(level.order_count() == 1);
    CHECK(level.total_quantity() == 100);
    CHECK(level.front() == order);
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

    CHECK(level.order_count() == 3);
    CHECK(level.total_quantity() == 175);

    // FIFO: first order must be at the front.
    CHECK(level.front() == first);

    // Fully fill first order before removing it.
    first->fill(100);
    level.reduce_quantity(100);

    CHECK(first->is_fully_filled());
    CHECK(level.total_quantity() == 75);

    level.remove_front();

    CHECK(level.order_count() == 2);
    CHECK(level.front() == second);
    CHECK(level.total_quantity() == 75);

    // Fully fill second order.
    second->fill(50);
    level.reduce_quantity(50);

    CHECK(second->is_fully_filled());
    CHECK(level.total_quantity() == 25);

    level.remove_front();

    CHECK(level.order_count() == 1);
    CHECK(level.front() == third);
    CHECK(level.total_quantity() == 25);

    // Fully fill third order.
    third->fill(25);
    level.reduce_quantity(25);

    CHECK(third->is_fully_filled());
    CHECK(level.total_quantity() == 0);

    level.remove_front();

    CHECK(level.empty());
    CHECK(level.order_count() == 0);
    CHECK(level.total_quantity() == 0);
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

    CHECK(threw);
    CHECK(level.empty());
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

    CHECK(threw);
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

    CHECK(threw);
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

    CHECK(threw);
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

    CHECK(threw);
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
     * PriceLevel does not automatically observe Order::fill().
     * MatchingEngine is responsible for keeping the aggregate
     * price-level quantity synchronized during matching.
     */

    CHECK(order->remaining_quantity() == 60);
    CHECK(level.order_count() == 1);

    // The level aggregate is still 100 until matching logic
    // explicitly reduces it.
    CHECK(level.total_quantity() == 100);
}

static void test_partial_order_cannot_be_removed()
{
    PriceLevel level(100.0);

    auto order = make_order(
        "ord-1",
        100.0,
        100,
        1);

    level.add_order(order);

    // Partially fill the order.
    order->fill(40);
    level.reduce_quantity(40);

    CHECK(order->remaining_quantity() == 60);
    CHECK(!order->is_fully_filled());
    CHECK(level.total_quantity() == 60);
    CHECK(level.order_count() == 1);

    bool threw = false;

    try
    {
        level.remove_front();
    }
    catch (const std::logic_error &)
    {
        threw = true;
    }

    CHECK(threw);

    // Order must remain in the queue.
    CHECK(!level.empty());
    CHECK(level.order_count() == 1);
    CHECK(level.front() == order);
    CHECK(level.total_quantity() == 60);
}

static void test_remove_fully_filled_order()
{
    PriceLevel level(100.0);

    auto order = make_order(
        "ord-1",
        100.0,
        100,
        1);

    level.add_order(order);

    CHECK(level.order_count() == 1);
    CHECK(level.total_quantity() == 100);

    // Fully fill the order.
    order->fill(100);
    level.reduce_quantity(100);

    CHECK(order->is_fully_filled());
    CHECK(level.total_quantity() == 0);

    level.remove_front();

    CHECK(level.empty());
    CHECK(level.order_count() == 0);
    CHECK(level.total_quantity() == 0);
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
    test_partial_order_cannot_be_removed();
    test_remove_fully_filled_order();

    std::cout
        << "All PriceLevel tests passed (11/11).\n";

    return 0;
}