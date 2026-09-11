#include "orderbook/BookSnapshot.hpp"
#include "orderbook/Order.hpp"
#include "orderbook/OrderBook.hpp"

#include "../TestCheck.hpp"

#include <iostream>
#include <memory>
#include <stdexcept>

using namespace engine;

namespace
{

std::shared_ptr<Order> make_order(
    const std::string& id,
    Side side,
    double price,
    std::int64_t quantity,
    std::uint64_t sequence)
{
    return std::make_shared<Order>(
        id,
        "BTC-USD",
        side,
        OrderType::LIMIT,
        price,
        quantity,
        sequence,
        TimeInForce::GTC
    );
}

void test_empty_book()
{
    OrderBook book("BTC-USD");

    const BookSnapshot snapshot = book.snapshot();

    CHECK(snapshot.empty());
    CHECK(snapshot.bids.empty());
    CHECK(snapshot.asks.empty());
    CHECK(snapshot.total_bid_quantity() == 0);
    CHECK(snapshot.total_ask_quantity() == 0);
}

void test_bid_snapshot()
{
    OrderBook book("BTC-USD");

    book.add_order(
        make_order("B1", Side::BUY, 105.0, 300, 1)
    );

    book.add_order(
        make_order("B2", Side::BUY, 103.0, 150, 2)
    );

    const BookSnapshot snapshot = book.snapshot();

    CHECK(snapshot.bids.size() == 2);

    CHECK(snapshot.bids[0].price == 105.0);
    CHECK(snapshot.bids[0].quantity == 300);

    CHECK(snapshot.bids[1].price == 103.0);
    CHECK(snapshot.bids[1].quantity == 150);

    CHECK(snapshot.total_bid_quantity() == 450);
}

void test_ask_snapshot()
{
    OrderBook book("BTC-USD");

    book.add_order(
        make_order("A1", Side::SELL, 106.0, 200, 1)
    );

    book.add_order(
        make_order("A2", Side::SELL, 108.0, 350, 2)
    );

    const BookSnapshot snapshot = book.snapshot();

    CHECK(snapshot.asks.size() == 2);

    CHECK(snapshot.asks[0].price == 106.0);
    CHECK(snapshot.asks[0].quantity == 200);

    CHECK(snapshot.asks[1].price == 108.0);
    CHECK(snapshot.asks[1].quantity == 350);

    CHECK(snapshot.total_ask_quantity() == 550);
}

void test_multiple_orders_same_price_are_aggregated()
{
    OrderBook book("BTC-USD");

    book.add_order(
        make_order("B1", Side::BUY, 105.0, 100, 1)
    );

    book.add_order(
        make_order("B2", Side::BUY, 105.0, 200, 2)
    );

    const BookSnapshot snapshot = book.snapshot();

    CHECK(snapshot.bids.size() == 1);
    CHECK(snapshot.bids[0].price == 105.0);
    CHECK(snapshot.bids[0].quantity == 300);
}

void test_price_ordering()
{
    OrderBook book("BTC-USD");

    book.add_order(
        make_order("B1", Side::BUY, 101.0, 100, 1)
    );

    book.add_order(
        make_order("B2", Side::BUY, 105.0, 100, 2)
    );

    book.add_order(
        make_order("B3", Side::BUY, 103.0, 100, 3)
    );

    book.add_order(
        make_order("A1", Side::SELL, 110.0, 100, 4)
    );

    book.add_order(
        make_order("A2", Side::SELL, 106.0, 100, 5)
    );

    book.add_order(
        make_order("A3", Side::SELL, 108.0, 100, 6)
    );

    const BookSnapshot snapshot = book.snapshot();

    CHECK(snapshot.bids[0].price == 105.0);
    CHECK(snapshot.bids[1].price == 103.0);
    CHECK(snapshot.bids[2].price == 101.0);

    CHECK(snapshot.asks[0].price == 106.0);
    CHECK(snapshot.asks[1].price == 108.0);
    CHECK(snapshot.asks[2].price == 110.0);
}

void test_snapshot_is_independent()
{
    OrderBook book("BTC-USD");

    book.add_order(
        make_order("B1", Side::BUY, 105.0, 100, 1)
    );

    BookSnapshot snapshot = book.snapshot();

    snapshot.bids[0].quantity = 999;

    const BookSnapshot second_snapshot = book.snapshot();

    CHECK(second_snapshot.bids[0].quantity == 100);
}

} // namespace

int main()
{
    test_empty_book();
    test_bid_snapshot();
    test_ask_snapshot();
    test_multiple_orders_same_price_are_aggregated();
    test_price_ordering();
    test_snapshot_is_independent();

    std::cout
        << "All BookSnapshot tests passed (6/6)"
        << std::endl;

    return 0;
}
