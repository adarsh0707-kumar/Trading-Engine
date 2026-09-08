#include "matching/MatchingEngine.hpp"

#include <cassert>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <algorithm>

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
        MatchResult result = matcher.match(book, incoming_buy);

        assert(result.matched);
        assert(result.trades.size() == 1);
        assert(result.trades.front()->price() == 100.0);
        assert(result.trades.front()->quantity() == 10);

        assert(incoming_buy->remaining_quantity() == 0);
        assert(resting_sell->remaining_quantity() == 0);
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
        MatchResult result = matcher.match(book, incoming_sell);

        assert(result.matched);
        assert(result.trades.size() == 1);
        assert(result.trades.front()->price() == 100.0);
        assert(result.trades.front()->quantity() == 10);

        assert(incoming_sell->remaining_quantity() == 0);
        assert(resting_buy->remaining_quantity() == 0);
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
        MatchResult result = matcher.match(book, incoming_buy);

        assert(!result.matched);
        assert(result.trades.empty());

        assert(incoming_buy->remaining_quantity() == 10);
        assert(resting_sell->remaining_quantity() == 10);
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
        MatchResult result = matcher.match(book, incoming_sell);

        assert(!result.matched);
        assert(result.trades.empty());

        assert(incoming_sell->remaining_quantity() == 10);
        assert(resting_buy->remaining_quantity() == 10);
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
        MatchResult result = matcher.match(book, incoming_buy);

        assert(result.matched);
        assert(result.trades.size() == 1);
        assert(result.trades.front()->price() == 100.0);
        assert(result.trades.front()->quantity() == 10);
    }

    void test_partial_fill_buy_against_larger_ask()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 4, 2);

        book.add_order(resting_sell);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_buy);

        assert(result.matched);
        assert(result.trades.size() == 1);

        assert(result.trades.front()->price() == 100.0);
        assert(result.trades.front()->quantity() == 4);

        assert(incoming_buy->remaining_quantity() == 0);
        assert(incoming_buy->is_fully_filled());

        assert(resting_sell->remaining_quantity() == 6);
        assert(!resting_sell->is_fully_filled());

        assert(book.ask_level_count() == 1);
        assert(book.order_count() == 1);

        assert(book.best_ask_level().total_quantity() == 6);
        assert(book.best_ask_level().front() == resting_sell);
    }

    void test_partial_fill_sell_against_larger_bid()
    {
        OrderBook book("BTC-USD");

        auto resting_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        auto incoming_sell =
            make_order("S1", Side::SELL, 99.0, 4, 2);

        book.add_order(resting_buy);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_sell);

        assert(result.matched);
        assert(result.trades.size() == 1);

        assert(result.trades.front()->price() == 100.0);
        assert(result.trades.front()->quantity() == 4);

        assert(incoming_sell->remaining_quantity() == 0);
        assert(incoming_sell->is_fully_filled());

        assert(resting_buy->remaining_quantity() == 6);
        assert(!resting_buy->is_fully_filled());

        assert(book.bid_level_count() == 1);
        assert(book.order_count() == 1);

        assert(book.best_bid_level().total_quantity() == 6);
        assert(book.best_bid_level().front() == resting_buy);
    }

    void test_partial_fill_preserves_fifo()
    {
        OrderBook book("BTC-USD");

        auto first =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto second =
            make_order("S2", Side::SELL, 100.0, 20, 2);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 4, 3);

        book.add_order(first);
        book.add_order(second);

        assert(book.order_count() == 2);
        assert(book.best_ask_level().total_quantity() == 30);
        assert(book.best_ask_level().front() == first);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_buy);

        assert(result.matched);
        assert(result.trades.size() == 1);
        assert(result.trades.front()->quantity() == 4);

        assert(first->remaining_quantity() == 6);
        assert(second->remaining_quantity() == 20);

        assert(book.order_count() == 2);
        assert(book.ask_level_count() == 1);

        assert(book.best_ask_level().total_quantity() == 26);
        assert(book.best_ask_level().front() == first);
    }

    void test_partial_fill_does_not_remove_price_level()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 100, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 25, 2);

        book.add_order(resting_sell);

        MatchingEngine matcher;
        matcher.match(book, incoming_buy);

        assert(book.ask_level_count() == 1);
        assert(book.order_count() == 1);

        assert(book.best_ask() == 100.0);
        assert(book.best_ask_level().total_quantity() == 75);

        assert(resting_sell->remaining_quantity() == 75);
        assert(book.best_ask_level().front() == resting_sell);
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
        assert(book.order_count() == 1);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_buy);

        assert(result.matched);

        assert(resting_sell->remaining_quantity() == 0);
        assert(resting_sell->is_fully_filled());

        assert(book.ask_level_count() == 0);
        assert(book.order_count() == 0);
    }

    void test_fully_filled_resting_bid_removed()
    {
        OrderBook book("BTC-USD");

        auto resting_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        auto incoming_sell =
            make_order("S1", Side::SELL, 99.0, 10, 2);

        book.add_order(resting_buy);

        assert(book.bid_level_count() == 1);
        assert(book.order_count() == 1);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_sell);

        assert(result.matched);

        assert(resting_buy->remaining_quantity() == 0);
        assert(resting_buy->is_fully_filled());

        assert(book.bid_level_count() == 0);
        assert(book.order_count() == 0);
    }

    void test_empty_opposite_book_does_not_match()
    {
        OrderBook book("BTC-USD");

        auto incoming_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_buy);

        assert(!result.matched);
        assert(result.trades.empty());

        assert(incoming_buy->remaining_quantity() == 10);
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
}


