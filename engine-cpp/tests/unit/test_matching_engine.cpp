#include "matching/MatchingEngine.hpp"

#include "../TestCheck.hpp"

#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
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

        CHECK(result.matched);
        CHECK(result.trades.size() == 1);
        CHECK(result.trades.front()->price() == 100.0);
        CHECK(result.trades.front()->quantity() == 10);

        CHECK(incoming_buy->remaining_quantity() == 0);
        CHECK(resting_sell->remaining_quantity() == 0);
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

        CHECK(result.matched);
        CHECK(result.trades.size() == 1);
        CHECK(result.trades.front()->price() == 100.0);
        CHECK(result.trades.front()->quantity() == 10);

        CHECK(incoming_sell->remaining_quantity() == 0);
        CHECK(resting_buy->remaining_quantity() == 0);
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

        CHECK(!result.matched);
        CHECK(result.trades.empty());

        CHECK(incoming_buy->remaining_quantity() == 10);
        CHECK(resting_sell->remaining_quantity() == 10);
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

        CHECK(!result.matched);
        CHECK(result.trades.empty());

        CHECK(incoming_sell->remaining_quantity() == 10);
        CHECK(resting_buy->remaining_quantity() == 10);
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

        CHECK(result.matched);
        CHECK(result.trades.size() == 1);
        CHECK(result.trades.front()->price() == 100.0);
        CHECK(result.trades.front()->quantity() == 10);
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

        CHECK(result.matched);
        CHECK(result.trades.size() == 1);

        CHECK(result.trades.front()->price() == 100.0);
        CHECK(result.trades.front()->quantity() == 4);

        CHECK(incoming_buy->remaining_quantity() == 0);
        CHECK(incoming_buy->is_fully_filled());

        CHECK(resting_sell->remaining_quantity() == 6);
        CHECK(!resting_sell->is_fully_filled());

        CHECK(book.ask_level_count() == 1);
        CHECK(book.order_count() == 1);

        CHECK(book.best_ask_level().total_quantity() == 6);
        CHECK(book.best_ask_level().front() == resting_sell);
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

        CHECK(result.matched);
        CHECK(result.trades.size() == 1);

        CHECK(result.trades.front()->price() == 100.0);
        CHECK(result.trades.front()->quantity() == 4);

        CHECK(incoming_sell->remaining_quantity() == 0);
        CHECK(incoming_sell->is_fully_filled());

        CHECK(resting_buy->remaining_quantity() == 6);
        CHECK(!resting_buy->is_fully_filled());

        CHECK(book.bid_level_count() == 1);
        CHECK(book.order_count() == 1);

        CHECK(book.best_bid_level().total_quantity() == 6);
        CHECK(book.best_bid_level().front() == resting_buy);
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

        CHECK(book.order_count() == 2);
        CHECK(book.best_ask_level().total_quantity() == 30);
        CHECK(book.best_ask_level().front() == first);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_buy);

        CHECK(result.matched);
        CHECK(result.trades.size() == 1);
        CHECK(result.trades.front()->quantity() == 4);

        CHECK(first->remaining_quantity() == 6);
        CHECK(second->remaining_quantity() == 20);

        CHECK(book.order_count() == 2);
        CHECK(book.ask_level_count() == 1);

        CHECK(book.best_ask_level().total_quantity() == 26);
        CHECK(book.best_ask_level().front() == first);
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

        CHECK(book.ask_level_count() == 1);
        CHECK(book.order_count() == 1);

        CHECK(book.best_ask() == 100.0);
        CHECK(book.best_ask_level().total_quantity() == 75);

        CHECK(resting_sell->remaining_quantity() == 75);
        CHECK(book.best_ask_level().front() == resting_sell);
    }

    void test_fully_filled_resting_order_removed()
    {
        OrderBook book("BTC-USD");

        auto resting_sell =
            make_order("S1", Side::SELL, 100.0, 10, 1);

        auto incoming_buy =
            make_order("B1", Side::BUY, 101.0, 10, 2);

        book.add_order(resting_sell);

        CHECK(book.ask_level_count() == 1);
        CHECK(book.order_count() == 1);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_buy);

        CHECK(result.matched);

        CHECK(resting_sell->remaining_quantity() == 0);
        CHECK(resting_sell->is_fully_filled());

        CHECK(book.ask_level_count() == 0);
        CHECK(book.order_count() == 0);
    }

    void test_fully_filled_resting_bid_removed()
    {
        OrderBook book("BTC-USD");

        auto resting_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        auto incoming_sell =
            make_order("S1", Side::SELL, 99.0, 10, 2);

        book.add_order(resting_buy);

        CHECK(book.bid_level_count() == 1);
        CHECK(book.order_count() == 1);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_sell);

        CHECK(result.matched);

        CHECK(resting_buy->remaining_quantity() == 0);
        CHECK(resting_buy->is_fully_filled());

        CHECK(book.bid_level_count() == 0);
        CHECK(book.order_count() == 0);
    }

    void test_empty_opposite_book_does_not_match()
    {
        OrderBook book("BTC-USD");

        auto incoming_buy =
            make_order("B1", Side::BUY, 100.0, 10, 1);

        MatchingEngine matcher;
        MatchResult result = matcher.match(book, incoming_buy);

        CHECK(!result.matched);
        CHECK(result.trades.empty());

        CHECK(incoming_buy->remaining_quantity() == 10);
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

        CHECK(threw);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 3);

    CHECK(result.trades[0]->price() == 100.0);
    CHECK(result.trades[0]->quantity() == 30);

    CHECK(result.trades[1]->price() == 101.0);
    CHECK(result.trades[1]->quantity() == 40);

    CHECK(result.trades[2]->price() == 102.0);
    CHECK(result.trades[2]->quantity() == 30);

    CHECK(incoming_buy->remaining_quantity() == 0);
    CHECK(incoming_buy->is_fully_filled());

    CHECK(ask_100->remaining_quantity() == 0);
    CHECK(ask_101->remaining_quantity() == 0);
    CHECK(ask_102->remaining_quantity() == 20);

    CHECK(book.ask_level_count() == 1);
    CHECK(book.order_count() == 1);
    CHECK(book.best_ask() == 102.0);
    CHECK(book.best_ask_level().total_quantity() == 20);
    CHECK(book.best_ask_level().front() == ask_102);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 3);

    CHECK(result.trades[0]->price() == 102.0);
    CHECK(result.trades[0]->quantity() == 30);

    CHECK(result.trades[1]->price() == 101.0);
    CHECK(result.trades[1]->quantity() == 40);

    CHECK(result.trades[2]->price() == 100.0);
    CHECK(result.trades[2]->quantity() == 30);

    CHECK(incoming_sell->remaining_quantity() == 0);
    CHECK(incoming_sell->is_fully_filled());

    CHECK(bid_102->remaining_quantity() == 0);
    CHECK(bid_101->remaining_quantity() == 0);
    CHECK(bid_100->remaining_quantity() == 20);

    CHECK(book.bid_level_count() == 1);
    CHECK(book.order_count() == 1);
    CHECK(book.best_bid() == 100.0);
    CHECK(book.best_bid_level().total_quantity() == 20);
    CHECK(book.best_bid_level().front() == bid_100);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 2);

    CHECK(result.trades[0]->price() == 100.0);
    CHECK(result.trades[0]->quantity() == 20);

    CHECK(result.trades[1]->price() == 101.0);
    CHECK(result.trades[1]->quantity() == 20);

    // Incoming order has 10 remaining and cannot cross 102.
    CHECK(incoming_buy->remaining_quantity() == 10);
    CHECK(incoming_buy->status() ==
           engine::OrderStatus::PARTIALLY_FILLED);

    // S1 and S2 were completely filled.
    CHECK(ask_100->remaining_quantity() == 0);
    CHECK(ask_101->remaining_quantity() == 0);

    // S3 remains because 101 cannot cross 102.
    CHECK(ask_102->remaining_quantity() == 20);

    // Incoming BUY is automatically rested.
    CHECK(book.order_count() == 2);
    CHECK(book.bid_level_count() == 1);
    CHECK(book.ask_level_count() == 1);

    CHECK(book.best_bid() == 101.0);
    CHECK(book.best_ask() == 102.0);

    CHECK(book.best_bid_level().order_count() == 1);
    CHECK(book.best_bid_level().total_quantity() == 10);
    CHECK(book.best_bid_level().front() == incoming_buy);

    CHECK(book.best_ask_level().order_count() == 1);
    CHECK(book.best_ask_level().total_quantity() == 20);
    CHECK(book.best_ask_level().front() == ask_102);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 2);

    CHECK(result.trades[0]->price() == 102.0);
    CHECK(result.trades[0]->quantity() == 20);

    CHECK(result.trades[1]->price() == 101.0);
    CHECK(result.trades[1]->quantity() == 20);

    CHECK(incoming_sell->remaining_quantity() == 10);

    CHECK(bid_102->remaining_quantity() == 0);
    CHECK(bid_101->remaining_quantity() == 0);
    CHECK(bid_100->remaining_quantity() == 20);

    CHECK(book.bid_level_count() == 1);
    CHECK(book.order_count() == 2);
    CHECK(book.best_bid() == 100.0);
    CHECK(book.best_bid_level().front() == bid_100);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 3);

    CHECK(result.trades[0]->maker_order_id() == "S1");
    CHECK(result.trades[0]->quantity() == 10);
    CHECK(result.trades[0]->price() == 100.0);

    CHECK(result.trades[1]->maker_order_id() == "S2");
    CHECK(result.trades[1]->quantity() == 20);
    CHECK(result.trades[1]->price() == 100.0);

    CHECK(result.trades[2]->maker_order_id() == "S3");
    CHECK(result.trades[2]->quantity() == 5);
    CHECK(result.trades[2]->price() == 101.0);

    CHECK(incoming_buy->remaining_quantity() == 0);

    CHECK(first->remaining_quantity() == 0);
    CHECK(second->remaining_quantity() == 0);
    CHECK(third->remaining_quantity() == 25);

    CHECK(book.ask_level_count() == 1);
    CHECK(book.order_count() == 1);
    CHECK(book.best_ask() == 101.0);
    CHECK(book.best_ask_level().front() == third);
}

