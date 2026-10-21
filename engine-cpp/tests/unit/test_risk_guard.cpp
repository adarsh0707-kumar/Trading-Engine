#include "engine/RiskGuard.hpp"

#include "../TestCheck.hpp"

#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <system_error>

using trading::engine_runtime::RiskGuard;
using trading::engine_runtime::RiskGuardConfig;

namespace
{
class ScopedTempDirectory
{
public:
    ScopedTempDirectory()
    {
        const auto stamp = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();

        for (unsigned int attempt = 0; attempt < 100; ++attempt)
        {
            path_ = std::filesystem::temp_directory_path() /
                ("risk-guard-recovery-" + std::to_string(stamp) + "-" +
                 std::to_string(attempt));

            std::error_code error;
            if (std::filesystem::create_directory(path_, error))
                return;

            if (error && error != std::errc::file_exists)
                throw std::filesystem::filesystem_error(
                    "cannot create isolated risk-guard test directory",
                    path_, error);
        }

        throw std::runtime_error("cannot allocate unique test directory");
    }

    ~ScopedTempDirectory()
    {
        std::error_code ignored;
        std::filesystem::remove_all(path_, ignored);
    }

    const std::filesystem::path &path() const noexcept { return path_; }

    ScopedTempDirectory(const ScopedTempDirectory &) = delete;
    ScopedTempDirectory &operator=(const ScopedTempDirectory &) = delete;

private:
    std::filesystem::path path_;
};

std::uint64_t journal_checksum(const std::string &text)
{
    std::uint64_t value = 14695981039346656037ULL;
    for (const unsigned char byte : text)
    {
        value ^= byte;
        value *= 1099511628211ULL;
    }
    return value;
}

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
    const auto diagnostics = guard.halt_diagnostics();
    CHECK(diagnostics.triggered);
    CHECK(diagnostics.reason == "max_drawdown");
    CHECK(diagnostics.timestamp_ms > 0);
    CHECK(diagnostics.equity == 9900.0);
    CHECK(diagnostics.drawdown == 100.0);
    CHECK(diagnostics.daily_loss == 100.0);
    CHECK(!guard.check_order(*make_order("B3", engine::Side::BUY, 90.0, 1)).allowed);
    guard.update_mark_price(110.0);
    CHECK(guard.is_halted());
    CHECK(guard.halt_diagnostics().timestamp_ms == diagnostics.timestamp_ms);
    CHECK(guard.halt_diagnostics().equity == diagnostics.equity);
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
    const auto diagnostics = guard.halt_diagnostics();
    CHECK(diagnostics.triggered);
    CHECK(diagnostics.reason == "max_daily_loss");
    CHECK(diagnostics.equity == 9900.0);
    CHECK(diagnostics.daily_loss == 100.0);
    guard.update_mark_price(90.0, before_midnight + std::chrono::seconds{1});
    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_daily_loss");
    CHECK(guard.daily_loss() == 0.0);
    CHECK(guard.halt_diagnostics().timestamp_ms == diagnostics.timestamp_ms);
    CHECK(guard.halt_diagnostics().daily_loss == 100.0);
}

void test_trade_trigger_captures_diagnostics()
{
    RiskGuard guard(RiskGuardConfig{100, 100000.0, 10000.0, 100.0, 10000.0});
    guard.update_mark_price(100.0);
    guard.record_trade("SIM", engine::Side::BUY, 10, 100.0);
    CHECK(!guard.is_halted());
    guard.record_trade("SIM", engine::Side::SELL, 10, 90.0);
    CHECK(guard.is_halted());
    CHECK(guard.halt_reason() == "max_daily_loss");
    const auto &diagnostics = guard.halt_diagnostics();
    CHECK(diagnostics.triggered);
    CHECK(diagnostics.reason == "max_daily_loss");
    CHECK(diagnostics.timestamp_ms > 0);
    CHECK(diagnostics.equity == 9900.0);
    CHECK(diagnostics.daily_loss == 100.0);
}

void test_state_restores_position_pnl_and_halt_after_restart()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-persist-test.snapshot";
    const auto journal = std::filesystem::path(path.string() + ".trades.log");
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
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
        CHECK(!restored.halt_diagnostics().triggered);
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
    std::filesystem::remove(journal);
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
        CHECK(recovered.replayed_trade_count() == 1);
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

