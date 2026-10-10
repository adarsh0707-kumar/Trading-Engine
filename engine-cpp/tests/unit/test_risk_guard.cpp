#include "engine/RiskGuard.hpp"

#include "../TestCheck.hpp"

#include <iostream>
#include <chrono>
#include <memory>
#include <stdexcept>

using trading::engine_runtime::RiskGuard;
using trading::engine_runtime::RiskGuardConfig;

namespace
{
std::shared_ptr<engine::Order> make_order(
    const char *id, engine::Side side, double price, std::int64_t quantity)
{
    return std::make_shared<engine::Order>(
        id, "SIM", side, engine::OrderType::LIMIT, price, quantity, 1);
}

void test_order_within_position_limits_is_allowed()
{
    RiskGuard guard(RiskGuardConfig{100, 10000.0});
    const auto order = make_order("B1", engine::Side::BUY, 100.0, 50);
    const auto decision = guard.check_order(*order);
    CHECK(decision.allowed);
    CHECK(decision.projected_position == 50);
    CHECK(decision.projected_position_value == 5000.0);
}

void test_order_that_would_exceed_position_is_rejected()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    guard.record_trade("SIM", engine::Side::BUY, 80, 100.0);
    const auto order = make_order("B2", engine::Side::BUY, 100.0, 21);
    const auto decision = guard.check_order(*order);
    CHECK(!decision.allowed);
    CHECK(decision.reason == "projected position exceeds max_position");
    CHECK(guard.position() == 80);
}

void test_sell_can_reduce_long_position()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    guard.record_trade("SIM", engine::Side::BUY, 80);
    const auto order = make_order("S1", engine::Side::SELL, 100.0, 30);
    const auto decision = guard.check_order(*order);
    CHECK(decision.allowed);
    CHECK(decision.projected_position == 50);
}

void test_position_value_limit_is_enforced()
{
    RiskGuard guard(RiskGuardConfig{100, 5000.0});
    const auto order = make_order("B1", engine::Side::BUY, 100.0, 51);
    const auto decision = guard.check_order(*order);
    CHECK(!decision.allowed);
    CHECK(decision.reason == "projected position value exceeds max_position_value");
}

void test_order_larger_than_position_limit_is_rejected()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    const auto order = make_order("B1", engine::Side::BUY, 100.0, 101);
    const auto decision = guard.check_order(*order);
    CHECK(!decision.allowed);
    CHECK(decision.reason == "projected position exceeds max_position");
}


void test_drawdown_halts_and_latches()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0, 100.0, 10000.0, 10000.0});
    guard.update_mark_price(100.0);
    guard.record_trade("SIM", engine::Side::BUY, 10, 100.0);
    guard.update_mark_price(89.0);

    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_drawdown");
    CHECK(guard.drawdown() >= 100.0);

    const auto rejected = guard.check_order(*make_order("B3", engine::Side::BUY, 89.0, 1));
    CHECK(!rejected.allowed);
    CHECK(rejected.reason.find("risk halt active") == 0);

    guard.update_mark_price(110.0);
    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_drawdown");
}

void test_daily_loss_halts_and_stays_latched_after_utc_rollover()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0, 10000.0, 100.0, 10000.0});
    const auto day = std::chrono::system_clock::time_point{
        std::chrono::seconds{2000000000}};
    guard.update_mark_price(100.0, day);
    guard.record_trade("SIM", engine::Side::BUY, 10, 100.0);
    guard.update_mark_price(89.0, day + std::chrono::seconds{1});

    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_daily_loss");
    CHECK(guard.daily_loss() >= 100.0);

    guard.update_mark_price(89.0, day + std::chrono::seconds{86400});
    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_daily_loss");
    CHECK(guard.daily_loss() == 0.0);
}

void test_invalid_loss_limits_are_rejected()
{
    bool drawdown_threw = false;
    try { RiskGuard guard(RiskGuardConfig{100, 1000.0, 0.0, 500.0, 10000.0}); }
    catch (const std::invalid_argument &) { drawdown_threw = true; }
    CHECK(drawdown_threw);

    bool daily_loss_threw = false;
    try { RiskGuard guard(RiskGuardConfig{100, 1000.0, 1000.0, -1.0, 10000.0}); }
    catch (const std::invalid_argument &) { daily_loss_threw = true; }
    CHECK(daily_loss_threw);
}

void test_invalid_risk_configuration_is_rejected()
{
    bool threw = false;
    try
    {
        RiskGuard guard(RiskGuardConfig{0, 1000.0});
    }
    catch (const std::invalid_argument &)
    {
        threw = true;
    }
    CHECK(threw);
}
}

int main()
{
    test_order_within_position_limits_is_allowed();
    test_order_that_would_exceed_position_is_rejected();
    test_sell_can_reduce_long_position();
    test_position_value_limit_is_enforced();
    test_order_larger_than_position_limit_is_rejected();
    test_drawdown_halts_and_latches();
    test_daily_loss_halts_and_stays_latched_after_utc_rollover();
    test_invalid_loss_limits_are_rejected();
    test_invalid_risk_configuration_is_rejected();
    std::cout << "RiskGuard tests passed (9/9)\n";
    return 0;
}