void test_unmatched_buy_is_automatically_rested()
{
    OrderBook book("BTC-USD");

    auto incoming_buy =
        make_order("B1", Side::BUY, 100.0, 10, 1);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    CHECK(!result.matched);
    CHECK(result.trades.empty());

    CHECK(incoming_buy->remaining_quantity() == 10);
    CHECK(incoming_buy->status() == engine::OrderStatus::NEW);

    CHECK(book.order_count() == 1);
    CHECK(book.bid_level_count() == 1);
    CHECK(book.best_bid() == 100.0);
    CHECK(book.best_bid_level().total_quantity() == 10);
    CHECK(book.best_bid_level().front() == incoming_buy);
}

void test_unmatched_sell_is_automatically_rested()
{
    OrderBook book("BTC-USD");

    auto incoming_sell =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_sell);

    CHECK(!result.matched);
    CHECK(result.trades.empty());

    CHECK(incoming_sell->remaining_quantity() == 10);
    CHECK(incoming_sell->status() == engine::OrderStatus::NEW);

    CHECK(book.order_count() == 1);
    CHECK(book.ask_level_count() == 1);
    CHECK(book.best_ask() == 100.0);
    CHECK(book.best_ask_level().total_quantity() == 10);
    CHECK(book.best_ask_level().front() == incoming_sell);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 1);

    CHECK(result.trades.front()->quantity() == 10);
    CHECK(result.trades.front()->price() == 100.0);

    CHECK(incoming_buy->remaining_quantity() == 10);
    CHECK(
        incoming_buy->status() ==
        engine::OrderStatus::PARTIALLY_FILLED);

    CHECK(book.order_count() == 1);
    CHECK(book.ask_level_count() == 0);

    CHECK(book.bid_level_count() == 1);
    CHECK(book.best_bid() == 101.0);
    CHECK(book.best_bid_level().total_quantity() == 10);
    CHECK(book.best_bid_level().front() == incoming_buy);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 1);

    CHECK(result.trades.front()->quantity() == 10);
    CHECK(result.trades.front()->price() == 100.0);

    CHECK(incoming_sell->remaining_quantity() == 10);
    CHECK(
        incoming_sell->status() ==
        engine::OrderStatus::PARTIALLY_FILLED);

    CHECK(book.order_count() == 1);
    CHECK(book.bid_level_count() == 0);

    CHECK(book.ask_level_count() == 1);
    CHECK(book.best_ask() == 99.0);
    CHECK(book.best_ask_level().total_quantity() == 10);
    CHECK(book.best_ask_level().front() == incoming_sell);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 1);

    CHECK(incoming_buy->remaining_quantity() == 0);
    CHECK(incoming_buy->is_fully_filled());
    CHECK(
        incoming_buy->status() ==
        engine::OrderStatus::FILLED);

    CHECK(book.order_count() == 0);
    CHECK(book.bid_level_count() == 0);
    CHECK(book.ask_level_count() == 0);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 1);

    CHECK(result.trades.front()->maker_order_id() == "S1");
    CHECK(result.trades.front()->quantity() == 5);
    CHECK(result.trades.front()->price() == 100.0);

    CHECK(incoming_buy->remaining_quantity() == 5);
    CHECK(incoming_buy->status() ==
           engine::OrderStatus::PARTIALLY_FILLED);

    // Incoming BUY is automatically rested at 101.
    CHECK(book.bid_level_count() == 1);
    CHECK(book.best_bid() == 101.0);

    // Existing B1 must remain ahead of newly rested B2.
    CHECK(book.best_bid_level().order_count() == 2);
    CHECK(book.best_bid_level().total_quantity() == 15);

    CHECK(book.best_bid_level().front() == existing_bid);
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

    CHECK(result.matched);
    CHECK(result.trades.size() == 1);

    CHECK(result.trades.front()->quantity() == 5);

    CHECK(incoming_buy->remaining_quantity() == 5);
    CHECK(
        incoming_buy->status() ==
        engine::OrderStatus::PARTIALLY_FILLED);

    /*
     * Incoming order rests at 100, which is a better price
     * than the existing 99 bid, so it becomes the best bid.
     */
    CHECK(book.bid_level_count() == 2);
    CHECK(book.order_count() == 2);

    CHECK(book.best_bid() == 100.0);
    CHECK(book.best_bid_level().front() == incoming_buy);
    CHECK(book.best_bid_level().total_quantity() == 5);
}

