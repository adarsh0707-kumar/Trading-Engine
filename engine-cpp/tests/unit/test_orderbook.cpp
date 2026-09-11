#include "orderbook/OrderBook.hpp"

#include "../TestCheck.hpp"

#include <cmath>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace
{

    using namespace engine;

    constexpr double EPSILON = 1e-9;

    std::shared_ptr<Order> make_buy(
        const std::string &id,
        double price,
        std::int64_t quantity,
        std::uint64_t sequence)
    {
        return std::make_shared<Order>(
            id,
            "BTC-USD",
            Side::BUY,
            OrderType::LIMIT,
            price,
            quantity,
            sequence,
            TimeInForce::GTC);
    }

    std::shared_ptr<Order> make_sell(
        const std::string &id,
        double price,
        std::int64_t quantity,
        std::uint64_t sequence)
    {
        return std::make_shared<Order>(
            id,
            "BTC-USD",
            Side::SELL,
            OrderType::LIMIT,
            price,
            quantity,
            sequence,
            TimeInForce::GTC);
    }

    void assert_price_equal(double actual, double expected)
    {
        CHECK(std::fabs(actual - expected) < EPSILON);
    }

    /*
     * Test 1
     *
     * A newly created order book must be empty.
     */
    void test_empty_book()
    {
        OrderBook book("BTC-USD");

        CHECK(book.empty());
        CHECK(book.order_count() == 0);
        CHECK(book.bid_level_count() == 0);
        CHECK(book.ask_level_count() == 0);
    }

    /*
     * Test 2
     *
     * best_bid() must reject an empty bid book.
     */
    void test_best_bid_empty_throws()
    {
        OrderBook book("BTC-USD");

        bool threw = false;

        try
        {
            static_cast<void>(book.best_bid());
        }
        catch (const std::out_of_range &)
        {
            threw = true;
        }

        CHECK(threw);
    }

    /*
     * Test 3
     *
     * best_ask() must reject an empty ask book.
     */
    void test_best_ask_empty_throws()
    {
        OrderBook book("BTC-USD");

        bool threw = false;

        try
        {
            static_cast<void>(book.best_ask());
        }
        catch (const std::out_of_range &)
        {
            threw = true;
        }

        CHECK(threw);
    }

    /*
     * Test 4
     *
     * A single BUY order becomes the best bid.
     */
    void test_single_buy_is_best_bid()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 100.0, 10, 1));

        assert_price_equal(book.best_bid(), 100.0);
        CHECK(book.best_bid_level().price() == 100.0);
    }

    /*
     * Test 5
     *
     * A single SELL order becomes the best ask.
     */
    void test_single_sell_is_best_ask()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_sell("S1", 105.0, 10, 1));

        assert_price_equal(book.best_ask(), 105.0);
        CHECK(book.best_ask_level().price() == 105.0);
    }

    /*
     * Test 6
     *
     * Multiple BUY levels must be ordered from highest
     * price to lowest price.
     */
    void test_best_bid_is_highest_buy_price()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 100.0, 10, 1));

        book.add_order(
            make_buy("B2", 105.0, 10, 2));

        book.add_order(
            make_buy("B3", 102.0, 10, 3));

        assert_price_equal(book.best_bid(), 105.0);

        auto it = book.bids().begin();

        assert_price_equal(it->first, 105.0);

        ++it;
        assert_price_equal(it->first, 102.0);

        ++it;
        assert_price_equal(it->first, 100.0);
    }

    /*
     * Test 7
     *
     * Multiple SELL levels must be ordered from lowest
     * price to highest price.
     */
    void test_best_ask_is_lowest_sell_price()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_sell("S1", 110.0, 10, 1));

        book.add_order(
            make_sell("S2", 105.0, 10, 2));

        book.add_order(
            make_sell("S3", 108.0, 10, 3));

        assert_price_equal(book.best_ask(), 105.0);

        auto it = book.asks().begin();

        assert_price_equal(it->first, 105.0);

        ++it;
        assert_price_equal(it->first, 108.0);

        ++it;
        assert_price_equal(it->first, 110.0);
    }

    /*
     * Test 8
     *
     * Adding a better BUY price must update best_bid().
     */
    void test_better_buy_updates_best_bid()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 100.0, 10, 1));

        assert_price_equal(book.best_bid(), 100.0);

        book.add_order(
            make_buy("B2", 103.0, 10, 2));

        assert_price_equal(book.best_bid(), 103.0);

        book.add_order(
            make_buy("B3", 110.0, 10, 3));

        assert_price_equal(book.best_bid(), 110.0);
    }

    /*
     * Test 9
     *
     * Adding a lower BUY price must not change best_bid().
     */
    void test_lower_buy_does_not_change_best_bid()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 105.0, 10, 1));

        book.add_order(
            make_buy("B2", 100.0, 10, 2));

        book.add_order(
            make_buy("B3", 103.0, 10, 3));

        assert_price_equal(book.best_bid(), 105.0);
    }

    /*
     * Test 10
     *
     * Adding a lower SELL price must update best_ask().
     */
    void test_better_sell_updates_best_ask()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_sell("S1", 110.0, 10, 1));

        assert_price_equal(book.best_ask(), 110.0);

        book.add_order(
            make_sell("S2", 108.0, 10, 2));

        assert_price_equal(book.best_ask(), 108.0);

        book.add_order(
            make_sell("S3", 105.0, 10, 3));

        assert_price_equal(book.best_ask(), 105.0);
    }

    /*
     * Test 11
     *
     * Adding a higher SELL price must not change best_ask().
     */
    void test_higher_sell_does_not_change_best_ask()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_sell("S1", 105.0, 10, 1));

        book.add_order(
            make_sell("S2", 110.0, 10, 2));

        book.add_order(
            make_sell("S3", 108.0, 10, 3));

        assert_price_equal(book.best_ask(), 105.0);
    }

    /*
     * Test 12
     *
     * Best bid and best ask must remain independent.
     */
    void test_best_bid_and_ask_are_independent()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 100.0, 10, 1));

        book.add_order(
            make_buy("B2", 105.0, 10, 2));

        book.add_order(
            make_sell("S1", 110.0, 10, 3));

        book.add_order(
            make_sell("S2", 107.0, 10, 4));

        assert_price_equal(book.best_bid(), 105.0);
        assert_price_equal(book.best_ask(), 107.0);
    }

    /*
     * Test 13
     *
     * A BUY price equal to the best bid remains at the same
     * price level.
     */
    void test_equal_buy_price_keeps_best_bid()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 105.0, 10, 1));

        book.add_order(
            make_buy("B2", 105.0, 20, 2));

        assert_price_equal(book.best_bid(), 105.0);
        CHECK(book.bid_level_count() == 1);
        CHECK(book.best_bid_level().order_count() == 2);
    }

    /*
     * Test 14
     *
     * A SELL price equal to the best ask remains at the same
     * price level.
     */
    void test_equal_sell_price_keeps_best_ask()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_sell("S1", 105.0, 10, 1));

        book.add_order(
            make_sell("S2", 105.0, 20, 2));

        assert_price_equal(book.best_ask(), 105.0);
        CHECK(book.ask_level_count() == 1);
        CHECK(book.best_ask_level().order_count() == 2);
    }

    /*
     * Test 15
     *
     * Best bid level must actually contain the highest-price
     * BUY orders.
     */
    void test_best_bid_level_matches_best_bid()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 100.0, 10, 1));

        book.add_order(
            make_buy("B2", 105.0, 25, 2));

        book.add_order(
            make_buy("B3", 102.0, 15, 3));

        assert_price_equal(book.best_bid(), 105.0);
        assert_price_equal(
            book.best_bid_level().price(),
            book.best_bid());

        CHECK(book.best_bid_level().order_count() == 1);
        CHECK(book.best_bid_level().total_quantity() == 25);
    }

    /*
     * Test 16
     *
     * Best ask level must actually contain the lowest-price
     * SELL orders.
     */
    void test_best_ask_level_matches_best_ask()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_sell("S1", 110.0, 10, 1));

        book.add_order(
            make_sell("S2", 105.0, 25, 2));

        book.add_order(
            make_sell("S3", 108.0, 15, 3));

        assert_price_equal(book.best_ask(), 105.0);
        assert_price_equal(
            book.best_ask_level().price(),
            book.best_ask());

        CHECK(book.best_ask_level().order_count() == 1);
        CHECK(book.best_ask_level().total_quantity() == 25);
    }

    /*
     * Test 17
     *
     * Adding only BUY orders must not create ASK levels.
     */
    void test_buy_orders_do_not_create_ask_levels()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_buy("B1", 100.0, 10, 1));

        book.add_order(
            make_buy("B2", 105.0, 10, 2));

        CHECK(book.bid_level_count() == 2);
        CHECK(book.ask_level_count() == 0);

        bool threw = false;

        try
        {
            static_cast<void>(book.best_ask());
        }
        catch (const std::out_of_range &)
        {
            threw = true;
        }

        CHECK(threw);
    }

    /*
     * Test 18
     *
     * Adding only SELL orders must not create BID levels.
     */
    void test_sell_orders_do_not_create_bid_levels()
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_sell("S1", 110.0, 10, 1));

        book.add_order(
            make_sell("S2", 105.0, 10, 2));

        CHECK(book.bid_level_count() == 0);
        CHECK(book.ask_level_count() == 2);

        bool threw = false;

        try
        {
            static_cast<void>(book.best_bid());
        }
        catch (const std::out_of_range &)
        {
            threw = true;
        }

        CHECK(threw);
    }

} // namespace

int main()
{
    test_empty_book();
    test_best_bid_empty_throws();
    test_best_ask_empty_throws();
    test_single_buy_is_best_bid();
    test_single_sell_is_best_ask();
    test_best_bid_is_highest_buy_price();
    test_best_ask_is_lowest_sell_price();
    test_better_buy_updates_best_bid();
    test_lower_buy_does_not_change_best_bid();
    test_better_sell_updates_best_ask();
    test_higher_sell_does_not_change_best_ask();
    test_best_bid_and_ask_are_independent();
    test_equal_buy_price_keeps_best_bid();
    test_equal_sell_price_keeps_best_ask();
    test_best_bid_level_matches_best_bid();
    test_best_ask_level_matches_best_ask();
    test_buy_orders_do_not_create_ask_levels();
    test_sell_orders_do_not_create_bid_levels();

    std::cout
        << "All OrderBook Step 1.4 tests passed (18/18)."
        << std::endl;

    return 0;
}