#include "engine/RiskGuard.hpp"

#include <cmath>
#include <stdexcept>

namespace trading
{
namespace engine_runtime
{

RiskGuard::RiskGuard(const RiskGuardConfig &config)
    : config_(config)
{
    if (config_.max_position <= 0)
    {
        throw std::invalid_argument("max_position must be positive");
    }
    if (!std::isfinite(config_.max_position_value) ||
        config_.max_position_value <= 0.0)
    {
        throw std::invalid_argument("max_position_value must be finite and positive");
    }
}

RiskDecision RiskGuard::check_order(const ::engine::Order &order) const
{
    RiskDecision decision;
    decision.projected_position = position_;

    if (!order.is_valid() || !order.is_active())
    {
        decision.reason = "order is invalid or inactive";
        return decision;
    }

    if (order.quantity() > config_.max_position)
    {
        decision.reason = "order quantity exceeds max_position";
        return decision;
    }

    const std::int64_t signed_quantity =
        order.side() == ::engine::Side::BUY
            ? order.quantity()
            : -order.quantity();

    const long double projected =
        static_cast<long double>(position_) +
        static_cast<long double>(signed_quantity);

    if (projected > static_cast<long double>(config_.max_position) ||
        projected < -static_cast<long double>(config_.max_position))
    {
        decision.reason = "projected position exceeds max_position";
        decision.projected_position =
            projected > 0
                ? config_.max_position + 1
                : -(config_.max_position + 1);
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

void RiskGuard::record_trade(
    const std::string &symbol,
    ::engine::Side taker_side,
    std::int64_t quantity)
{
    if (symbol.empty())
    {
        throw std::invalid_argument("trade symbol cannot be empty");
    }
    if (quantity <= 0)
    {
        throw std::invalid_argument("trade quantity must be positive");
    }

    const std::int64_t signed_quantity =
        taker_side == ::engine::Side::BUY ? quantity : -quantity;

    const long double next_position =
        static_cast<long double>(position_) +
        static_cast<long double>(signed_quantity);

    if (next_position > static_cast<long double>(config_.max_position) ||
        next_position < -static_cast<long double>(config_.max_position))
    {
        throw std::logic_error("executed trade would violate max_position");
    }

    position_ = static_cast<std::int64_t>(next_position);
}

std::int64_t RiskGuard::position() const noexcept
{
    return position_;
}

} // namespace engine_runtime
} // namespace trading
