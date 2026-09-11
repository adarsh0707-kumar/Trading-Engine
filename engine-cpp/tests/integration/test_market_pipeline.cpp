#include "market/MockMarketGenerator.hpp"
#include "matching/MatchingEngine.hpp"
#include "orderbook/Order.hpp"
#include "orderbook/OrderBook.hpp"
#include "orderbook/Trade.hpp"

#include "../TestCheck.hpp"

#include <cmath>
#include <cstdint>
#include <iostream>
#include <memory>

namespace
{

    std::shared_ptr<engine::Order> order_from_tick(
        const engine::Tick &tick)
    {
        return std::make_shared<engine::Order>(
            tick.order_id,
            tick.symbol,
            tick.side,
            tick.order_type,
            tick.price,
            tick.quantity,
            static_cast<std::int64_t>(tick.sequence),
            tick.time_in_force);
    }

    void test_generated_tick_reaches_matching_engine()
    {
        engine::MarketGeneratorConfig config;

        config.seed = 42;
        config.symbol = "SIM";
        config.min_price = 100.0;
        config.max_price = 100.0;
        config.min_quantity = 10;
        config.max_quantity = 10;

        engine::MockMarketGenerator generator(config);

        const engine::Tick tick = generator.next();

        CHECK(tick.sequence == 1);
        CHECK(tick.order_id == "SIM-00000001");
        CHECK(tick.symbol == "SIM");
        CHECK(tick.price == 100.0);
        CHECK(tick.quantity == 10);
        CHECK(tick.is_valid());

        engine::OrderBook order_book("SIM");

        const engine::Side resting_side =
            tick.side == engine::Side::BUY
                ? engine::Side::SELL
                : engine::Side::BUY;

        auto resting_order = std::make_shared<engine::Order>(
            "RESTING-1",
            "SIM",
            resting_side,
            engine::OrderType::LIMIT,
            tick.price,
            tick.quantity,
            1,
            engine::TimeInForce::GTC);

        CHECK(resting_order->is_valid());

        order_book.add_order(resting_order);

        CHECK(order_book.order_count() == 1);

        auto incoming_order = order_from_tick(tick);

        CHECK(incoming_order->is_valid());
        CHECK(incoming_order->status() == engine::OrderStatus::NEW);
        CHECK(incoming_order->remaining_quantity() == 10);

        engine::MatchingEngine matching_engine;

        const engine::MatchResult result =
            matching_engine.match(
                order_book,
                incoming_order);

        CHECK(result.matched);
        CHECK(result.trades.size() == 1);

        const auto &trade = result.trades.front();

        CHECK(trade);
        CHECK(trade->symbol() == "SIM");
        CHECK(trade->taker_order_id() == tick.order_id);
        CHECK(trade->maker_order_id() == "RESTING-1");
        CHECK(std::abs(trade->price() - 100.0) < 1e-9);
        CHECK(trade->quantity() == 10);

        CHECK(
            incoming_order->status() ==
            engine::OrderStatus::FILLED);

        CHECK(incoming_order->remaining_quantity() == 0);

        CHECK(
            resting_order->status() ==
            engine::OrderStatus::FILLED);

        CHECK(order_book.empty());
        CHECK(order_book.order_count() == 0);
    }

    void test_deterministic_reset_replays_same_tick()
    {
        engine::MarketGeneratorConfig config;

        config.seed = 12345;
        config.symbol = "SIM";
        config.min_price = 95.0;
        config.max_price = 105.0;
        config.min_quantity = 1;
        config.max_quantity = 50;

        engine::MockMarketGenerator generator(config);

        const engine::Tick first = generator.next();
        const engine::Tick second = generator.next();

        generator.reset();

        const engine::Tick replay_first = generator.next();
        const engine::Tick replay_second = generator.next();

        CHECK(first.sequence == replay_first.sequence);
        CHECK(first.order_id == replay_first.order_id);
        CHECK(first.symbol == replay_first.symbol);
        CHECK(first.side == replay_first.side);
        CHECK(first.order_type == replay_first.order_type);
        CHECK(first.price == replay_first.price);
        CHECK(first.quantity == replay_first.quantity);
        CHECK(first.time_in_force == replay_first.time_in_force);

        CHECK(second.sequence == replay_second.sequence);
        CHECK(second.order_id == replay_second.order_id);
        CHECK(second.symbol == replay_second.symbol);
        CHECK(second.side == replay_second.side);
        CHECK(second.order_type == replay_second.order_type);
        CHECK(second.price == replay_second.price);
        CHECK(second.quantity == replay_second.quantity);
        CHECK(second.time_in_force == replay_second.time_in_force);
    }

    void test_generated_tick_can_become_resting_order()
    {
        engine::MarketGeneratorConfig config;

        config.seed = 7;
        config.symbol = "SIM";
        config.min_price = 101.0;
        config.max_price = 101.0;
        config.min_quantity = 25;
        config.max_quantity = 25;

        engine::MockMarketGenerator generator(config);

        const engine::Tick tick = generator.next();

        CHECK(tick.is_valid());

        auto order = order_from_tick(tick);

        CHECK(order->is_valid());
        CHECK(order->status() == engine::OrderStatus::NEW);

        engine::OrderBook order_book("SIM");

        order_book.add_order(order);

        CHECK(order_book.order_count() == 1);

        if (tick.side == engine::Side::BUY)
        {
            CHECK(order_book.bid_level_count() == 1);
            CHECK(
                std::abs(order_book.best_bid() - 101.0) <
                1e-9);
        }
        else
        {
            CHECK(order_book.ask_level_count() == 1);
            CHECK(
                std::abs(order_book.best_ask() - 101.0) <
                1e-9);
        }
    }

} // namespace

int main()
{
    test_generated_tick_reaches_matching_engine();
    test_deterministic_reset_replays_same_tick();
    test_generated_tick_can_become_resting_order();

    std::cout
        << "All Market Pipeline integration tests passed (3/3)"
        << std::endl;

    return 0;
}