#include "orderbook/Trade.hpp"

#include <stdexcept>
#include <utility>

namespace engine
{

    Trade::Trade(
        std::string trade_id,
        std::string symbol,
        std::string taker_order_id,
        std::string maker_order_id,
        Side taker_side,
        double price,
        std::int64_t quantity)
        : trade_id_(std::move(trade_id)),
          symbol_(std::move(symbol)),
          taker_order_id_(std::move(taker_order_id)),
          maker_order_id_(std::move(maker_order_id)),
          taker_side_(taker_side),
          price_(price),
          quantity_(quantity)
    {
        if (trade_id_.empty())
        {
            throw std::invalid_argument(
                "trade id cannot be empty");
        }

        if (symbol_.empty())
        {
            throw std::invalid_argument(
                "trade symbol cannot be empty");
        }

        if (taker_order_id_.empty())
        {
            throw std::invalid_argument(
                "taker order id cannot be empty");
        }

        if (maker_order_id_.empty())
        {
            throw std::invalid_argument(
                "maker order id cannot be empty");
        }

        if (price_ <= 0.0)
        {
            throw std::invalid_argument(
                "trade price must be positive");
        }

        if (quantity_ <= 0)
        {
            throw std::invalid_argument(
                "trade quantity must be positive");
        }
    }

    const std::string &Trade::trade_id() const noexcept
    {
        return trade_id_;
    }

    const std::string &Trade::symbol() const noexcept
    {
        return symbol_;
    }

    const std::string &Trade::taker_order_id() const noexcept
    {
        return taker_order_id_;
    }

    const std::string &Trade::maker_order_id() const noexcept
    {
        return maker_order_id_;
    }

    Side Trade::taker_side() const noexcept
    {
        return taker_side_;
    }

    const std::string &Trade::buy_order_id() const noexcept
    {
        return taker_side_ == Side::BUY
                   ? taker_order_id_
                   : maker_order_id_;
    }

    const std::string &Trade::sell_order_id() const noexcept
    {
        return taker_side_ == Side::BUY
                   ? maker_order_id_
                   : taker_order_id_;
    }

    double Trade::price() const noexcept
    {
        return price_;
    }

    std::int64_t Trade::quantity() const noexcept
    {
        return quantity_;
    }

    bool Trade::is_valid() const noexcept
    {
        return !trade_id_.empty() && !symbol_.empty() && !taker_order_id_.empty() && !maker_order_id_.empty() && price_ > 0.0 && quantity_ > 0;
    }

} // namespace engine