void test_buy_fully_consumes_multiple_price_levels()
{
    OrderBook book("BTC-USD");

    auto ask_100 =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    auto ask_101 =
        make_order("S2", Side::SELL, 101.0, 10, 2);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 20, 3);

    book.add_order(ask_100);
    book.add_order(ask_101);

    MatchingEngine matcher;
    MatchResult result = matcher.match(book, incoming_buy);

    CHECK(result.matched);
    CHECK(result.trades.size() == 2);

    CHECK(result.trades[0]->maker_order_id() == "S1");
    CHECK(result.trades[0]->price() == 100.0);
    CHECK(result.trades[0]->quantity() == 10);

    CHECK(result.trades[1]->maker_order_id() == "S2");
    CHECK(result.trades[1]->price() == 101.0);
    CHECK(result.trades[1]->quantity() == 10);

    CHECK(incoming_buy->remaining_quantity() == 0);
    CHECK(incoming_buy->status() ==
           engine::OrderStatus::FILLED);

    CHECK(book.order_count() == 0);
    CHECK(book.ask_level_count() == 0);
}

void test_sell_fully_consumes_multiple_price_levels()
{
    OrderBook book("BTC-USD");

    auto bid_102 =
        make_order("B1", Side::BUY, 102.0, 10, 1);

    auto bid_101 =
        make_order("B2", Side::BUY, 101.0, 10, 2);

    auto incoming_sell =
        make_order("S1", Side::SELL, 101.0, 20, 3);

    book.add_order(bid_102);
    book.add_order(bid_101);

    MatchingEngine matcher;
    MatchResult result = matcher.match(book, incoming_sell);

    CHECK(result.matched);
    CHECK(result.trades.size() == 2);

    CHECK(result.trades[0]->maker_order_id() == "B1");
    CHECK(result.trades[0]->price() == 102.0);
    CHECK(result.trades[0]->quantity() == 10);

    CHECK(result.trades[1]->maker_order_id() == "B2");
    CHECK(result.trades[1]->price() == 101.0);
    CHECK(result.trades[1]->quantity() == 10);

    CHECK(incoming_sell->remaining_quantity() == 0);
    CHECK(incoming_sell->status() ==
           engine::OrderStatus::FILLED);

    CHECK(book.order_count() == 0);
    CHECK(book.bid_level_count() == 0);
}