void test_replay_that_crosses_risk_threshold_restores_halt_without_live_diagnostics()
{
    ScopedTempDirectory temp;
    const auto snapshot = temp.path() / "risk-state.snapshot";
    const auto journal = temp.path() / "trades.log";
    RiskGuardConfig config{
        100, 100000.0, 1000.0, 100.0, 10000.0,
        snapshot.string(), journal.string()
    };

    {
        RiskGuard guard(config);
        guard.record_trade("SIM", engine::Side::BUY, 10, 100.0,
                           "replay-buy", "taker-buy", "maker-buy");
        guard.record_trade("SIM", engine::Side::SELL, 10, 90.0,
                           "replay-sell", "taker-sell", "maker-sell");
        CHECK(guard.is_halted());
        CHECK(guard.halt_reason() == "max_daily_loss");
    }

    // Simulate a stale but valid snapshot while preserving both durable journal records.
    const auto now_seconds = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    const auto utc_day = now_seconds / 86400;
    {
        std::ofstream stale(snapshot, std::ios::trunc);
        stale << "2 0 0 0 0 10000 10000 " << utc_day << " 0 - 0\n";
    }

    {
        RiskGuard recovered(config);
        CHECK(recovered.is_halted());
        CHECK(recovered.halt_reason() == "max_daily_loss");
        CHECK(!recovered.halt_diagnostics().triggered);
        CHECK(recovered.position() == 0);
        CHECK(recovered.equity() == 9900.0);
        CHECK(recovered.journal_sequence() == 2);
        CHECK(recovered.replayed_trade_count() == 2);
    }

    // Replay recovery must retain the halt and must not append duplicate trades.
    {
        std::ifstream input(journal);
        std::string line;
        std::size_t records = 0;
        while (std::getline(input, line))
            ++records;
        CHECK(records == 2);
    }
}

void test_duplicate_trade_ids_are_rejected_during_replay()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-duplicate-id.snapshot";
    const auto journal = std::filesystem::path(path.string() + ".trades.log");
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
    RiskGuardConfig config{100, 100000.0, 1000.0, 500.0, 10000.0, path.string()};
    {
        RiskGuard guard(config);
        guard.record_trade("SIM", engine::Side::BUY, 1, 100.0, "trade-duplicate", "taker-1", "maker-1");
        CHECK(guard.journal_sequence() == 1);
    }
    {
        const std::string body = R"(2 "trade-duplicate" "SIM" SELL 1 100 1791645644276 "taker-2" "maker-2")";
        std::ofstream output(journal, std::ios::app);
        output << body << ' ' << journal_checksum(body) << '\n';
    }

    bool rejected_duplicate = false;
    try { RiskGuard restored(config); }
    catch (const std::runtime_error &error)
    {
        rejected_duplicate = std::string(error.what()).find("duplicate trade ID") != std::string::npos;
    }
    CHECK(rejected_duplicate);
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
}

void test_duplicate_trade_id_covered_by_snapshot_is_accepted_without_replay()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-snapshot-covered-duplicate.snapshot";
    const auto journal = std::filesystem::path(path.string() + ".trades.log");
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
    RiskGuardConfig config{100, 100000.0, 1000.0, 500.0, 10000.0, path.string()};
    {
        RiskGuard guard(config);
        guard.record_trade("SIM", engine::Side::BUY, 1, 100.0, "trade-covered", "taker-1", "maker-1");
        CHECK(guard.position() == 1);
        CHECK(guard.journal_sequence() == 1);
    }
    {
        const std::string body = R"(2 "trade-covered" "SIM" SELL 1 100 1791645644276 "taker-2" "maker-2")";
        std::ofstream output(journal, std::ios::app);
        output << body << ' ' << journal_checksum(body) << '\n';
    }
    {
        std::ifstream input(path);
        std::string state;
        std::getline(input, state);
        input.close();
        const auto last_space = state.rfind(' ');
        CHECK(last_space != std::string::npos);
        state.replace(last_space + 1, std::string::npos, "2");
        std::ofstream output(path, std::ios::trunc);
        output << state << '\n';
    }

    {
        RiskGuard restored(config);
        CHECK(restored.position() == 1);
        CHECK(restored.journal_sequence() == 2);
        CHECK(restored.replayed_trade_count() == 0);
    }
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
}

