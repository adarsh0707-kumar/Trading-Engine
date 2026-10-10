#include "engine/RiskGuard.hpp"

#include "../TestCheck.hpp"

#include <chrono>
#include <cmath>
#include <iostream>
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
    guard.record_trade("SIM", engine::Side::BUY, 80, 100.0);
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

void test_position_limit_below_at_and_above_boundary()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    const auto below = guard.check_order(*make_order("B1", engine::Side::BUY, 50.0, 99));
    const auto at = guard.check_order(*make_order("B2", engine::Side::BUY, 50.0, 100));
    const auto above = guard.check_order(*make_order("B3", engine::Side::BUY, 50.0, 101));

    CHECK(below.allowed);
    CHECK(below.projected_position == 99);
    CHECK(at.allowed);
    CHECK(at.projected_position == 100);
    CHECK(!above.allowed);
    CHECK(above.reason == "projected position exceeds max_position");
}

void test_position_value_limit_below_at_and_above_boundary()
{
    RiskGuard guard(RiskGuardConfig{200, 10000.0});
    const auto below = guard.check_order(*make_order("B1", engine::Side::BUY, 99.99, 100));
    const auto at = guard.check_order(*make_order("B2", engine::Side::BUY, 100.0, 100));
    const auto above = guard.check_order(*make_order("B3", engine::Side::BUY, 100.01, 100));

    CHECK(below.allowed);
    CHECK(below.projected_position_value < 10000.0);
    CHECK(at.allowed);
    CHECK(at.projected_position_value == 10000.0);
    CHECK(!above.allowed);
    CHECK(above.reason == "projected position value exceeds max_position_value");
}

void test_order_larger_than_position_limit_is_rejected()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    const auto order = make_order("B1", engine::Side::BUY, 100.0, 101);
    const auto decision = guard.check_order(*order);
    CHECK(!decision.allowed);
    CHECK(decision.reason == "projected position exceeds max_position");
}

void test_realized_and_unrealized_pnl_when_reducing_and_reversing_position()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0, 10000.0, 10000.0, 10000.0});
    guard.record_trade("SIM", engine::Side::BUY, 10, 100.0);
    guard.update_mark_price(110.0);
    CHECK(guard.position() == 10);
    CHECK(guard.equity() == 10100.0);

    // Closing four units realizes +40; the remaining six retain a 100 entry.
    guard.record_trade("SIM", engine::Side::SELL, 4, 110.0);
    CHECK(guard.position() == 6);
    CHECK(guard.equity() == 10100.0);

    // Selling eight closes the remaining six for -60 and opens a short of two.
    guard.record_trade("SIM", engine::Side::SELL, 8, 90.0);
    CHECK(guard.position() == -2);
    CHECK(guard.equity() == 9980.0);

    // A lower mark benefits the short by 20 without changing realized P&L.
    guard.update_mark_price(80.0);
    CHECK(guard.position() == -2);
    CHECK(guard.equity() == 10000.0);
    CHECK(!guard.is_halted());
}

void test_drawdown_halts_at_exact_threshold_and_stays_latched()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0, 100.0, 10000.0, 10000.0});
    guard.update_mark_price(100.0);
    guard.record_trade("SIM", engine::Side::BUY, 10, 100.0);
    guard.update_mark_price(90.0);

    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_drawdown");
    CHECK(guard.drawdown() == 100.0);

    const auto rejected = guard.check_order(*make_order("B3", engine::Side::BUY, 90.0, 1));
    CHECK(!rejected.allowed);
    CHECK(rejected.reason.find("risk halt active") == 0);

    guard.update_mark_price(110.0);
    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_drawdown");
}

void test_daily_loss_halts_at_exact_threshold_and_stays_latched_after_utc_rollover()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0, 10000.0, 100.0, 10000.0});
    const auto day_start_seconds = (std::int64_t{2000000000} / 86400) * 86400;
    const auto before_midnight = std::chrono::system_clock::time_point{
        std::chrono::seconds{day_start_seconds + 86399}};
    guard.update_mark_price(100.0, before_midnight);
    guard.record_trade("SIM", engine::Side::BUY, 10, 100.0);
    guard.update_mark_price(90.0, before_midnight);

    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_daily_loss");
    CHECK(guard.daily_loss() == 100.0);

    // The next UTC date resets the daily baseline, but must not clear the halt.
    guard.update_mark_price(90.0, before_midnight + std::chrono::seconds{1});
    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_daily_loss");
    CHECK(guard.daily_loss() == 0.0);
    CHECK(!guard.check_order(*make_order("B4", engine::Side::BUY, 90.0, 1)).allowed);
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
    test_position_limit_below_at_and_above_boundary();
    test_position_value_limit_below_at_and_above_boundary();
    test_order_larger_than_position_limit_is_rejected();
    test_realized_and_unrealized_pnl_when_reducing_and_reversing_position();
    test_drawdown_halts_at_exact_threshold_and_stays_latched();
    test_daily_loss_halts_at_exact_threshold_and_stays_latched_after_utc_rollover();
    test_invalid_loss_limits_are_rejected();
    test_invalid_risk_configuration_is_rejected();
    std::cout << "RiskGuard tests passed (12/12)\n";
    return 0;
}
