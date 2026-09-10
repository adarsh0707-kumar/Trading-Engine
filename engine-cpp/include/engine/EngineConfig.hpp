#pragma once

#include "market/MarketData.hpp"

#include <cstdint>
#include <string>

namespace trading
{
namespace engine_runtime
{

struct EngineConfig
{
    std::string symbol{"SIM"};
    std::uint16_t port{9000};
    std::uint64_t tick_interval_ms{100};
    std::uint64_t market_seed{42};
    double min_price{95.0};
    double max_price{105.0};
    std::int64_t min_quantity{1};
    std::int64_t max_quantity{100};
};

} // namespace engine_runtime
} // namespace trading
