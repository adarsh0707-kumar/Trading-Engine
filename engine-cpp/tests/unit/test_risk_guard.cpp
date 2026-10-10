#include "engine/RiskGuard.hpp"

#include "../TestCheck.hpp"

#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

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
    const auto decision = guard.check_order(*make_order("B1", engine::Side::BUY, 100.0, 50));
    CHECK(decision.allowed);
    CHECK(decision.projected_position == 50);
    CHECK(decision.projected_position_value == 5000.0);
}

void test_order_that_would_exceed_position_is_rejected()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    guard.record_trade("SIM", engine::Side::BUY, 80, 100.0);
    const auto decision = guard.check_order(*make_order("B2", engine::Side::BUY, 100.0, 21));
    CHECK(!decision.allowed);
    CHECK(decision.reason == "projected position exceeds max_position");
    CHECK(guard.position() == 80);
}

void test_sell_can_reduce_long_position()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    guard.record_trade("SIM", engine::Side::BUY, 80, 100.0);
    const auto decision = guard.check_order(*make_order("S1", engine::Side::SELL, 100.0, 30));
    CHECK(decision.allowed);
    CHECK(decision.projected_position == 50);
}

void test_position_value_limit_is_enforced()
{
    RiskGuard guard(RiskGuardConfig{100, 5000.0});
    const auto decision = guard.check_order(*make_order("B1", engine::Side::BUY, 100.0, 51));
    CHECK(!decision.allowed);
    CHECK(decision.reason == "projected position value exceeds max_position_value");
}

void test_position_limit_below_at_and_above_boundary()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    CHECK(guard.check_order(*make_order("B1", engine::Side::BUY, 50.0, 99)).allowed);
    CHECK(guard.check_order(*make_order("B2", engine::Side::BUY, 50.0, 100)).allowed);
    const auto above = guard.check_order(*make_order("B3", engine::Side::BUY, 50.0, 101));
    CHECK(!above.allowed);
    CHECK(above.reason == "projected position exceeds max_position");
}

void test_position_value_limit_below_at_and_above_boundary()
{
    RiskGuard guard(RiskGuardConfig{200, 10000.0});
    CHECK(guard.check_order(*make_order("B1", engine::Side::BUY, 99.99, 100)).allowed);
    CHECK(guard.check_order(*make_order("B2", engine::Side::BUY, 100.0, 100)).allowed);
    const auto above = guard.check_order(*make_order("B3", engine::Side::BUY, 100.01, 100));
    CHECK(!above.allowed);
}

void test_order_larger_than_position_limit_is_rejected()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0});
    const auto decision = guard.check_order(*make_order("B1", engine::Side::BUY, 100.0, 101));
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
    guard.record_trade("SIM", engine::Side::SELL, 4, 110.0);
    CHECK(guard.position() == 6);
    CHECK(guard.equity() == 10100.0);
    guard.record_trade("SIM", engine::Side::SELL, 8, 90.0);
    CHECK(guard.position() == -2);
    CHECK(guard.equity() == 9980.0);
    guard.update_mark_price(80.0);
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
    CHECK(!guard.check_order(*make_order("B3", engine::Side::BUY, 90.0, 1)).allowed);
    guard.update_mark_price(110.0);
    CHECK(guard.is_halted());
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
    guard.update_mark_price(90.0, before_midnight + std::chrono::seconds{1});
    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_daily_loss");
    CHECK(guard.daily_loss() == 0.0);
}

