#include "market/Tick.hpp"

#include <cmath>

namespace engine
{

bool Tick::is_valid() const noexcept
{
    return sequence > 0 &&
           !order_id.empty() &&
           !symbol.empty() &&
           order_type == OrderType::LIMIT &&
           std::isfinite(price) &&
           price > 0.0 &&
           quantity > 0 &&
           time_in_force == TimeInForce::GTC;
}

} // namespace engine