void test_buy_matches_multiple_ask_levels()
{
    OrderBook book("BTC-USD");

    auto ask_100 =
        make_order("S1", Side::SELL, 100.0, 30, 1);

    auto ask_101 =
        make_order("S2", Side::SELL, 101.0, 40, 2);

    auto ask_102 =
        make_order("S3", Side::SELL, 102.0, 50, 3);

    auto incoming_buy =
        make_order("B1", Side::BUY, 102.0, 100, 4);

    book.add_order(ask_100);
    book.add_order(ask_101);
    book.add_order(ask_102);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    assert(result.matched);
    assert(result.trades.size() == 3);

    assert(result.trades[0]->price() == 100.0);
    assert(result.trades[0]->quantity() == 30);

    assert(result.trades[1]->price() == 101.0);
    assert(result.trades[1]->quantity() == 40);

    assert(result.trades[2]->price() == 102.0);
    assert(result.trades[2]->quantity() == 30);

    assert(incoming_buy->remaining_quantity() == 0);
    assert(incoming_buy->is_fully_filled());

    assert(ask_100->remaining_quantity() == 0);
    assert(ask_101->remaining_quantity() == 0);
    assert(ask_102->remaining_quantity() == 20);

    assert(book.ask_level_count() == 1);
    assert(book.order_count() == 1);
    assert(book.best_ask() == 102.0);
    assert(book.best_ask_level().total_quantity() == 20);
    assert(book.best_ask_level().front() == ask_102);
}

void test_sell_matches_multiple_bid_levels()
{
    OrderBook book("BTC-USD");

    auto bid_102 =
        make_order("B1", Side::BUY, 102.0, 30, 1);

    auto bid_101 =
        make_order("B2", Side::BUY, 101.0, 40, 2);

    auto bid_100 =
        make_order("B3", Side::BUY, 100.0, 50, 3);

    auto incoming_sell =
        make_order("S1", Side::SELL, 100.0, 100, 4);

    book.add_order(bid_102);
    book.add_order(bid_101);
    book.add_order(bid_100);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_sell);

    assert(result.matched);
    assert(result.trades.size() == 3);

    assert(result.trades[0]->price() == 102.0);
    assert(result.trades[0]->quantity() == 30);

    assert(result.trades[1]->price() == 101.0);
    assert(result.trades[1]->quantity() == 40);

    assert(result.trades[2]->price() == 100.0);
    assert(result.trades[2]->quantity() == 30);

    assert(incoming_sell->remaining_quantity() == 0);
    assert(incoming_sell->is_fully_filled());

    assert(bid_102->remaining_quantity() == 0);
    assert(bid_101->remaining_quantity() == 0);
    assert(bid_100->remaining_quantity() == 20);

    assert(book.bid_level_count() == 1);
    assert(book.order_count() == 1);
    assert(book.best_bid() == 100.0);
    assert(book.best_bid_level().total_quantity() == 20);
    assert(book.best_bid_level().front() == bid_100);
}