void test_state_restores_position_pnl_and_halt_after_restart()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-persist-test.snapshot";
    std::filesystem::remove(path);
    RiskGuardConfig config{100, 100000.0, 100.0, 10000.0, 10000.0, path.string()};
    {
        RiskGuard guard(config);
        guard.record_trade("SIM", engine::Side::BUY, 10, 100.0);
        guard.update_mark_price(90.0);
        CHECK(guard.is_halted());
        CHECK(guard.position() == 10);
    }
    {
        RiskGuard restored(config);
        CHECK(restored.is_halted());
        CHECK(restored.halt_reason() == "max_drawdown");
        CHECK(restored.position() == 10);
        CHECK(restored.equity() == 9900.0);
        CHECK(!restored.check_order(*make_order("B4", engine::Side::BUY, 90.0, 1)).allowed);
        bool denied = false;
        try { restored.resume_after_operator_authorization(false); }
        catch (const std::runtime_error &) { denied = true; }
        CHECK(denied);
        CHECK(restored.is_halted());
        restored.resume_after_operator_authorization(true);
        CHECK(!restored.is_halted());
        CHECK(restored.position() == 10);
    }
    std::filesystem::remove(path);
}

void test_trade_journal_replays_records_after_stale_snapshot()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-journal-replay.snapshot";
    const auto journal = std::filesystem::path(path.string() + ".trades.log");
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
    RiskGuardConfig config{100, 100000.0, 1000.0, 500.0, 10000.0, path.string()};
    {
        RiskGuard guard(config);
        guard.record_trade("SIM", engine::Side::BUY, 10, 100.0, "trade-001", "taker-001", "maker-001");
        CHECK(guard.position() == 10);
    }

    const auto now_seconds = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    const auto utc_day = now_seconds / 86400;
    {
        std::ofstream stale(path, std::ios::trunc);
        stale << "2 0 0 0 0 10000 10000 " << utc_day << " 0 - 0\n";
    }
    {
        RiskGuard recovered(config);
        CHECK(recovered.position() == 10);
        CHECK(recovered.equity() == 10000.0);
    }
    {
        std::ifstream records(journal);
        std::string contents((std::istreambuf_iterator<char>(records)), std::istreambuf_iterator<char>());
        CHECK(contents.find("trade-001") != std::string::npos);
        CHECK(contents.find("taker-001") != std::string::npos);
        CHECK(contents.find("maker-001") != std::string::npos);
    }
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
}

void test_corrupt_trade_journal_fails_closed()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-journal-corrupt.snapshot";
    const auto journal = std::filesystem::path(path.string() + ".trades.log");
    std::filesystem::remove(path);
    { std::ofstream output(journal); output << "1 trade-1 SIM BUY 10 100 0 taker maker 123\n"; }
    bool threw = false;
    try { RiskGuard guard(RiskGuardConfig{100, 100000.0, 1000.0, 500.0, 10000.0, path.string()}); }
    catch (const std::runtime_error &) { threw = true; }
    CHECK(threw);
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
}

void test_corrupt_state_fails_closed()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-corrupt-test.snapshot";
    { std::ofstream output(path); output << "partial snapshot"; }
    bool threw = false;
    try { RiskGuard guard(RiskGuardConfig{100, 100000.0, 1000.0, 500.0, 100000.0, path.string()}); }
    catch (const std::runtime_error &) { threw = true; }
    CHECK(threw);
    std::filesystem::remove(path);
}

void test_invalid_risk_configuration_is_rejected()
{
    bool threw = false;
    try { RiskGuard guard(RiskGuardConfig{0, 1000.0}); }
    catch (const std::invalid_argument &) { threw = true; }
    CHECK(threw);
    threw = false;
    try { RiskGuard guard(RiskGuardConfig{100, 1000.0, 0.0, 500.0, 10000.0}); }
    catch (const std::invalid_argument &) { threw = true; }
    CHECK(threw);
    threw = false;
    try { RiskGuard guard(RiskGuardConfig{100, 1000.0, 1000.0, -1.0, 10000.0}); }
    catch (const std::invalid_argument &) { threw = true; }
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
    test_state_restores_position_pnl_and_halt_after_restart();\n    test_trade_journal_replays_records_after_stale_snapshot();\n    test_corrupt_trade_journal_fails_closed();
    test_corrupt_state_fails_closed();
    test_invalid_risk_configuration_is_rejected();
    std::cout << "RiskGuard tests passed (15/15)\n";
    return 0;
}
