#include "engine/RiskGuard.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace trading
{
namespace engine_runtime
{

RiskGuard::RiskGuard(const RiskGuardConfig &config)
    : config_(config),
      peak_equity_(config.initial_equity),
      day_start_equity_(config.initial_equity)
{
    if (config_.max_position <= 0)
        throw std::invalid_argument("max_position must be positive");
    if (!std::isfinite(config_.max_position_value) || config_.max_position_value <= 0.0)
        throw std::invalid_argument("max_position_value must be finite and positive");
    if (!std::isfinite(config_.max_drawdown) || config_.max_drawdown <= 0.0)
        throw std::invalid_argument("max_drawdown must be finite and positive");
    if (!std::isfinite(config_.max_daily_loss) || config_.max_daily_loss <= 0.0)
        throw std::invalid_argument("max_daily_loss must be finite and positive");
    if (!std::isfinite(config_.initial_equity) || config_.initial_equity <= 0.0)
        throw std::invalid_argument("initial_equity must be finite and positive");

    roll_daily_window(std::chrono::system_clock::now());
}

RiskDecision RiskGuard::check_order(const ::engine::Order &order) const
{
    RiskDecision decision;
    decision.projected_position = position_;

    if (halted_)
    {
        decision.reason = "risk halt active: " + halt_reason_;
        return decision;
    }

    if (!order.is_valid() || !order.is_active() || !std::isfinite(order.price()))
    {
        decision.reason = "order is invalid or inactive";
        return decision;
    }

    const std::int64_t signed_quantity =
        order.side() == ::engine::Side::BUY ? order.quantity() : -order.quantity();
    const long double projected = static_cast<long double>(position_) + signed_quantity;

    if (projected > static_cast<long double>(config_.max_position) ||
        projected < -static_cast<long double>(config_.max_position))
    {
        decision.reason = "projected position exceeds max_position";
        return decision;
    }

    decision.projected_position = static_cast<std::int64_t>(projected);
    decision.projected_position_value =
        std::abs(static_cast<double>(decision.projected_position)) * order.price();

    if (!std::isfinite(decision.projected_position_value) ||
        decision.projected_position_value > config_.max_position_value)
    {
        decision.reason = "projected position value exceeds max_position_value";
        return decision;
    }

    decision.allowed = true;
    return decision;
}

void RiskGuard::update_mark_price(
    double price, std::chrono::system_clock::time_point now)
{
    if (!std::isfinite(price) || price <= 0.0)
        throw std::invalid_argument("mark price must be finite and positive");

    roll_daily_window(now);
    mark_price_ = price;
    evaluate_limits();
}

void RiskGuard::record_trade(
    const std::string &symbol,
    ::engine::Side taker_side,
    std::int64_t quantity,
    double price)
{
    if (symbol.empty())
        throw std::invalid_argument("trade symbol cannot be empty");
    if (quantity <= 0)
        throw std::invalid_argument("trade quantity must be positive");
    if (!std::isfinite(price) || price <= 0.0)
        throw std::invalid_argument("trade price must be finite and positive");

    const std::int64_t signed_quantity =
        taker_side == ::engine::Side::BUY ? quantity : -quantity;
    const long double next_position =
        static_cast<long double>(position_) + signed_quantity;

    if (next_position > static_cast<long double>(config_.max_position) ||
        next_position < -static_cast<long double>(config_.max_position))
        throw std::logic_error("executed trade would violate max_position");

    const std::int64_t old_position = position_;
    const std::int64_t next = static_cast<std::int64_t>(next_position);

    if (old_position == 0 || (old_position > 0) == (signed_quantity > 0))
    {
        const long double old_notional =
            static_cast<long double>(std::abs(old_position)) * average_entry_price_;
        const long double added_notional =
            static_cast<long double>(quantity) * price;
        average_entry_price_ = static_cast<double>(
            (old_notional + added_notional) /
            static_cast<long double>(std::abs(next)));
    }
    else
    {
        const std::int64_t closing_quantity =
            std::min<std::int64_t>(std::abs(old_position), quantity);
        const double pnl_per_unit =
            old_position > 0 ? price - average_entry_price_
                             : average_entry_price_ - price;
        realized_pnl_ += static_cast<double>(closing_quantity) * pnl_per_unit;

        if (next == 0)
            average_entry_price_ = 0.0;
        else if ((next > 0) != (old_position > 0))
            average_entry_price_ = price;
    }

    position_ = next;
    mark_price_ = price;
    evaluate_limits();
}

void RiskGuard::roll_daily_window(std::chrono::system_clock::time_point now) noexcept
{
    const auto seconds = std::chrono::duration_cast<std::chrono::seconds>(
        now.time_since_epoch()).count();
    const std::int64_t day = seconds / 86400;
    if (utc_day_ == -1)
        utc_day_ = day;
    else if (day != utc_day_)
    {
        utc_day_ = day;
        day_start_equity_ = equity();
    }
}

void RiskGuard::evaluate_limits() noexcept
{
    const double current_equity = equity();
    peak_equity_ = std::max(peak_equity_, current_equity);

    if (!halted_ && peak_equity_ - current_equity >= config_.max_drawdown)
    {
        halted_ = true;
        halt_reason_ = "max_drawdown";
    }
    if (!halted_ && day_start_equity_ - current_equity >= config_.max_daily_loss)
    {
        halted_ = true;
        halt_reason_ = "max_daily_loss";
    }
}

std::int64_t RiskGuard::position() const noexcept { return position_; }
bool RiskGuard::is_halted() const noexcept { return halted_; }
const std::string &RiskGuard::halt_reason() const noexcept { return halt_reason_; }
double RiskGuard::equity() const noexcept
{
    const double unrealized = position_ == 0 || mark_price_ <= 0.0
        ? 0.0
        : static_cast<double>(position_) * (mark_price_ - average_entry_price_);
    return config_.initial_equity + realized_pnl_ + unrealized;
}
double RiskGuard::drawdown() const noexcept { return peak_equity_ - equity(); }
double RiskGuard::daily_loss() const noexcept
{
    return std::max(0.0, day_start_equity_ - equity());
}

} // namespace engine_runtime
} // namespace trading