void test_buy_stops_at_non_crossing_ask_level()
{
    OrderBook book("BTC-USD");

    auto ask_100 =
        make_order("S1", Side::SELL, 100.0, 20, 1);

    auto ask_101 =
        make_order("S2", Side::SELL, 101.0, 20, 2);

    auto ask_102 =
        make_order("S3", Side::SELL, 102.0, 20, 3);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 50, 4);

    book.add_order(ask_100);
    book.add_order(ask_101);
    book.add_order(ask_102);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    assert(result.matched);
    assert(result.trades.size() == 2);

    assert(result.trades[0]->price() == 100.0);
    assert(result.trades[0]->quantity() == 20);

    assert(result.trades[1]->price() == 101.0);
    assert(result.trades[1]->quantity() == 20);

    // Incoming order has 10 remaining and cannot cross 102.
    assert(incoming_buy->remaining_quantity() == 10);
    assert(incoming_buy->status() ==
           engine::OrderStatus::PARTIALLY_FILLED);

    // S1 and S2 were completely filled.
    assert(ask_100->remaining_quantity() == 0);
    assert(ask_101->remaining_quantity() == 0);

    // S3 remains because 101 cannot cross 102.
    assert(ask_102->remaining_quantity() == 20);

    // Incoming BUY is automatically rested.
    assert(book.order_count() == 2);
    assert(book.bid_level_count() == 1);
    assert(book.ask_level_count() == 1);

    assert(book.best_bid() == 101.0);
    assert(book.best_ask() == 102.0);

    assert(book.best_bid_level().order_count() == 1);
    assert(book.best_bid_level().total_quantity() == 10);
    assert(book.best_bid_level().front() == incoming_buy);

    assert(book.best_ask_level().order_count() == 1);
    assert(book.best_ask_level().total_quantity() == 20);
    assert(book.best_ask_level().front() == ask_102);
}

void test_sell_stops_at_non_crossing_bid_level()
{
    OrderBook book("BTC-USD");

    auto bid_102 =
        make_order("B1", Side::BUY, 102.0, 20, 1);

    auto bid_101 =
        make_order("B2", Side::BUY, 101.0, 20, 2);

    auto bid_100 =
        make_order("B3", Side::BUY, 100.0, 20, 3);

    auto incoming_sell =
        make_order("S1", Side::SELL, 101.0, 50, 4);

    book.add_order(bid_102);
    book.add_order(bid_101);
    book.add_order(bid_100);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_sell);

    assert(result.matched);
    assert(result.trades.size() == 2);

    assert(result.trades[0]->price() == 102.0);
    assert(result.trades[0]->quantity() == 20);

    assert(result.trades[1]->price() == 101.0);
    assert(result.trades[1]->quantity() == 20);

    assert(incoming_sell->remaining_quantity() == 10);

    assert(bid_102->remaining_quantity() == 0);
    assert(bid_101->remaining_quantity() == 0);
    assert(bid_100->remaining_quantity() == 20);

    assert(book.bid_level_count() == 1);
    assert(book.order_count() == 2);
    assert(book.best_bid() == 100.0);
    assert(book.best_bid_level().front() == bid_100);
}

