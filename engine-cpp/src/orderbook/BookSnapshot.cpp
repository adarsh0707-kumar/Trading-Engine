#include "orderbook/BookSnapshot.hpp"

namespace engine
{

std::int64_t BookSnapshot::total_bid_quantity() const noexcept
{
    std::int64_t total = 0;

    for (const auto& level : bids)
    {
        total += level.quantity;
    }

    return total;
}

std::int64_t BookSnapshot::total_ask_quantity() const noexcept
{
    std::int64_t total = 0;

    for (const auto& level : asks)
    {
        total += level.quantity;
    }

    return total;
}

bool BookSnapshot::empty() const noexcept
{
    return bids.empty() && asks.empty();
}

} // namespace engine
