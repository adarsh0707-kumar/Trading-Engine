#pragma once

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
            double price,
            std::int64_t quantity);

        const std::string &trade_id() const noexcept;

        const std::string &symbol() const noexcept;

        const std::string &taker_order_id() const noexcept;

        const std::string &maker_order_id() const noexcept;

        double price() const noexcept;

        std::int64_t quantity() const noexcept;

        bool is_valid() const noexcept;

    private:
        std::string trade_id_;
        std::string symbol_;
        std::string taker_order_id_;
        std::string maker_order_id_;

        double price_;
        std::int64_t quantity_;
    };

} // namespace engine