void test_buy_preserves_fifo_across_multiple_orders()
{
    OrderBook book("BTC-USD");

    auto first =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    auto second =
        make_order("S2", Side::SELL, 100.0, 20, 2);

    auto third =
        make_order("S3", Side::SELL, 101.0, 30, 3);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 35, 4);

    book.add_order(first);
    book.add_order(second);
    book.add_order(third);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    assert(result.matched);
    assert(result.trades.size() == 3);

    assert(result.trades[0]->maker_order_id() == "S1");
    assert(result.trades[0]->quantity() == 10);
    assert(result.trades[0]->price() == 100.0);

    assert(result.trades[1]->maker_order_id() == "S2");
    assert(result.trades[1]->quantity() == 20);
    assert(result.trades[1]->price() == 100.0);

    assert(result.trades[2]->maker_order_id() == "S3");
    assert(result.trades[2]->quantity() == 5);
    assert(result.trades[2]->price() == 101.0);

    assert(incoming_buy->remaining_quantity() == 0);

    assert(first->remaining_quantity() == 0);
    assert(second->remaining_quantity() == 0);
    assert(third->remaining_quantity() == 25);

    assert(book.ask_level_count() == 1);
    assert(book.order_count() == 1);
    assert(book.best_ask() == 101.0);
    assert(book.best_ask_level().front() == third);
}

void test_unmatched_buy_is_automatically_rested()
{
    OrderBook book("BTC-USD");

    auto incoming_buy =
        make_order("B1", Side::BUY, 100.0, 10, 1);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    assert(!result.matched);
    assert(result.trades.empty());

    assert(incoming_buy->remaining_quantity() == 10);
    assert(incoming_buy->status() == engine::OrderStatus::NEW);

    assert(book.order_count() == 1);
    assert(book.bid_level_count() == 1);
    assert(book.best_bid() == 100.0);
    assert(book.best_bid_level().total_quantity() == 10);
    assert(book.best_bid_level().front() == incoming_buy);
}

void test_unmatched_sell_is_automatically_rested()
{
    OrderBook book("BTC-USD");

    auto incoming_sell =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_sell);

    assert(!result.matched);
    assert(result.trades.empty());

    assert(incoming_sell->remaining_quantity() == 10);
    assert(incoming_sell->status() == engine::OrderStatus::NEW);

    assert(book.order_count() == 1);
    assert(book.ask_level_count() == 1);
    assert(book.best_ask() == 100.0);
    assert(book.best_ask_level().total_quantity() == 10);
    assert(book.best_ask_level().front() == incoming_sell);
}

void test_partially_filled_buy_is_automatically_rested()
{
    OrderBook book("BTC-USD");

    auto resting_sell =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 20, 2);

    book.add_order(resting_sell);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    assert(result.matched);
    assert(result.trades.size() == 1);

    assert(result.trades.front()->quantity() == 10);
    assert(result.trades.front()->price() == 100.0);

    assert(incoming_buy->remaining_quantity() == 10);
    assert(
        incoming_buy->status() ==
        engine::OrderStatus::PARTIALLY_FILLED);

    assert(book.order_count() == 1);
    assert(book.ask_level_count() == 0);

    assert(book.bid_level_count() == 1);
    assert(book.best_bid() == 101.0);
    assert(book.best_bid_level().total_quantity() == 10);
    assert(book.best_bid_level().front() == incoming_buy);
}

void test_partially_filled_sell_is_automatically_rested()
{
    OrderBook book("BTC-USD");

    auto resting_buy =
        make_order("B1", Side::BUY, 100.0, 10, 1);

    auto incoming_sell =
        make_order("S1", Side::SELL, 99.0, 20, 2);

    book.add_order(resting_buy);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_sell);

    assert(result.matched);
    assert(result.trades.size() == 1);

    assert(result.trades.front()->quantity() == 10);
    assert(result.trades.front()->price() == 100.0);

    assert(incoming_sell->remaining_quantity() == 10);
    assert(
        incoming_sell->status() ==
        engine::OrderStatus::PARTIALLY_FILLED);

    assert(book.order_count() == 1);
    assert(book.bid_level_count() == 0);

    assert(book.ask_level_count() == 1);
    assert(book.best_ask() == 99.0);
    assert(book.best_ask_level().total_quantity() == 10);
    assert(book.best_ask_level().front() == incoming_sell);
}

