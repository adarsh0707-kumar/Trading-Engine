#pragma once

#include "orderbook/BookSnapshot.hpp"
#include "orderbook/Order.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <string>

namespace trading
{
namespace engine_runtime
{

// Construct an IOC reduction order using only currently visible opposing liquidity.
// The caller must still pass the returned order through RiskGuard before matching.
inline std::shared_ptr<::engine::Order> make_risk_reduction_order(
    const ::engine::BookSnapshot &book,
    std::int64_t position,
    const std::string &order_id,
    const std::string &symbol,
    std::int64_t requested_quantity,
    std::int64_t sequence)
{
    if (position == 0 || order_id.empty() || symbol.empty() ||
        requested_quantity <= 0)
    {
        return nullptr;
    }

    ::engine::Side side;
    const ::engine::PriceLevelSnapshot *opposing_level = nullptr;

    if (position > 0)
    {
        side = ::engine::Side::SELL;
        if (!book.bids.empty())
        {
            opposing_level = &book.bids.front();
        }
    }
    else
    {
        side = ::engine::Side::BUY;
        if (!book.asks.empty())
        {
            opposing_level = &book.asks.front();
        }
    }

    if (opposing_level == nullptr ||
        !std::isfinite(opposing_level->price) ||
        opposing_level->price <= 0.0 ||
        opposing_level->quantity <= 0)
    {
        return nullptr;
    }

    const std::int64_t max_reducible =
        position > 0
            ? position
            : (position == std::numeric_limits<std::int64_t>::min()
                   ? std::numeric_limits<std::int64_t>::max()
                   : -position);

    const std::int64_t quantity = std::min(
        {requested_quantity, max_reducible, opposing_level->quantity});

    if (quantity <= 0)
    {
        return nullptr;
    }

    return std::make_shared<::engine::Order>(
        order_id,
        symbol,
        side,
        ::engine::OrderType::LIMIT,
        opposing_level->price,
        quantity,
        sequence,
        ::engine::TimeInForce::IOC);
}

} // namespace engine_runtime
} // namespace trading