void test_duplicate_trade_id_is_rejected_before_append()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-duplicate-live.snapshot";
    const auto journal = std::filesystem::path(path.string() + ".trades.log");
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
    RiskGuardConfig config{100, 100000.0, 1000.0, 500.0, 10000.0, path.string()};
    {
        RiskGuard guard(config);
        guard.record_trade("SIM", engine::Side::BUY, 1, 100.0, "trade-once", "taker-1", "maker-1");
        bool rejected_duplicate = false;
        try { guard.record_trade("SIM", engine::Side::BUY, 1, 100.0, "trade-once", "taker-2", "maker-2"); }
        catch (const std::logic_error &) { rejected_duplicate = true; }
        CHECK(rejected_duplicate);
        CHECK(guard.position() == 1);
        CHECK(guard.journal_sequence() == 1);
    }
    std::filesystem::remove(path);
    std::filesystem::remove(journal);
}

void test_journal_write_failure_does_not_apply_risk_trade()
{
    const auto path = std::filesystem::temp_directory_path() / "risk-guard-journal-write-failure.snapshot";
    const auto journal = std::filesystem::path(path.string() + ".trades.log");
    std::filesystem::remove(path);
    std::filesystem::remove_all(journal);
    RiskGuardConfig config{100, 100000.0, 1000.0, 500.0, 10000.0, path.string(), journal.string()};
    {
        RiskGuard guard(config);
        std::filesystem::create_directory(journal); // A directory cannot be opened as an append-only journal.
        bool failed_closed = false;
        try { guard.record_trade("SIM", engine::Side::BUY, 1, 100.0, "trade-no-write", "taker", "maker"); }
        catch (const std::runtime_error &) { failed_closed = true; }
        CHECK(failed_closed);
        CHECK(guard.position() == 0);
        CHECK(guard.journal_sequence() == 0);
    }
    std::filesystem::remove(path);
    std::filesystem::remove_all(journal);
}

void test_snapshot_save_failure_recovers_journaled_trade()
{
    ScopedTempDirectory temp;
    const auto snapshot = temp.path() / "risk-state.snapshot";
    const auto journal = temp.path() / "trades.log";
    RiskGuardConfig config{
        100, 100000.0, 1000.0, 500.0, 10000.0,
        snapshot.string(), journal.string()
    };

    {
        RiskGuard guard(config);
        CHECK(guard.position() == 0);
        CHECK(guard.journal_sequence() == 0);

        // Block snapshot replacement without blocking the sibling journal.
        std::filesystem::remove(snapshot);
        CHECK(std::filesystem::create_directory(snapshot));

        bool expected_save_failure = false;
        try
        {
            guard.record_trade(
                "SIM", engine::Side::BUY, 1, 100.0,
                "trade-snapshot-failure", "taker-failure", "maker-failure");
        }
        catch (const std::runtime_error &error)
        {
            expected_save_failure =
                std::string(error.what()).find(
                    "cannot atomically replace risk-state snapshot") !=
                std::string::npos;
        }

        CHECK(expected_save_failure);
        // The journal append and in-memory risk update preceded snapshot save.
        CHECK(guard.position() == 1);
        CHECK(guard.journal_sequence() == 1);
    }

    // Remove only the deliberate obstruction; preserve the journal.
    std::filesystem::remove_all(snapshot);
    CHECK(std::filesystem::exists(journal));

    {
        std::ifstream input(journal);
        std::string line;
        std::size_t records = 0;
        while (std::getline(input, line))
            ++records;
        CHECK(records == 1);
    }

    {
        RiskGuard recovered(config);
        CHECK(recovered.position() == 1);
        CHECK(recovered.journal_sequence() == 1);
        CHECK(recovered.replayed_trade_count() == 1);
    }

    // Recovery must not append a second copy of the original trade.
    {
        std::ifstream input(journal);
        std::string line;
        std::size_t records = 0;
        while (std::getline(input, line))
            ++records;
        CHECK(records == 1);
    }
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
    std::filesystem::remove(path);
    std::filesystem::remove(path.string() + ".trades.log");
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
    test_trade_trigger_captures_diagnostics();
    test_state_restores_position_pnl_and_halt_after_restart();
    test_trade_journal_replays_records_after_stale_snapshot();
    test_duplicate_trade_ids_are_rejected_during_replay();
    test_duplicate_trade_id_covered_by_snapshot_is_accepted_without_replay();
    test_duplicate_trade_id_is_rejected_before_append();
    test_journal_write_failure_does_not_apply_risk_trade();
    test_snapshot_save_failure_recovers_journaled_trade();
    test_corrupt_trade_journal_fails_closed();
    test_corrupt_state_fails_closed();
    test_invalid_risk_configuration_is_rejected();
    std::cout << "RiskGuard tests passed (20/20)\n";
    return 0;
}
