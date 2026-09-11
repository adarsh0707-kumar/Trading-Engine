// Unit tests for Order, matching the "Order validation" list in
// docs/09-testing-strategy.md §3:
//   zero quantity, negative/invalid values, invalid price,
//   unsupported side, valid order — plus lifecycle transitions
//   (partial fill, full fill, cancel) used later by MatchingEngine.

#include "orderbook/Order.hpp"

#include "../TestCheck.hpp"

#include <iostream>
#include <stdexcept>

using namespace engine;

static void test_valid_order_is_new()
{
    Order o("ord-1", "SIM", Side::BUY, OrderType::LIMIT, 101.25, 100, 1);
    CHECK(o.is_valid());
    CHECK(o.status() == OrderStatus::NEW);
    CHECK(o.remaining_quantity() == 100);
    CHECK(o.is_active());
}

static void test_negative_price_is_rejected()
{
    Order o("ord-2", "SIM", Side::SELL, OrderType::LIMIT, -5.0, 10, 2);
    CHECK(!o.is_valid());
    CHECK(o.status() == OrderStatus::REJECTED);
    CHECK(!o.is_active());
}

static void test_zero_price_is_rejected()
{
    Order o("ord-3", "SIM", Side::SELL, OrderType::LIMIT, 0.0, 10, 3);
    CHECK(o.status() == OrderStatus::REJECTED);
}

static void test_zero_quantity_is_rejected()
{
    Order o("ord-4", "SIM", Side::BUY, OrderType::LIMIT, 100.0, 0, 4);
    CHECK(o.status() == OrderStatus::REJECTED);
}

static void test_negative_quantity_is_rejected()
{
    Order o("ord-5", "SIM", Side::BUY, OrderType::LIMIT, 100.0, -10, 5);
    CHECK(o.status() == OrderStatus::REJECTED);
}

static void test_missing_symbol_is_rejected()
{
    Order o("ord-6", "", Side::BUY, OrderType::LIMIT, 100.0, 10, 6);
    CHECK(o.status() == OrderStatus::REJECTED);
}

static void test_partial_fill_updates_status_and_remaining()
{
    Order o("ord-7", "SIM", Side::BUY, OrderType::LIMIT, 101.0, 100, 7);
    o.fill(40);
    CHECK(o.remaining_quantity() == 60);
    CHECK(o.status() == OrderStatus::PARTIALLY_FILLED);
    CHECK(!o.is_fully_filled());
}

static void test_full_fill_sets_filled_status()
{
    Order o("ord-8", "SIM", Side::SELL, OrderType::LIMIT, 101.0, 40, 8);
    o.fill(40);
    CHECK(o.remaining_quantity() == 0);
    CHECK(o.status() == OrderStatus::FILLED);
    CHECK(o.is_fully_filled());
    CHECK(!o.is_active());
}

static void test_overfill_throws()
{
    Order o("ord-9", "SIM", Side::BUY, OrderType::LIMIT, 101.0, 10, 9);
    bool threw = false;
    try
    {
        o.fill(11);
    }
    catch (const std::invalid_argument &)
    {
        threw = true;
    }
    CHECK(threw);
}

static void test_cancel_active_order()
{
    Order o("ord-10", "SIM", Side::BUY, OrderType::LIMIT, 101.0, 10, 10);
    o.cancel();
    CHECK(o.status() == OrderStatus::CANCELLED);
    CHECK(!o.is_active());
}

static void test_cancel_filled_order_throws()
{
    Order o("ord-11", "SIM", Side::BUY, OrderType::LIMIT, 101.0, 10, 11);
    o.fill(10);
    bool threw = false;
    try
    {
        o.cancel();
    }
    catch (const std::logic_error &)
    {
        threw = true;
    }
    CHECK(threw);
}

static void test_fill_on_cancelled_order_throws()
{
    Order o("ord-12", "SIM", Side::BUY, OrderType::LIMIT, 101.0, 10, 12);
    o.cancel();
    bool threw = false;
    try
    {
        o.fill(5);
    }
    catch (const std::logic_error &)
    {
        threw = true;
    }
    CHECK(threw);
}

static void test_to_string_helpers()
{
    CHECK(to_string(Side::BUY) == "BUY");
    CHECK(to_string(Side::SELL) == "SELL");
    CHECK(to_string(OrderType::LIMIT) == "LIMIT");
    CHECK(to_string(TimeInForce::GTC) == "GTC");
    CHECK(to_string(OrderStatus::NEW) == "NEW");
}

int main()
{
    test_valid_order_is_new();
    test_negative_price_is_rejected();
    test_zero_price_is_rejected();
    test_zero_quantity_is_rejected();
    test_negative_quantity_is_rejected();
    test_missing_symbol_is_rejected();
    test_partial_fill_updates_status_and_remaining();
    test_full_fill_sets_filled_status();
    test_overfill_throws();
    test_cancel_active_order();
    test_cancel_filled_order_throws();
    test_fill_on_cancelled_order_throws();
    test_to_string_helpers();

    std::cout << "All Order tests passed (13/13).\n";
    return 0;
}
