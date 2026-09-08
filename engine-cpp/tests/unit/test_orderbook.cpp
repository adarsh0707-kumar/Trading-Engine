#include "orderbook/OrderBook.hpp"

#include <cassert>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace
{

    std::shared_ptr<engine::Order> make_buy_order(
        const std::string &order_id,
        double price,
        std::int64_t quantity,
        std::uint64_t sequence)
    {
        return std::make_shared<engine::Order>(
            order_id,
            "BTC-USD",
            engine::Side::BUY,
            engine::OrderType::LIMIT,
            price,
            quantity,
            sequence,
            engine::TimeInForce::GTC);
    }

    std::shared_ptr<engine::Order> make_sell_order(
        const std::string &order_id,
        double price,
        std::int64_t quantity,
        std::uint64_t sequence)
    {
        return std::make_shared<engine::Order>(
            order_id,
            "BTC-USD",
            engine::Side::SELL,
            engine::OrderType::LIMIT,
            price,
            quantity,
            sequence,
            engine::TimeInForce::GTC);
    }

    void test_empty_book()
    {
        engine::OrderBook book("BTC-USD");

        assert(book.symbol() == "BTC-USD");
        assert(book.empty());
        assert(book.order_count() == 0);
        assert(book.bid_level_count() == 0);
        assert(book.ask_level_count() == 0);
    }

    void test_empty_book_best_bid_throws()
    {
        engine::OrderBook book("BTC-USD");

        bool threw = false;

        try
        {
            (void)book.best_bid();
        }
        catch (const std::out_of_range &)
        {
            threw = true;
        }

        assert(threw);
    }

    void test_empty_book_best_ask_throws()
    {
        engine::OrderBook book("BTC-USD");

        bool threw = false;

        try
        {
            (void)book.best_ask();
        }
        catch (const std::out_of_range &)
        {
            threw = true;
        }

        assert(threw);
    }

    void test_add_single_buy_order()
    {
        engine::OrderBook book("BTC-USD");

        auto order = make_buy_order(
            "B1",
            100.0,
            10,
            1);

        book.add_order(order);

        assert(!book.empty());
        assert(book.order_count() == 1);
        assert(book.bid_level_count() == 1);
        assert(book.ask_level_count() == 0);

        assert(book.best_bid() == 100.0);
        assert(book.best_bid_level().order_count() == 1);
        assert(book.best_bid_level().total_quantity() == 10);
    }

    void test_add_single_sell_order()
    {
        engine::OrderBook book("BTC-USD");

        auto order = make_sell_order(
            "S1",
            101.0,
            5,
            1);

        book.add_order(order);

        assert(!book.empty());
        assert(book.order_count() == 1);
        assert(book.bid_level_count() == 0);
        assert(book.ask_level_count() == 1);

        assert(book.best_ask() == 101.0);
        assert(book.best_ask_level().order_count() == 1);
        assert(book.best_ask_level().total_quantity() == 5);
    }

    void test_multiple_orders_same_price_share_level()
    {
        engine::OrderBook book("BTC-USD");

        auto order1 = make_buy_order(
            "B1",
            100.0,
            10,
            1);

        auto order2 = make_buy_order(
            "B2",
            100.0,
            20,
            2);

        book.add_order(order1);
        book.add_order(order2);

        assert(book.order_count() == 2);
        assert(book.bid_level_count() == 1);

        const auto &level = book.best_bid_level();

        assert(level.order_count() == 2);
        assert(level.total_quantity() == 30);

        assert(level.front()->order_id() == "B1");
    }

    void test_bid_price_ordering()
    {
        engine::OrderBook book("BTC-USD");

        book.add_order(
            make_buy_order("B1", 100.0, 10, 1));

        book.add_order(
            make_buy_order("B2", 105.0, 10, 2));

        book.add_order(
            make_buy_order("B3", 102.0, 10, 3));

        assert(book.bid_level_count() == 3);
        assert(book.best_bid() == 105.0);

        const auto &bids = book.bids();

        auto it = bids.begin();

        assert(it->first == 105.0);

        ++it;
        assert(it->first == 102.0);

        ++it;
        assert(it->first == 100.0);
    }

    void test_ask_price_ordering()
    {
        engine::OrderBook book("BTC-USD");

        book.add_order(
            make_sell_order("S1", 105.0, 10, 1));

        book.add_order(
            make_sell_order("S2", 101.0, 10, 2));

        book.add_order(
            make_sell_order("S3", 103.0, 10, 3));

        assert(book.ask_level_count() == 3);
        assert(book.best_ask() == 101.0);

        const auto &asks = book.asks();

        auto it = asks.begin();

        assert(it->first == 101.0);

        ++it;
        assert(it->first == 103.0);

        ++it;
        assert(it->first == 105.0);
    }

    void test_best_bid_and_best_ask()
    {
        engine::OrderBook book("BTC-USD");

        book.add_order(
            make_buy_order("B1", 100.0, 10, 1));

        book.add_order(
            make_buy_order("B2", 102.0, 10, 2));

        book.add_order(
            make_sell_order("S1", 105.0, 10, 3));

        book.add_order(
            make_sell_order("S2", 103.0, 10, 4));

        assert(book.best_bid() == 102.0);
        assert(book.best_ask() == 103.0);
    }

    void test_wrong_symbol_rejected()
    {
        engine::OrderBook book("BTC-USD");

        auto order = std::make_shared<engine::Order>(
            "B1",
            "ETH-USD",
            engine::Side::BUY,
            engine::OrderType::LIMIT,
            100.0,
            10,
            1,
            engine::TimeInForce::GTC);

        bool threw = false;

        try
        {
            book.add_order(order);
        }
        catch (const std::invalid_argument &)
        {
            threw = true;
        }

        assert(threw);
        assert(book.empty());
    }

    void test_null_order_rejected()
    {
        engine::OrderBook book("BTC-USD");

        bool threw = false;

        try
        {
            book.add_order(nullptr);
        }
        catch (const std::invalid_argument &)
        {
            threw = true;
        }

        assert(threw);
        assert(book.empty());
    }

    void test_order_count_across_levels()
    {
        engine::OrderBook book("BTC-USD");

        book.add_order(
            make_buy_order("B1", 100.0, 10, 1));

        book.add_order(
            make_buy_order("B2", 101.0, 20, 2));

        book.add_order(
            make_buy_order("B3", 101.0, 30, 3));

        book.add_order(
            make_sell_order("S1", 102.0, 15, 4));

        assert(book.order_count() == 4);
        assert(book.bid_level_count() == 2);
        assert(book.ask_level_count() == 1);
    }

    void test_empty_symbol_rejected()
    {
        bool threw = false;

        try
        {
            engine::OrderBook book("");
        }
        catch (const std::invalid_argument &)
        {
            threw = true;
        }

        assert(threw);
    }

} // namespace

int main()
{
    test_empty_book();
    test_empty_book_best_bid_throws();
    test_empty_book_best_ask_throws();
    test_add_single_buy_order();
    test_add_single_sell_order();
    test_multiple_orders_same_price_share_level();
    test_bid_price_ordering();
    test_ask_price_ordering();
    test_best_bid_and_best_ask();
    test_wrong_symbol_rejected();
    test_null_order_rejected();
    test_order_count_across_levels();
    test_empty_symbol_rejected();

    std::cout << "All OrderBook tests passed (13/13).\n";

    return 0;
}