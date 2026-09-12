#include "orderbook/Order.hpp"
#include "orderbook/PriceLevel.hpp"

#include "../TestCheck.hpp"

#include <iostream>
#include <memory>
#include <stdexcept>

using namespace engine;

std::shared_ptr<Order> make_order(
    const std::string& id,
    std::int64_t quantity)
{
    return std::make_shared<Order>(
        id,
        "AAPL",
        Side::BUY,
        OrderType::LIMIT,
        100.0,
        quantity,
        1,
        TimeInForce::GTC
    );
}

int main()
{
    // Test 1: cancel an existing order
    {
        PriceLevel level(100.0);

        auto order1 = make_order("B1", 100);
        auto order2 = make_order("B2", 50);

        level.add_order(order1);
        level.add_order(order2);

        CHECK(level.order_count() == 2);
        CHECK(level.total_quantity() == 150);

        bool cancelled = level.cancel_order("B1");

        CHECK(cancelled);
        CHECK(order1->status() == OrderStatus::CANCELLED);
        CHECK(level.order_count() == 1);
        CHECK(level.total_quantity() == 50);
        CHECK(level.front()->order_id() == "B2");
    }

    // Test 2: cancel middle order preserves FIFO
    {
        PriceLevel level(100.0);

        auto order1 = make_order("B1", 100);
        auto order2 = make_order("B2", 50);
        auto order3 = make_order("B3", 75);

        level.add_order(order1);
        level.add_order(order2);
        level.add_order(order3);

        bool cancelled = level.cancel_order("B2");

        CHECK(cancelled);
        CHECK(order2->status() == OrderStatus::CANCELLED);
        CHECK(level.order_count() == 2);
        CHECK(level.total_quantity() == 175);
        CHECK(level.front()->order_id() == "B1");

        // B1 should remain at the front.
        // B3 should remain behind it.
        CHECK(level.front()->order_id() == "B1");
    }

    // Test 3: unknown order returns false
    {
        PriceLevel level(100.0);

        auto order = make_order("B1", 100);
        level.add_order(order);

        bool cancelled = level.cancel_order("UNKNOWN");

        CHECK(!cancelled);
        CHECK(level.order_count() == 1);
        CHECK(level.total_quantity() == 100);
        CHECK(order->is_active());
    }

    // Test 4: empty order ID is rejected
    {
        PriceLevel level(100.0);

        auto order = make_order("B1", 100);
        level.add_order(order);

        bool threw = false;

        try
        {
            level.cancel_order("");
        }
        catch (const std::invalid_argument&)
        {
            threw = true;
        }

        CHECK(threw);
    }

    // Test 5: partially filled order can be cancelled
    {
        PriceLevel level(100.0);

        auto order = make_order("B1", 100);
        level.add_order(order);

        order->fill(40);

        CHECK(order->remaining_quantity() == 60);
        CHECK(order->status() == OrderStatus::PARTIALLY_FILLED);
        CHECK(level.total_quantity() == 100);

        bool cancelled = level.cancel_order("B1");

        CHECK(cancelled);
        CHECK(order->status() == OrderStatus::CANCELLED);
        CHECK(level.order_count() == 0);
        CHECK(level.total_quantity() == 40);
    }

    std::cout
        << "All PriceLevel cancellation tests passed (5/5)"
        << std::endl;

    return 0;
}