void test_partially_filled_buy_rests_after_multiple_levels()
{
    OrderBook book("BTC-USD");

    auto ask_100 =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    auto ask_101 =
        make_order("S2", Side::SELL, 101.0, 10, 2);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 25, 3);

    book.add_order(ask_100);
    book.add_order(ask_101);

    MatchingEngine matcher;
    MatchResult result = matcher.match(book, incoming_buy);

    CHECK(result.matched);
    CHECK(result.trades.size() == 2);

    CHECK(result.trades[0]->quantity() == 10);
    CHECK(result.trades[0]->price() == 100.0);

    CHECK(result.trades[1]->quantity() == 10);
    CHECK(result.trades[1]->price() == 101.0);

    CHECK(incoming_buy->remaining_quantity() == 5);
    CHECK(incoming_buy->status() ==
           engine::OrderStatus::PARTIALLY_FILLED);

    CHECK(book.order_count() == 1);
    CHECK(book.bid_level_count() == 1);
    CHECK(book.ask_level_count() == 0);

    CHECK(book.best_bid() == 101.0);
    CHECK(book.best_bid_level().total_quantity() == 5);
    CHECK(book.best_bid_level().front() == incoming_buy);
}

void test_partially_filled_sell_rests_after_multiple_levels()
{
    OrderBook book("BTC-USD");

    auto bid_102 =
        make_order("B1", Side::BUY, 102.0, 10, 1);

    auto bid_101 =
        make_order("B2", Side::BUY, 101.0, 10, 2);

    auto incoming_sell =
        make_order("S1", Side::SELL, 101.0, 25, 3);

    book.add_order(bid_102);
    book.add_order(bid_101);

    MatchingEngine matcher;
    MatchResult result = matcher.match(book, incoming_sell);

    CHECK(result.matched);
    CHECK(result.trades.size() == 2);

    CHECK(result.trades[0]->quantity() == 10);
    CHECK(result.trades[0]->price() == 102.0);

    CHECK(result.trades[1]->quantity() == 10);
    CHECK(result.trades[1]->price() == 101.0);

    CHECK(incoming_sell->remaining_quantity() == 5);
    CHECK(incoming_sell->status() ==
           engine::OrderStatus::PARTIALLY_FILLED);

    CHECK(book.order_count() == 1);
    CHECK(book.ask_level_count() == 1);
    CHECK(book.bid_level_count() == 0);

    CHECK(book.best_ask() == 101.0);
    CHECK(book.best_ask_level().total_quantity() == 5);
    CHECK(book.best_ask_level().front() == incoming_sell);
}

