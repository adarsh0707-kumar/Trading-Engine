#pragma once

#include "matching/MatchResult.hpp"
#include "orderbook/OrderBook.hpp"

#include <atomic>
#include <cstdint>
#include <memory>
#include <string>

namespace engine
{

    class MatchingEngine
    {
    public:
        MatchResult match(
            OrderBook &order_book,
            const std::shared_ptr<Order> &incoming_order) const;

    private:
        std::string next_trade_id(
            const std::string &taker_order_id,
            const std::string &maker_order_id) const;

        mutable std::atomic<std::uint64_t> trade_sequence_{0};
    };

} // namespace engine