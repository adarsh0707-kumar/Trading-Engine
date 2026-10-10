#pragma once

#include "orderbook/Order.hpp"

#include <cstdint>
#include <string>

namespace trading
{
namespace engine_runtime
{

struct RiskGuardConfig
{
    std::int64_t max_position{1000};
    double max_position_value{100000.0};
};

struct RiskDecision
{
    bool allowed{false};
    std::string reason;
    std::int64_t projected_position{0};
    double projected_position_value{0.0};
};

class RiskGuard
{
public:
    explicit RiskGuard(const RiskGuardConfig &config);

    RiskDecision check_order(const ::engine::Order &order) const;
    void record_trade(const std::string &symbol, ::engine::Side taker_side,
                      std::int64_t quantity);
    std::int64_t position() const noexcept;

private:
    RiskGuardConfig config_;
    std::int64_t position_{0};
};

} // namespace engine_runtime
} // namespace trading