void test_rested_buy_matches_on_subsequent_order()
{
    OrderBook book("BTC-USD");

    auto first_buy =
        make_order("B1", Side::BUY, 100.0, 10, 1);

    MatchingEngine matcher;

    MatchResult first_result =
        matcher.match(book, first_buy);

    CHECK(!first_result.matched);
    CHECK(book.order_count() == 1);

    auto incoming_sell =
        make_order("S1", Side::SELL, 99.0, 10, 2);

    MatchResult second_result =
        matcher.match(book, incoming_sell);

    CHECK(second_result.matched);
    CHECK(second_result.trades.size() == 1);

    CHECK(second_result.trades.front()->maker_order_id() == "B1");
    CHECK(second_result.trades.front()->price() == 100.0);
    CHECK(second_result.trades.front()->quantity() == 10);

    CHECK(first_buy->status() ==
           engine::OrderStatus::FILLED);

    CHECK(incoming_sell->status() ==
           engine::OrderStatus::FILLED);

    CHECK(book.order_count() == 0);
    CHECK(book.bid_level_count() == 0);
    CHECK(book.ask_level_count() == 0);
}

void test_rested_sell_matches_on_subsequent_order()
{
    OrderBook book("BTC-USD");

    auto first_sell =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    MatchingEngine matcher;

    MatchResult first_result =
        matcher.match(book, first_sell);

    CHECK(!first_result.matched);
    CHECK(book.order_count() == 1);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 10, 2);

    MatchResult second_result =
        matcher.match(book, incoming_buy);

    CHECK(second_result.matched);
    CHECK(second_result.trades.size() == 1);

    CHECK(second_result.trades.front()->maker_order_id() == "S1");
    CHECK(second_result.trades.front()->price() == 100.0);
    CHECK(second_result.trades.front()->quantity() == 10);

    CHECK(first_sell->status() ==
           engine::OrderStatus::FILLED);

    CHECK(incoming_buy->status() ==
           engine::OrderStatus::FILLED);

    CHECK(book.order_count() == 0);
    CHECK(book.bid_level_count() == 0);
    CHECK(book.ask_level_count() == 0);
}

