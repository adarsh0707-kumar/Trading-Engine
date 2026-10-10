#pragma once
#include "market/MarketData.hpp"
#include <cstdint>
#include <string>
namespace trading { namespace engine_runtime {
struct EngineConfig {
    std::string symbol{"SIM"};
    std::string bind_address{"127.0.0.1"};
    std::uint16_t port{9000};
    std::uint64_t tick_interval_ms{100};
    std::uint64_t market_seed{42};
    double min_price{95.0};
    double max_price{105.0};
    std::int64_t min_quantity{1};
    std::int64_t max_quantity{100};
    std::int64_t risk_max_position{1000};
    double risk_max_position_value{100000.0};
    double risk_max_drawdown{1000.0};
    double risk_max_daily_loss{500.0};
    double risk_initial_equity{100000.0};
    std::string risk_state_file_path{};
};
} }
