#pragma once

#include "market/MarketData.hpp"

#include <cstddef>
#include <cstdint>
#include <random>
#include <string>

namespace engine
{

struct MarketGeneratorConfig
{
    std::uint64_t seed = 1;
    std::string symbol = "SIM";
    double min_price = 90.0;
    double max_price = 110.0;
    std::int64_t min_quantity = 1;
    std::int64_t max_quantity = 100;
};

class MockMarketGenerator
{
public:
    explicit MockMarketGenerator(
        const MarketGeneratorConfig &config);

    Tick next();

    MarketData generate(std::size_t count);

    void reset();

    std::uint64_t seed() const noexcept;

    std::uint64_t next_sequence() const noexcept;

private:
    Tick generate_tick();

    MarketGeneratorConfig config_;
    std::mt19937_64 rng_;
    std::uint64_t sequence_;
};

} // namespace engine
