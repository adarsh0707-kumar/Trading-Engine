#include "market/MockMarketGenerator.hpp"

#include <cassert>
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

    assert(tick.sequence == 1);
    assert(tick.order_id == "SIM-00000001");
    assert(tick.symbol == "SIM");
    assert(tick.is_valid());
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

        assert(a.sequence == b.sequence);
        assert(a.order_id == b.order_id);
        assert(a.symbol == b.symbol);
        assert(a.side == b.side);
        assert(a.order_type == b.order_type);
        assert(a.price == b.price);
        assert(a.quantity == b.quantity);
        assert(a.time_in_force == b.time_in_force);
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

    assert(different);
}

static void test_sequence_numbers_are_monotonic()
{
    MockMarketGenerator generator(
        MarketGeneratorConfig{42});

    for (std::uint64_t expected = 1; expected <= 100; ++expected)
    {
        Tick tick = generator.next();

        assert(tick.sequence == expected);
        assert(generator.next_sequence() == expected + 1);
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

        assert(!tick.order_id.empty());

        if (!previous_id.empty())
        {
            assert(tick.order_id != previous_id);
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

        assert(tick.price >= 100.00);
        assert(tick.price <= 101.00);

        assert(tick.quantity >= 10);
        assert(tick.quantity <= 20);

        assert(tick.is_valid());
    }
}

static void test_generate_count()
{
    MarketGeneratorConfig config;
    config.seed = 777;

    MockMarketGenerator generator(config);

    MarketData data = generator.generate(50);

    assert(data.size() == 50);
    assert(!data.empty());

    for (std::size_t i = 0; i < data.size(); ++i)
    {
        assert(data.ticks()[i].sequence == i + 1);
        assert(data.ticks()[i].is_valid());
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

    assert(first.sequence == replay_first.sequence);
    assert(first.order_id == replay_first.order_id);
    assert(first.price == replay_first.price);
    assert(first.quantity == replay_first.quantity);
    assert(first.side == replay_first.side);

    assert(second.sequence == replay_second.sequence);
    assert(second.order_id == replay_second.order_id);
    assert(second.price == replay_second.price);
    assert(second.quantity == replay_second.quantity);
    assert(second.side == replay_second.side);

    assert(third.sequence == replay_third.sequence);
    assert(third.order_id == replay_third.order_id);
    assert(third.price == replay_third.price);
    assert(third.quantity == replay_third.quantity);
    assert(third.side == replay_third.side);
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

    assert(threw);
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

    assert(threw);
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
