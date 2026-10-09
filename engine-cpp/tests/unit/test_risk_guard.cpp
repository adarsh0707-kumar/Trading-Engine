#include "engine/RiskGuard.hpp"

#include "../TestCheck.hpp"

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
    guard.record_trade("SIM", engine::Side::BUY, 80);
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
    CHECK(decision.reason == "order quantity exceeds max_position");
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
    test_invalid_risk_configuration_is_rejected();
    std::cout << "RiskGuard tests passed (6/6)\n";
    return 0;
}
