#include "engine/RiskGuard.hpp"

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <cstring>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>
#include <unordered_set>
#include <utility>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#else
#include <fcntl.h>
#include <unistd.h>
#endif

#include <atomic>
#include <chrono>

namespace trading { namespace engine_runtime {
namespace {
constexpr int STATE_VERSION = 2;

std::string journal_path_for(const RiskGuardConfig &config) {
    if (!config.trade_journal_file_path.empty()) return config.trade_journal_file_path;
    if (config.state_file_path.empty()) return {};
    return config.state_file_path + ".trades.log";
}

std::uint64_t checksum(const std::string &text) {
    std::uint64_t value = 14695981039346656037ULL;
    for (const unsigned char byte : text) {
        value ^= byte;
        value *= 1099511628211ULL;
    }
    return value;
}

std::string side_name(::engine::Side side) {
    return side == ::engine::Side::BUY ? "BUY" : "SELL";
}
} // namespace

RiskGuard::RiskGuard(const RiskGuardConfig &config)
    : config_(config), peak_equity_(config.initial_equity), day_start_equity_(config.initial_equity) {
    if (config_.max_position <= 0) throw std::invalid_argument("max_position must be positive");
    if (!std::isfinite(config_.max_position_value) || config_.max_position_value <= 0)
        throw std::invalid_argument("max_position_value must be finite and positive");
    if (!std::isfinite(config_.max_drawdown) || config_.max_drawdown <= 0)
        throw std::invalid_argument("max_drawdown must be finite and positive");
    if (!std::isfinite(config_.max_daily_loss) || config_.max_daily_loss <= 0)
        throw std::invalid_argument("max_daily_loss must be finite and positive");
    if (!std::isfinite(config_.initial_equity) || config_.initial_equity <= 0)
        throw std::invalid_argument("initial_equity must be finite and positive");
    load_state();
    replay_trade_journal();
    if (utc_day_ == -1) roll_daily_window(std::chrono::system_clock::now());
    save_state();
}

void RiskGuard::load_state() {
    if (config_.state_file_path.empty()) return;
    const std::filesystem::path path(config_.state_file_path);
    if (!std::filesystem::exists(path)) return;

    std::ifstream in(path);
    int version = 0, halted = 0;
    std::int64_t position = 0, day = -1;
    double average = 0, realized = 0, mark = 0, peak = 0, day_start = 0;
    std::string reason;
    std::uint64_t sequence = 0;
    if (!(in >> version >> position >> average >> realized >> mark >> peak >> day_start >> day >> halted >> reason) ||
        (version != 1 && version != STATE_VERSION) || (halted != 0 && halted != 1) ||
        position > config_.max_position || position < -config_.max_position ||
        !std::isfinite(average) || average < 0 || !std::isfinite(realized) ||
        !std::isfinite(mark) || mark < 0 || !std::isfinite(peak) || peak <= 0 ||
        !std::isfinite(day_start) || day_start <= 0 || day < 0 || (halted == 1 && reason == "-"))
        throw std::runtime_error("risk state is corrupt or incompatible; refusing startup");
    if (version == STATE_VERSION && !(in >> sequence))
        throw std::runtime_error("risk state is missing its journal sequence; refusing startup");
    std::string extra;
    if (in >> extra) throw std::runtime_error("risk state has unexpected trailing data; refusing startup");

    position_ = position;
    average_entry_price_ = average;
    realized_pnl_ = realized;
    mark_price_ = mark;
    peak_equity_ = peak;
    day_start_equity_ = day_start;
    utc_day_ = day;
    halted_ = halted == 1;
    halt_reason_ = reason == "-" ? "" : reason;
    journal_sequence_ = sequence;
}

void RiskGuard::save_state() const {
    if (config_.state_file_path.empty()) return;

    const std::filesystem::path path(config_.state_file_path);
    if (!path.parent_path().empty())
        std::filesystem::create_directories(path.parent_path());

    std::ostringstream snapshot;
    snapshot << STATE_VERSION << ' ' << position_ << ' '
             << std::setprecision(std::numeric_limits<double>::max_digits10)
             << average_entry_price_ << ' ' << realized_pnl_ << ' ' << mark_price_ << ' '
             << peak_equity_ << ' ' << day_start_equity_ << ' ' << utc_day_ << ' '
             << (halted_ ? 1 : 0) << ' '
             << (halt_reason_.empty() ? "-" : halt_reason_) << ' '
             << journal_sequence_ << '\n';

    const std::string data = snapshot.str();

    // O_EXCL prevents this process from truncating another writer's temporary
    // file. It does not provide locking or make concurrent writers safe.
    static std::atomic<std::uint64_t> temp_sequence{0};
    std::filesystem::path temp;
    int fd = -1;

    for (int attempt = 0; attempt < 100; ++attempt) {
        const auto nonce =
            std::chrono::steady_clock::now().time_since_epoch().count();
        temp = path.string() + ".tmp." + std::to_string(nonce) + "." +
               std::to_string(temp_sequence.fetch_add(1));

#ifdef _WIN32
        fd = ::_open(
            temp.string().c_str(),
            _O_WRONLY | _O_CREAT | _O_EXCL | _O_BINARY,
            _S_IREAD | _S_IWRITE);
#else
        fd = ::open(temp.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0600);
#endif
        if (fd >= 0) break;

        const int open_errno = errno;
        if (open_errno == EEXIST) continue;

        throw std::runtime_error(
            "cannot create temporary risk-state file: " +
            std::string(std::strerror(open_errno)));
    }

    if (fd < 0)
        throw std::runtime_error(
            "could not allocate a unique temporary risk-state filename");

    auto close_fd = [&]() {
        if (fd < 0) return 0;

        const int descriptor = fd;
        fd = -1;
#ifdef _WIN32
        return ::_close(descriptor);
#else
        return ::close(descriptor);
#endif
    };

    auto remove_temp = [&]() {
        std::error_code ignored;
        std::filesystem::remove(temp, ignored);
    };

    auto fail_before_rename = [&](const std::string& message,
                                  int saved_errno) -> void {
        (void)close_fd();
        remove_temp();
        throw std::runtime_error(
            message + ": " + std::string(std::strerror(saved_errno)));
    };

    std::size_t written = 0;
    while (written < data.size()) {
#ifdef _WIN32
        const auto remaining = data.size() - written;
        const auto chunk = static_cast<unsigned int>(
            std::min<std::size_t>(remaining, 0x7fffffffU));
        const auto count = ::_write(fd, data.data() + written, chunk);
#else
        const auto count = ::write(fd, data.data() + written, data.size() - written);
#endif
        if (count < 0) {
            const int write_errno = errno;
            if (write_errno == EINTR) continue;
            fail_before_rename("failed to write risk-state snapshot",
                               write_errno);
        }

        if (count == 0) {
            (void)close_fd();
            remove_temp();
            throw std::runtime_error(
                "failed to write risk-state snapshot: write returned zero");
        }

        written += static_cast<std::size_t>(count);
    }

    int sync_result = 0;
#ifdef _WIN32
    sync_result = ::_commit(fd);
#else
    do {
        sync_result = ::fsync(fd);
    } while (sync_result != 0 && errno == EINTR);
#endif
    if (sync_result != 0) {
        const int sync_errno = errno;
        fail_before_rename("failed to sync risk-state snapshot", sync_errno);
    }

    if (close_fd() != 0) {
        const int saved_errno = errno;
        remove_temp();
        throw std::runtime_error(
            "failed to close risk-state snapshot: " +
            std::string(std::strerror(saved_errno)));
    }

    std::error_code error;
    std::filesystem::rename(temp, path, error);
    if (error) {
        remove_temp();
        throw std::runtime_error(
            "cannot atomically replace risk-state snapshot: " + error.message());
    }

#ifndef _WIN32
    // Rename has already made the new snapshot visible. Failures below mean
    // that persistence across a sudden system crash could not be confirmed.
    const auto parent = path.parent_path().empty()
        ? std::filesystem::path(".")
        : path.parent_path();

    const int directory_fd = ::open(parent.c_str(), O_RDONLY | O_DIRECTORY);
    if (directory_fd < 0) {
        const int saved_errno = errno;
        throw std::runtime_error(
            "snapshot replaced, but cannot open risk-state directory for sync: " +
            std::string(std::strerror(saved_errno)));
    }

    int directory_sync_result = 0;
    do {
        directory_sync_result = ::fsync(directory_fd);
    } while (directory_sync_result != 0 && errno == EINTR);
    const int directory_sync_errno =
        directory_sync_result != 0 ? errno : 0;
    const int directory_close_result = ::close(directory_fd);
    const int directory_close_errno =
        directory_close_result != 0 ? errno : 0;

    if (directory_sync_result != 0)
        throw std::runtime_error(
            "snapshot replaced, but risk-state directory durability is unconfirmed: " +
            std::string(std::strerror(directory_sync_errno)));

    if (directory_close_result != 0)
        throw std::runtime_error(
            "snapshot replaced and directory synced, but directory close failed: " +
            std::string(std::strerror(directory_close_errno)));
#endif
}

std::uint64_t RiskGuard::append_trade_journal(
    const std::string &symbol, ::engine::Side side, std::int64_t quantity, double price,
    const std::string &trade_id, const std::string &taker_order_id, const std::string &maker_order_id) {
    const std::string path_string = journal_path_for(config_);
    if (path_string.empty()) return journal_sequence_;

    const std::uint64_t sequence = journal_sequence_ + 1;
    const auto now = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    std::ostringstream payload;
    payload << sequence << ' ' << std::quoted(trade_id.empty() ? ("risk-trade-" + std::to_string(sequence)) : trade_id)
            << ' ' << std::quoted(symbol) << ' ' << side_name(side) << ' ' << quantity << ' '
            << std::setprecision(std::numeric_limits<double>::max_digits10) << price << ' ' << now << ' '
            << std::quoted(taker_order_id) << ' ' << std::quoted(maker_order_id);
    const std::string body = payload.str();
    const std::string line = body + ' ' + std::to_string(checksum(body)) + '\n';

    const std::filesystem::path path(path_string);
    if (!path.parent_path().empty()) std::filesystem::create_directories(path.parent_path());
    const bool existed_before_append = std::filesystem::exists(path);
#ifdef _WIN32
    const int fd = ::_open(path.string().c_str(), _O_WRONLY | _O_CREAT | _O_APPEND | _O_BINARY, _S_IREAD | _S_IWRITE);
#else
    const int fd = ::open(path.c_str(), O_WRONLY | O_CREAT | O_APPEND, 0600);
#endif
    if (fd < 0) throw std::runtime_error("cannot open durable trade journal");
    std::size_t written = 0;
    while (written < line.size()) {
#ifdef _WIN32
        const auto count = ::_write(fd, line.data() + written,
                                    static_cast<unsigned int>(line.size() - written));
#else
        const auto count = ::write(fd, line.data() + written, line.size() - written);
#endif
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) {
            const int saved_errno = errno;
#ifdef _WIN32
            ::_close(fd);
#else
            ::close(fd);
#endif
            throw std::runtime_error("failed to append durable trade journal: " +
                                     std::string(std::strerror(saved_errno)));
        }
        written += static_cast<std::size_t>(count);
    }
#ifdef _WIN32
    const int sync_result = ::_commit(fd);
#else
    const int sync_result = ::fsync(fd);
#endif
    if (sync_result != 0) {
        const int saved_errno = errno;
#ifdef _WIN32
        ::_close(fd);
#else
        ::close(fd);
#endif
        throw std::runtime_error("failed to sync durable trade journal: " +
                                 std::string(std::strerror(saved_errno)));
    }
#ifdef _WIN32
    if (::_close(fd) != 0) throw std::runtime_error("failed to close durable trade journal");
#else
    if (::close(fd) != 0) throw std::runtime_error("failed to close durable trade journal");
    if (!existed_before_append) {
        const auto parent = path.parent_path().empty() ? std::filesystem::path(".") : path.parent_path();
        const int directory_fd = ::open(parent.c_str(), O_RDONLY | O_DIRECTORY);
        if (directory_fd < 0) throw std::runtime_error("cannot open trade-journal directory for sync");
        const int directory_sync_result = ::fsync(directory_fd);
        ::close(directory_fd);
        if (directory_sync_result != 0) throw std::runtime_error("failed to fsync trade-journal directory");
    }
#endif
    return sequence;
}

void RiskGuard::replay_trade_journal() {
    const std::string path_string = journal_path_for(config_);
    if (path_string.empty()) return;
    const std::filesystem::path path(path_string);
    const std::uint64_t snapshot_sequence = journal_sequence_;
    if (!std::filesystem::exists(path)) {
        if (snapshot_sequence != 0)
            throw std::runtime_error("risk snapshot references a missing trade journal; refusing startup");
        return;
    }

    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot read durable trade journal; refusing startup");
    std::string line;
    std::unordered_set<std::string> trade_ids;
    std::uint64_t expected_sequence = 1;
    while (std::getline(in, line)) {
        if (line.empty()) throw std::runtime_error("trade journal contains an empty record; refusing startup");
        const auto split = line.rfind(' ');
        if (split == std::string::npos) throw std::runtime_error("trade journal record has no checksum; refusing startup");
        const std::string body = line.substr(0, split);
        std::uint64_t recorded_checksum = 0;
        try { recorded_checksum = std::stoull(line.substr(split + 1)); }
        catch (...) { throw std::runtime_error("trade journal checksum is invalid; refusing startup"); }
        if (recorded_checksum != checksum(body))
            throw std::runtime_error("trade journal checksum mismatch; refusing startup");

        std::istringstream record(body);
        std::uint64_t sequence = 0;
        std::string trade_id, symbol, side_text, taker_order_id, maker_order_id;
        std::int64_t quantity = 0, timestamp_ms = 0;
        double price = 0;
        if (!(record >> sequence >> std::quoted(trade_id) >> std::quoted(symbol) >> side_text >>
              quantity >> price >> timestamp_ms >> std::quoted(taker_order_id) >> std::quoted(maker_order_id)))
            throw std::runtime_error("trade journal record is malformed; refusing startup");
        std::string extra;
        if (record >> extra) throw std::runtime_error("trade journal record has trailing data; refusing startup");
        if (sequence != expected_sequence++ || trade_id.empty() || symbol.empty() || quantity <= 0 ||
            !std::isfinite(price) || price <= 0 || timestamp_ms < 0 ||
            (side_text != "BUY" && side_text != "SELL"))
            throw std::runtime_error("trade journal sequence or fields are invalid; refusing startup");
        const bool duplicate_trade_id = !trade_ids.insert(trade_id).second;
        if (duplicate_trade_id && sequence > snapshot_sequence)
            throw std::runtime_error("trade journal contains duplicate trade ID after snapshot; refusing startup");

        if (sequence > snapshot_sequence) {
            apply_trade(symbol, side_text == "BUY" ? ::engine::Side::BUY : ::engine::Side::SELL, quantity, price);
            journal_sequence_ = sequence;
            ++replayed_trade_count_;
        }
    }
    if (!in.eof()) throw std::runtime_error("failed while reading durable trade journal; refusing startup");
    const std::uint64_t last_sequence = expected_sequence - 1;
    if (last_sequence < snapshot_sequence)
        throw std::runtime_error("trade journal is behind the risk snapshot; refusing startup");
    journal_sequence_ = last_sequence;
    synthetic_trade_sequence_ = last_sequence;
    trade_ids_ = std::move(trade_ids);
}

RiskDecision RiskGuard::check_order(const ::engine::Order &order) const {
    RiskDecision decision;
    decision.projected_position = position_;
    if (halted_) { decision.reason = "risk halt active: " + halt_reason_; return decision; }
    if (!order.is_valid() || !order.is_active() || !std::isfinite(order.price())) {
        decision.reason = "order is invalid or inactive";
        return decision;
    }
    const std::int64_t quantity = order.side() == ::engine::Side::BUY ? order.quantity() : -order.quantity();
    const long double projected = static_cast<long double>(position_) + quantity;
    if (projected > config_.max_position || projected < -config_.max_position) {
        decision.reason = "projected position exceeds max_position";
        return decision;
    }
    decision.projected_position = static_cast<std::int64_t>(projected);
    decision.projected_position_value = std::abs(static_cast<double>(decision.projected_position)) * order.price();
    if (!std::isfinite(decision.projected_position_value) ||
        decision.projected_position_value > config_.max_position_value) {
        decision.reason = "projected position value exceeds max_position_value";
        return decision;
    }
    decision.allowed = true;
    return decision;
}

void RiskGuard::update_mark_price(double price, std::chrono::system_clock::time_point now) {
    if (!std::isfinite(price) || price <= 0) throw std::invalid_argument("mark price must be finite and positive");
    roll_daily_window(now);
    mark_price_ = price;
    evaluate_limits();
    save_state();
}

void RiskGuard::record_trade(const std::string &symbol, ::engine::Side side, std::int64_t quantity, double price,
                             const std::string &trade_id, const std::string &taker_order_id,
                             const std::string &maker_order_id) {
    if (symbol.empty()) throw std::invalid_argument("trade symbol cannot be empty");
    if (quantity <= 0) throw std::invalid_argument("trade quantity must be positive");
    if (!std::isfinite(price) || price <= 0) throw std::invalid_argument("trade price must be finite and positive");
    const std::int64_t signed_quantity = side == ::engine::Side::BUY ? quantity : -quantity;
    const long double projected = static_cast<long double>(position_) + signed_quantity;
    if (projected > config_.max_position || projected < -config_.max_position)
        throw std::logic_error("executed trade would violate max_position");

    std::string canonical_trade_id = trade_id;
    if (canonical_trade_id.empty()) {
        synthetic_trade_sequence_ = std::max(synthetic_trade_sequence_, journal_sequence_);
        do {
            ++synthetic_trade_sequence_;
            canonical_trade_id = "risk-trade-" + std::to_string(synthetic_trade_sequence_);
        } while (trade_ids_.count(canonical_trade_id) != 0);
    }
    if (trade_ids_.count(canonical_trade_id) != 0)
        throw std::logic_error("trade ID has already been recorded");

    const std::uint64_t sequence = append_trade_journal(
        symbol, side, quantity, price, canonical_trade_id, taker_order_id, maker_order_id);
    trade_ids_.insert(canonical_trade_id);
    apply_trade(symbol, side, quantity, price);
    journal_sequence_ = sequence;
    synthetic_trade_sequence_ = std::max(synthetic_trade_sequence_, sequence);
    save_state();
}

void RiskGuard::apply_trade(const std::string &symbol, ::engine::Side side, std::int64_t quantity, double price) {
    if (symbol.empty() || quantity <= 0 || !std::isfinite(price) || price <= 0)
        throw std::runtime_error("trade journal contains an invalid trade");
    const std::int64_t signed_quantity = side == ::engine::Side::BUY ? quantity : -quantity;
    const long double projected = static_cast<long double>(position_) + signed_quantity;
    if (projected > config_.max_position || projected < -config_.max_position)
        throw std::runtime_error("replayed trade violates max_position; refusing startup");

    const std::int64_t old_position = position_;
    const auto next_position = static_cast<std::int64_t>(projected);
    if (old_position == 0 || (old_position > 0) == (signed_quantity > 0)) {
        const long double old_notional = static_cast<long double>(std::abs(old_position)) * average_entry_price_;
        const long double added_notional = static_cast<long double>(quantity) * price;
        average_entry_price_ = static_cast<double>(
            (old_notional + added_notional) / static_cast<long double>(std::abs(next_position)));
    } else {
        const auto closing = std::min<std::int64_t>(std::abs(old_position), quantity);
        realized_pnl_ += static_cast<double>(closing) *
            (old_position > 0 ? price - average_entry_price_ : average_entry_price_ - price);
        if (next_position == 0) average_entry_price_ = 0;
        else if ((next_position > 0) != (old_position > 0)) average_entry_price_ = price;
    }
    position_ = next_position;
    mark_price_ = price;
    evaluate_limits();
}

void RiskGuard::resume_after_operator_authorization(bool authorized) {
    if (!authorized) throw std::runtime_error("operator authorization required to resume risk halt");
    if (!halted_) return;
    halted_ = false;
    halt_reason_.clear();
    peak_equity_ = equity();
    day_start_equity_ = equity();
    const auto seconds = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    utc_day_ = seconds / 86400;
    save_state();
}

void RiskGuard::roll_daily_window(std::chrono::system_clock::time_point now) noexcept {
    const auto seconds = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    const auto day = seconds / 86400;
    if (utc_day_ == -1) utc_day_ = day;
    else if (day != utc_day_) { utc_day_ = day; day_start_equity_ = equity(); }
}

void RiskGuard::evaluate_limits() noexcept {
    const double current_equity = equity();
    peak_equity_ = std::max(peak_equity_, current_equity);
    if (!halted_ && peak_equity_ - current_equity >= config_.max_drawdown) {
        halted_ = true;
        halt_reason_ = "max_drawdown";
    }
    if (!halted_ && day_start_equity_ - current_equity >= config_.max_daily_loss) {
        halted_ = true;
        halt_reason_ = "max_daily_loss";
    }
}

std::int64_t RiskGuard::position() const noexcept { return position_; }
bool RiskGuard::is_halted() const noexcept { return halted_; }
const std::string &RiskGuard::halt_reason() const noexcept { return halt_reason_; }
double RiskGuard::equity() const noexcept {
    const double unrealized = position_ == 0 || mark_price_ <= 0 ? 0 :
        static_cast<double>(position_) * (mark_price_ - average_entry_price_);
    return config_.initial_equity + realized_pnl_ + unrealized;
}
double RiskGuard::drawdown() const noexcept { return peak_equity_ - equity(); }
double RiskGuard::daily_loss() const noexcept { return std::max(0.0, day_start_equity_ - equity()); }
std::uint64_t RiskGuard::journal_sequence() const noexcept { return journal_sequence_; }
std::uint64_t RiskGuard::replayed_trade_count() const noexcept { return replayed_trade_count_; }
} } // namespace trading::engine_runtime
