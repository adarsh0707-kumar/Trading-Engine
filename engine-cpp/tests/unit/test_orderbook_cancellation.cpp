#include "orderbook/Order.hpp"
#include "orderbook/OrderBook.hpp"

#include <cassert>
#include <iostream>
#include <memory>
#include <stdexcept>

using namespace engine;

std::shared_ptr<Order> make_order(
    const std::string &id,
    Side side,
    double price,
    std::int64_t quantity,
    std::uint64_t sequence)
{
    return std::make_shared<Order>(
        id,
        "AAPL",
        side,
        OrderType::LIMIT,
        price,
        quantity,
        sequence,
        TimeInForce::GTC);
}

int main()
{
    // Test 1: cancel a bid order
    {
        OrderBook book("AAPL");

        auto bid = make_order(
            "B1",
            Side::BUY,
            100.0,
            100,
            1);

        book.add_order(bid);

        assert(book.order_count() == 1);
        assert(book.best_bid() == 100.0);

        bool cancelled = book.cancel_order("B1");

        assert(cancelled);
        assert(bid->status() == OrderStatus::CANCELLED);
        assert(book.order_count() == 0);
        assert(book.bids().empty());
    }

    // Test 2: cancel an ask order
    {
        OrderBook book("AAPL");

        auto ask = make_order(
            "S1",
            Side::SELL,
            101.0,
            100,
            1);

        book.add_order(ask);

        assert(book.order_count() == 1);
        assert(book.best_ask() == 101.0);

        bool cancelled = book.cancel_order("S1");

        assert(cancelled);
        assert(ask->status() == OrderStatus::CANCELLED);
        assert(book.order_count() == 0);
        assert(book.asks().empty());
    }

    // Test 3: cancel one order and preserve other orders
    {
        OrderBook book("AAPL");

        auto bid1 = make_order(
            "B1",
            Side::BUY,
            100.0,
            100,
            1);

        auto bid2 = make_order(
            "B2",
            Side::BUY,
            100.0,
            50,
            2);

        book.add_order(bid1);
        book.add_order(bid2);

        assert(book.order_count() == 2);

        bool cancelled = book.cancel_order("B1");

        assert(cancelled);
        assert(bid1->status() == OrderStatus::CANCELLED);
        assert(bid2->is_active());
        assert(book.order_count() == 1);
        assert(book.best_bid() == 100.0);
        assert(book.bids().at(100.0).front()->order_id() == "B2");
        assert(book.bids().at(100.0).total_quantity() == 50);
    }

    // Test 4: cancel partially filled order
    {
        OrderBook book("AAPL");

        auto bid = make_order(
            "B1",
            Side::BUY,
            100.0,
            100,
            1);

        book.add_order(bid);

        bid->fill(40);

        assert(bid->remaining_quantity() == 60);
        assert(bid->status() == OrderStatus::PARTIALLY_FILLED);
        assert(book.order_count() == 1);

        bool cancelled = book.cancel_order("B1");

        assert(cancelled);
        assert(bid->status() == OrderStatus::CANCELLED);
        assert(book.order_count() == 0);
        assert(book.bids().empty());
    }

    // Test 5: unknown order returns false
    {
        OrderBook book("AAPL");

        auto bid = make_order(
            "B1",
            Side::BUY,
            100.0,
            100,
            1);

        book.add_order(bid);

        bool cancelled = book.cancel_order("UNKNOWN");

        assert(!cancelled);
        assert(book.order_count() == 1);
        assert(bid->is_active());
    }

    // Test 6: empty order ID is rejected
    {
        OrderBook book("AAPL");

        bool threw = false;

        try
        {
            book.cancel_order("");
        }
        catch (const std::invalid_argument &)
        {
            threw = true;
        }

        assert(threw);
    }

    // Test 7: cancellation removes empty price level
    {
        OrderBook book("AAPL");

        auto bid1 = make_order(
            "B1",
            Side::BUY,
            100.0,
            100,
            1);

        auto bid2 = make_order(
            "B2",
            Side::BUY,
            99.0,
            50,
            2);

        book.add_order(bid1);
        book.add_order(bid2);

        assert(book.order_count() == 2);
        assert(book.best_bid() == 100.0);

        bool cancelled = book.cancel_order("B1");

        assert(cancelled);
        assert(book.order_count() == 1);
        assert(book.bids().size() == 1);
        assert(book.best_bid() == 99.0);
        assert(book.bids().at(99.0).front()->order_id() == "B2");
    }

    // Test 8: filled order cannot be cancelled
    {
        OrderBook book("AAPL");

        auto bid = make_order(
            "B1",
            Side::BUY,
            100.0,
            100,
            1);

        book.add_order(bid);

        bid->fill(100);

        assert(bid->is_fully_filled());

        bool threw = false;

        try
        {
            book.cancel_order("B1");
        }
        catch (const std::logic_error &)
        {
            threw = true;
        }

        assert(threw);
        assert(book.order_count() == 1);
    }

    std::cout
        << "All OrderBook cancellation tests passed (8/8)"
        << std::endl;

    return 0;
}