void test_fully_filled_incoming_order_is_not_rested()
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

    assert(incoming_buy->remaining_quantity() == 0);
    assert(incoming_buy->is_fully_filled());
    assert(
        incoming_buy->status() ==
        engine::OrderStatus::FILLED);

    assert(book.order_count() == 0);
    assert(book.bid_level_count() == 0);
    assert(book.ask_level_count() == 0);
}

void test_rested_order_preserves_fifo()
{
    OrderBook book("BTC-USD");

    auto existing_bid =
        make_order("B1", Side::BUY, 101.0, 10, 1);

    auto resting_sell =
        make_order("S1", Side::SELL, 100.0, 5, 2);

    auto incoming_buy =
        make_order("B2", Side::BUY, 101.0, 10, 3);

    book.add_order(existing_bid);
    book.add_order(resting_sell);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    assert(result.matched);
    assert(result.trades.size() == 1);

    assert(result.trades.front()->maker_order_id() == "S1");
    assert(result.trades.front()->quantity() == 5);
    assert(result.trades.front()->price() == 100.0);

    assert(incoming_buy->remaining_quantity() == 5);
    assert(incoming_buy->status() ==
           engine::OrderStatus::PARTIALLY_FILLED);

    // Incoming BUY is automatically rested at 101.
    assert(book.bid_level_count() == 1);
    assert(book.best_bid() == 101.0);

    // Existing B1 must remain ahead of newly rested B2.
    assert(book.best_bid_level().order_count() == 2);
    assert(book.best_bid_level().total_quantity() == 15);

    assert(book.best_bid_level().front() == existing_bid);
}
void test_partially_filled_order_rests_after_existing_orders()
{
    OrderBook book("BTC-USD");

    auto resting_sell =
        make_order("S1", Side::SELL, 100.0, 5, 1);

    auto existing_bid =
        make_order("B1", Side::BUY, 99.0, 10, 2);

    auto incoming_buy =
        make_order("B2", Side::BUY, 100.0, 10, 3);

    book.add_order(resting_sell);
    book.add_order(existing_bid);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    assert(result.matched);
    assert(result.trades.size() == 1);

    assert(result.trades.front()->quantity() == 5);

    assert(incoming_buy->remaining_quantity() == 5);
    assert(
        incoming_buy->status() ==
        engine::OrderStatus::PARTIALLY_FILLED);

    /*
     * Incoming order rests at 100, which is a better price
     * than the existing 99 bid, so it becomes the best bid.
     */
    assert(book.bid_level_count() == 2);
    assert(book.order_count() == 2);

    assert(book.best_bid() == 100.0);
    assert(book.best_bid_level().front() == incoming_buy);
    assert(book.best_bid_level().total_quantity() == 5);
}

int main()
{
    test_buy_matches_best_ask();
    test_sell_matches_best_bid();

    test_non_crossing_buy_does_not_match();
    test_non_crossing_sell_does_not_match();

    test_exact_price_match();

    test_partial_fill_buy_against_larger_ask();
    test_partial_fill_sell_against_larger_bid();
    test_partial_fill_preserves_fifo();
    test_partial_fill_does_not_remove_price_level();

    test_fully_filled_resting_order_removed();
    test_fully_filled_resting_bid_removed();

    test_empty_opposite_book_does_not_match();
    test_symbol_mismatch_is_rejected();

    test_buy_matches_multiple_ask_levels();
    test_sell_matches_multiple_bid_levels();
    test_buy_stops_at_non_crossing_ask_level();
    test_sell_stops_at_non_crossing_bid_level();
    test_buy_preserves_fifo_across_multiple_orders();

    test_unmatched_buy_is_automatically_rested();
    test_unmatched_sell_is_automatically_rested();
    test_partially_filled_buy_is_automatically_rested();
    test_partially_filled_sell_is_automatically_rested();
    test_fully_filled_incoming_order_is_not_rested();
    test_rested_order_preserves_fifo();
    test_partially_filled_order_rests_after_existing_orders();

    std::cout
        << "All MatchingEngine Phase 1.12 tests passed (25/25)"
        << std::endl;

    return 0;
}