void test_cancel_rested_order_after_matching()
{
    OrderBook book("BTC-USD");

    auto resting_sell =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 5, 2);

    book.add_order(resting_sell);

    MatchingEngine matcher;

    MatchResult result =
        matcher.match(book, incoming_buy);

    CHECK(result.matched);
    CHECK(incoming_buy->remaining_quantity() == 0);

    CHECK(resting_sell->remaining_quantity() == 5);
    CHECK(resting_sell->status() ==
           engine::OrderStatus::PARTIALLY_FILLED);

    CHECK(book.order_count() == 1);

    bool cancelled =
        book.cancel_order(resting_sell->order_id());

    CHECK(cancelled);

    CHECK(resting_sell->status() ==
           engine::OrderStatus::CANCELLED);

    CHECK(book.order_count() == 0);
    CHECK(book.ask_level_count() == 0);
}

void test_trade_contains_correct_maker_and_taker()
{
    OrderBook book("BTC-USD");

    auto resting_sell =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 4, 2);

    book.add_order(resting_sell);

    MatchingEngine matcher;
    MatchResult result =
        matcher.match(book, incoming_buy);

    CHECK(result.matched);
    CHECK(result.trades.size() == 1);

    const auto &trade = result.trades.front();

    CHECK(trade->maker_order_id() == "S1");
    CHECK(trade->taker_order_id() == "B1");
    CHECK(trade->price() == 100.0);
    CHECK(trade->quantity() == 4);
}

void test_book_integrity_after_multi_level_partial_match()
{
    OrderBook book("BTC-USD");

    auto ask_100 =
        make_order("S1", Side::SELL, 100.0, 10, 1);

    auto ask_101 =
        make_order("S2", Side::SELL, 101.0, 20, 2);

    auto ask_102 =
        make_order("S3", Side::SELL, 102.0, 30, 3);

    auto incoming_buy =
        make_order("B1", Side::BUY, 101.0, 35, 4);

    book.add_order(ask_100);
    book.add_order(ask_101);
    book.add_order(ask_102);

    MatchingEngine matcher;
    MatchResult result =
        matcher.match(book, incoming_buy);

    CHECK(result.matched);
    CHECK(result.trades.size() == 2);

    CHECK(incoming_buy->remaining_quantity() == 5);

    CHECK(book.order_count() == 2);
    CHECK(book.bid_level_count() == 1);
    CHECK(book.ask_level_count() == 1);

    CHECK(book.best_bid() == 101.0);
    CHECK(book.best_ask() == 102.0);

    CHECK(book.best_bid_level().order_count() == 1);
    CHECK(book.best_bid_level().total_quantity() == 5);
    CHECK(book.best_bid_level().front() == incoming_buy);

    CHECK(book.best_ask_level().order_count() == 1);
    CHECK(book.best_ask_level().total_quantity() == 30);
    CHECK(book.best_ask_level().front() == ask_102);
}

void test_trade_ids_are_unique_across_matches()
{
    MatchingEngine matcher;

    std::vector<std::string> trade_ids;

    for (int round = 0; round < 2; ++round)
    {
        OrderBook book("BTC-USD");

        book.add_order(
            make_order("S1", Side::SELL, 100.0, 4, 1));

        book.add_order(
            make_order("S2", Side::SELL, 101.0, 4, 2));

        MatchResult result =
            matcher.match(
                book,
                make_order("B1", Side::BUY, 101.0, 8, 3));

        CHECK(result.trades.size() == 2);

        for (const auto &trade : result.trades)
        {
            trade_ids.push_back(trade->trade_id());
        }
    }

    std::sort(trade_ids.begin(), trade_ids.end());

    CHECK(
        std::adjacent_find(
            trade_ids.begin(),
            trade_ids.end()) == trade_ids.end());
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
    test_buy_fully_consumes_multiple_price_levels();
    test_sell_fully_consumes_multiple_price_levels();

    test_partially_filled_buy_rests_after_multiple_levels();
    test_partially_filled_sell_rests_after_multiple_levels();

    test_rested_buy_matches_on_subsequent_order();
    test_rested_sell_matches_on_subsequent_order();

    test_cancel_rested_order_after_matching();

    test_trade_contains_correct_maker_and_taker();

    test_book_integrity_after_multi_level_partial_match();
    test_partially_filled_order_rests_after_existing_orders();

    test_trade_ids_are_unique_across_matches();

    std::cout
        << "All MatchingEngine Phase 1.13 tests passed (35/35)"
        << std::endl;

    return 0;
}