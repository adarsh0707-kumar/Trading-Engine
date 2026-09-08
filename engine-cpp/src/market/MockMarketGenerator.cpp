#include "market/MockMarketGenerator.hpp"

#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>
#include <cmath>

namespace engine
{

MockMarketGenerator::MockMarketGenerator(
    const MarketGeneratorConfig &config)
    : config_(config),
      rng_(config.seed),
      sequence_(0)
{
    if (config_.symbol.empty())
    {
        throw std::invalid_argument(
            "market generator symbol cannot be empty");
    }

    if (!std::isfinite(config_.min_price) ||
        !std::isfinite(config_.max_price) ||
        config_.min_price <= 0.0 ||
        config_.max_price <= 0.0 ||
        config_.min_price > config_.max_price)
    {
        throw std::invalid_argument(
            "invalid market generator price range");
    }

    if (config_.min_quantity <= 0 ||
        config_.max_quantity <= 0 ||
        config_.min_quantity > config_.max_quantity)
    {
        throw std::invalid_argument(
            "invalid market generator quantity range");
    }
}

Tick MockMarketGenerator::next()
{
    return generate_tick();
}

MarketData MockMarketGenerator::generate(std::size_t count)
{
    MarketData data;

    for (std::size_t i = 0; i < count; ++i)
    {
        data.add(generate_tick());
    }

    return data;
}

void MockMarketGenerator::reset()
{
    rng_.seed(config_.seed);
    sequence_ = 0;
}

std::uint64_t MockMarketGenerator::seed() const noexcept
{
    return config_.seed;
}

std::uint64_t MockMarketGenerator::next_sequence() const noexcept
{
    return sequence_ + 1;
}

Tick MockMarketGenerator::generate_tick()
{
    ++sequence_;

    std::uniform_int_distribution<int> side_distribution(0, 1);

    std::uniform_int_distribution<std::int64_t>
        quantity_distribution(
            config_.min_quantity,
            config_.max_quantity);

    /*
     * Generate prices in cents so that the generated value has
     * deterministic two-decimal precision without repeatedly
     * constructing a floating-point distribution.
     */
    const auto min_price_cents =
        static_cast<std::int64_t>(config_.min_price * 100.0);

    const auto max_price_cents =
        static_cast<std::int64_t>(config_.max_price * 100.0);

    std::uniform_int_distribution<std::int64_t>
        price_distribution(
            min_price_cents,
            max_price_cents);

    const Side side =
        side_distribution(rng_) == 0
            ? Side::BUY
            : Side::SELL;

    const std::int64_t price_cents =
        price_distribution(rng_);

    const std::int64_t quantity =
        quantity_distribution(rng_);

    std::ostringstream order_id;
    order_id << "SIM-" << std::setw(8)
             << std::setfill('0')
             << sequence_;

    Tick tick{
        sequence_,
        order_id.str(),
        config_.symbol,
        side,
        OrderType::LIMIT,
        static_cast<double>(price_cents) / 100.0,
        quantity,
        TimeInForce::GTC};

    return tick;
}

} // namespace engine
