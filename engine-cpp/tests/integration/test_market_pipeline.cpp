#include "market/MockMarketGenerator.hpp"
#include "matching/MatchingEngine.hpp"
#include "orderbook/Order.hpp"
#include "orderbook/OrderBook.hpp"
#include "orderbook/Trade.hpp"

#include <cassert>
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

        assert(tick.sequence == 1);
        assert(tick.order_id == "SIM-00000001");
        assert(tick.symbol == "SIM");
        assert(tick.price == 100.0);
        assert(tick.quantity == 10);
        assert(tick.is_valid());

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

        assert(resting_order->is_valid());

        order_book.add_order(resting_order);

        assert(order_book.order_count() == 1);

        auto incoming_order = order_from_tick(tick);

        assert(incoming_order->is_valid());
        assert(incoming_order->status() == engine::OrderStatus::NEW);
        assert(incoming_order->remaining_quantity() == 10);

        engine::MatchingEngine matching_engine;

        const engine::MatchResult result =
            matching_engine.match(
                order_book,
                incoming_order);

        assert(result.matched);
        assert(result.trades.size() == 1);

        const auto &trade = result.trades.front();

        assert(trade);
        assert(trade->symbol() == "SIM");
        assert(trade->taker_order_id() == tick.order_id);
        assert(trade->maker_order_id() == "RESTING-1");
        assert(std::abs(trade->price() - 100.0) < 1e-9);
        assert(trade->quantity() == 10);

        assert(
            incoming_order->status() ==
            engine::OrderStatus::FILLED);

        assert(incoming_order->remaining_quantity() == 0);

        assert(
            resting_order->status() ==
            engine::OrderStatus::FILLED);

        assert(order_book.empty());
        assert(order_book.order_count() == 0);
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

        assert(first.sequence == replay_first.sequence);
        assert(first.order_id == replay_first.order_id);
        assert(first.symbol == replay_first.symbol);
        assert(first.side == replay_first.side);
        assert(first.order_type == replay_first.order_type);
        assert(first.price == replay_first.price);
        assert(first.quantity == replay_first.quantity);
        assert(first.time_in_force == replay_first.time_in_force);

        assert(second.sequence == replay_second.sequence);
        assert(second.order_id == replay_second.order_id);
        assert(second.symbol == replay_second.symbol);
        assert(second.side == replay_second.side);
        assert(second.order_type == replay_second.order_type);
        assert(second.price == replay_second.price);
        assert(second.quantity == replay_second.quantity);
        assert(second.time_in_force == replay_second.time_in_force);
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

        assert(tick.is_valid());

        auto order = order_from_tick(tick);

        assert(order->is_valid());
        assert(order->status() == engine::OrderStatus::NEW);

        engine::OrderBook order_book("SIM");

        order_book.add_order(order);

        assert(order_book.order_count() == 1);

        if (tick.side == engine::Side::BUY)
        {
            assert(order_book.bid_level_count() == 1);
            assert(
                std::abs(order_book.best_bid() - 101.0) <
                1e-9);
        }
        else
        {
            assert(order_book.ask_level_count() == 1);
            assert(
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