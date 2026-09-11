#pragma once

#include "orderbook/Order.hpp"

#include <cstdint>
#include <string>

namespace engine
{

    class Trade
    {
    public:
        Trade(
            std::string trade_id,
            std::string symbol,
            std::string taker_order_id,
            std::string maker_order_id,
            Side taker_side,
            double price,
            std::int64_t quantity);

        const std::string &trade_id() const noexcept;

        const std::string &symbol() const noexcept;

        const std::string &taker_order_id() const noexcept;

        const std::string &maker_order_id() const noexcept;

        Side taker_side() const noexcept;

        const std::string &buy_order_id() const noexcept;

        const std::string &sell_order_id() const noexcept;

        double price() const noexcept;

        std::int64_t quantity() const noexcept;

        bool is_valid() const noexcept;

    private:
        std::string trade_id_;
        std::string symbol_;
        std::string taker_order_id_;
        std::string maker_order_id_;
        Side taker_side_;

        double price_;
        std::int64_t quantity_;
    };

} // namespace engine