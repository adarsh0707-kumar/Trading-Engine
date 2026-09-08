#pragma once

#include "orderbook/Order.hpp"

#include <cstdint>
#include <string>

namespace engine
{

struct Tick
{
    std::uint64_t sequence;
    std::string order_id;
    std::string symbol;
    Side side;
    OrderType order_type;
    double price;
    std::int64_t quantity;
    TimeInForce time_in_force;

    bool is_valid() const noexcept;
};

} // namespace engine
