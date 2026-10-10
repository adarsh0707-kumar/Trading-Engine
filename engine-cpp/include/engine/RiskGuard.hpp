#pragma once

#include "orderbook/Order.hpp"

#include <chrono>
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
    double max_drawdown{1000.0};
    double max_daily_loss{500.0};
    double initial_equity{100000.0};
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
    void update_mark_price(
        double price,
        std::chrono::system_clock::time_point now = std::chrono::system_clock::now());
    void record_trade(const std::string &symbol, ::engine::Side taker_side,
                      std::int64_t quantity, double price);
    std::int64_t position() const noexcept;
    bool is_halted() const noexcept;
    const std::string &halt_reason() const noexcept;
    double equity() const noexcept;
    double drawdown() const noexcept;
    double daily_loss() const noexcept;

private:
    void evaluate_limits() noexcept;
    void roll_daily_window(std::chrono::system_clock::time_point now) noexcept;

    RiskGuardConfig config_;
    std::int64_t position_{0};
    double average_entry_price_{0.0};
    double realized_pnl_{0.0};
    double mark_price_{0.0};
    double peak_equity_{0.0};
    double day_start_equity_{0.0};
    std::int64_t utc_day_{-1};
    bool halted_{false};
    std::string halt_reason_;
};

} // namespace engine_runtime
} // namespace trading
