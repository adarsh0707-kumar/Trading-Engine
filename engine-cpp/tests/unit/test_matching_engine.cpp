#include "matching/MatchingEngine.hpp"

#include <cassert>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace
{

    using engine::MatchingEngine;
    using engine::MatchResult;
    using engine::Order;
    using engine::OrderBook;
    using engine::OrderType;
    using engine::Side;
    using engine::TimeInForce;

    std::shared_ptr<Order> make_order(
        const std::string &id,
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
            TimeInForce::GTC);
    }

    void test_buy_matches_best_ask()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 10, 2);

        book.add_order(resting_sell);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_buy);

        assert(result.matched);
        assert(result.trades.size() == 1);

        assert(
            result.trades.front()->price() == 100.0);

        assert(
            result.trades.front()->quantity() == 10);

        assert(
            incoming_buy->remaining_quantity() == 0);

        assert(
            resting_sell->remaining_quantity() == 0);
    }

    void test_sell_matches_best_bid()
    {
        OrderBook book("BTC-USD");

        auto resting_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        auto incoming_sell =
            make_order("S1", Side::SELL, 99.0, 10, 2);

        book.add_order(resting_buy);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_sell);

        assert(result.matched);
        assert(result.trades.size() == 1);

        assert(
            result.trades.front()->price() == 100.0);

        assert(
            result.trades.front()->quantity() == 10);

        assert(
            incoming_sell->remaining_quantity() == 0);

        assert(
            resting_buy->remaining_quantity() == 0);
    }

    void test_non_crossing_buy_does_not_match()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 105.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 100.0, 10, 2);

        book.add_order(resting_sell);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_buy);

        assert(!result.matched);
        assert(result.trades.empty());

        assert(
            incoming_buy->remaining_quantity() == 10);

        assert(
            resting_sell->remaining_quantity() == 10);
    }

    void test_non_crossing_sell_does_not_match()
    {
        OrderBook book("BTC-USD");

        auto resting_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        auto incoming_sell =
            make_order("S1", Side::SELL, 105.0, 10, 2);

        book.add_order(resting_buy);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_sell);

        assert(!result.matched);
        assert(result.trades.empty());

        assert(
            incoming_sell->remaining_quantity() == 10);

        assert(
            resting_buy->remaining_quantity() == 10);
    }

    void test_exact_price_match()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 100.0, 10, 2);

        book.add_order(resting_sell);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_buy);

        assert(result.matched);
        assert(result.trades.size() == 1);

        assert(
            result.trades.front()->price() == 100.0);
    }

    void test_trade_quantity_is_minimum()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 5, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 10, 2);

        book.add_order(resting_sell);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_buy);

        assert(result.matched);
        assert(result.trades.size() == 1);

        assert(
            result.trades.front()->quantity() == 5);

        assert(
            incoming_buy->remaining_quantity() == 5);

        assert(
            resting_sell->remaining_quantity() == 0);
    }

    void test_trade_uses_resting_order_price()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 110.0, 10, 2);

        book.add_order(resting_sell);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_buy);

        assert(result.matched);

        assert(
            result.trades.front()->price() == 100.0);
    }

    void test_fully_filled_resting_order_removed()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 10, 2);

        book.add_order(resting_sell);

        assert(book.ask_level_count() == 1);

        MatchingEngine matcher;

        matcher.match(book, incoming_buy);

        assert(book.ask_level_count() == 0);
    }

    void test_price_level_quantity_updates_after_match()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 4, 2);

        book.add_order(resting_sell);

        assert(
            book.best_ask_level().total_quantity() == 10);

        MatchingEngine matcher;

        matcher.match(book, incoming_buy);

        assert(
            book.ask_level_count() == 1);

        assert(
            book.best_ask_level().total_quantity() == 6);

        assert(
            resting_sell->remaining_quantity() == 6);
    }

    void test_empty_opposite_book_does_not_match()
    {
        OrderBook book("BTC-USD");

        auto incoming_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        MatchingEngine matcher;

        MatchResult result =
            matcher.match(book, incoming_buy);

        assert(!result.matched);
        assert(result.trades.empty());

        assert(
            incoming_buy->remaining_quantity() == 10);
    }

    void test_symbol_mismatch_is_rejected()
    {
        OrderBook book("BTC-USD");

        auto order =
            std::make_shared<Order>(
                "B1",
                "ETH-USD",
                Side::BUY,
                OrderType::LIMIT,
                100.0,
                10,
                1,
                TimeInForce::GTC);

        MatchingEngine matcher;

        bool threw = false;

        try
        {
            matcher.match(book, order);
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
    test_buy_matches_best_ask();
    test_sell_matches_best_bid();
    test_non_crossing_buy_does_not_match();
    test_non_crossing_sell_does_not_match();
    test_exact_price_match();
    test_trade_quantity_is_minimum();
    test_trade_uses_resting_order_price();
    test_fully_filled_resting_order_removed();
    test_price_level_quantity_updates_after_match();
    test_empty_opposite_book_does_not_match();
    test_symbol_mismatch_is_rejected();

    std::cout
        << "All MatchingEngine Step 1.5 tests passed (11/11)"
        << std::endl;

    return 0;
}