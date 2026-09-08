#pragma once

#include "matching/MatchResult.hpp"
#include "orderbook/OrderBook.hpp"

#include <memory>

namespace engine
{

    class MatchingEngine
    {
    public:
        MatchResult match(
            OrderBook &order_book,
            const std::shared_ptr<Order> &incoming_order) const;
    };

} // namespace engine