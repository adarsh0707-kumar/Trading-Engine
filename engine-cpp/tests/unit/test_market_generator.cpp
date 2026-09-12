#include "market/MockMarketGenerator.hpp"

#include "../TestCheck.hpp"

#include <iostream>
#include <stdexcept>

using namespace engine;

static void test_first_tick_is_deterministic()
{
    MarketGeneratorConfig config;
    config.seed = 12345;
    config.symbol = "SIM";

    MockMarketGenerator generator(config);

    Tick tick = generator.next();

    CHECK(tick.sequence == 1);
    CHECK(tick.order_id == "SIM-00000001");
    CHECK(tick.symbol == "SIM");
    CHECK(tick.is_valid());
}

static void test_same_seed_produces_same_stream()
{
    MarketGeneratorConfig config;
    config.seed = 12345;
    config.symbol = "SIM";

    MockMarketGenerator first(config);
    MockMarketGenerator second(config);

    for (int i = 0; i < 100; ++i)
    {
        Tick a = first.next();
        Tick b = second.next();

        CHECK(a.sequence == b.sequence);
        CHECK(a.order_id == b.order_id);
        CHECK(a.symbol == b.symbol);
        CHECK(a.side == b.side);
        CHECK(a.order_type == b.order_type);
        CHECK(a.price == b.price);
        CHECK(a.quantity == b.quantity);
        CHECK(a.time_in_force == b.time_in_force);
    }
}

static void test_different_seed_produces_different_stream()
{
    MarketGeneratorConfig first_config;
    first_config.seed = 12345;

    MarketGeneratorConfig second_config;
    second_config.seed = 67890;

    MockMarketGenerator first(first_config);
    MockMarketGenerator second(second_config);

    bool different = false;

    for (int i = 0; i < 20; ++i)
    {
        Tick a = first.next();
        Tick b = second.next();

        if (a.side != b.side ||
            a.price != b.price ||
            a.quantity != b.quantity)
        {
            different = true;
            break;
        }
    }

    CHECK(different);
}

static void test_sequence_numbers_are_monotonic()
{
    MockMarketGenerator generator(
        MarketGeneratorConfig{42});

    for (std::uint64_t expected = 1; expected <= 100; ++expected)
    {
        Tick tick = generator.next();

        CHECK(tick.sequence == expected);
        CHECK(generator.next_sequence() == expected + 1);
    }
}

static void test_order_ids_are_unique()
{
    MockMarketGenerator generator(
        MarketGeneratorConfig{42});

    std::string previous_id;

    for (int i = 0; i < 100; ++i)
    {
        Tick tick = generator.next();

        CHECK(!tick.order_id.empty());

        if (!previous_id.empty())
        {
            CHECK(tick.order_id != previous_id);
        }

        previous_id = tick.order_id;
    }
}

static void test_generated_values_are_in_range()
{
    MarketGeneratorConfig config;
    config.seed = 99;
    config.min_price = 100.00;
    config.max_price = 101.00;
    config.min_quantity = 10;
    config.max_quantity = 20;

    MockMarketGenerator generator(config);

    for (int i = 0; i < 1000; ++i)
    {
        Tick tick = generator.next();

        CHECK(tick.price >= 100.00);
        CHECK(tick.price <= 101.00);

        CHECK(tick.quantity >= 10);
        CHECK(tick.quantity <= 20);

        CHECK(tick.is_valid());
    }
}

static void test_generate_count()
{
    MarketGeneratorConfig config;
    config.seed = 777;

    MockMarketGenerator generator(config);

    MarketData data = generator.generate(50);

    CHECK(data.size() == 50);
    CHECK(!data.empty());

    for (std::size_t i = 0; i < data.size(); ++i)
    {
        CHECK(data.ticks()[i].sequence == i + 1);
        CHECK(data.ticks()[i].is_valid());
    }
}

static void test_reset_replays_stream()
{
    MarketGeneratorConfig config;
    config.seed = 2026;

    MockMarketGenerator generator(config);

    Tick first = generator.next();
    Tick second = generator.next();
    Tick third = generator.next();

    generator.reset();

    Tick replay_first = generator.next();
    Tick replay_second = generator.next();
    Tick replay_third = generator.next();

    CHECK(first.sequence == replay_first.sequence);
    CHECK(first.order_id == replay_first.order_id);
    CHECK(first.price == replay_first.price);
    CHECK(first.quantity == replay_first.quantity);
    CHECK(first.side == replay_first.side);

    CHECK(second.sequence == replay_second.sequence);
    CHECK(second.order_id == replay_second.order_id);
    CHECK(second.price == replay_second.price);
    CHECK(second.quantity == replay_second.quantity);
    CHECK(second.side == replay_second.side);

    CHECK(third.sequence == replay_third.sequence);
    CHECK(third.order_id == replay_third.order_id);
    CHECK(third.price == replay_third.price);
    CHECK(third.quantity == replay_third.quantity);
    CHECK(third.side == replay_third.side);
}

static void test_invalid_configuration_is_rejected()
{
    MarketGeneratorConfig config;
    config.min_price = 110.0;
    config.max_price = 100.0;

    bool threw = false;

    try
    {
        MockMarketGenerator generator(config);
    }
    catch (const std::invalid_argument &)
    {
        threw = true;
    }

    CHECK(threw);
}

static void test_empty_symbol_is_rejected()
{
    MarketGeneratorConfig config;
    config.symbol = "";

    bool threw = false;

    try
    {
        MockMarketGenerator generator(config);
    }
    catch (const std::invalid_argument &)
    {
        threw = true;
    }

    CHECK(threw);
}

int main()
{
    test_first_tick_is_deterministic();
    test_same_seed_produces_same_stream();
    test_different_seed_produces_different_stream();
    test_sequence_numbers_are_monotonic();
    test_order_ids_are_unique();
    test_generated_values_are_in_range();
    test_generate_count();
    test_reset_replays_stream();
    test_invalid_configuration_is_rejected();
    test_empty_symbol_is_rejected();

    std::cout
        << "All Market Generator tests passed (10/10).\n";

    return 0;
}
