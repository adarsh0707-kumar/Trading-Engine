#include "orderbook/OrderBook.hpp"

#include <stdexcept>
#include <utility>

namespace engine
{

    OrderBook::OrderBook(std::string symbol)
        : symbol_(std::move(symbol)),
          bids_(),
          asks_(),
          order_count_(0)
    {
        if (symbol_.empty())
        {
            throw std::invalid_argument("order book symbol cannot be empty");
        }
    }

    const std::string &OrderBook::symbol() const noexcept
    {
        return symbol_;
    }

    std::size_t OrderBook::order_count() const noexcept
    {
        return order_count_;
    }

    std::size_t OrderBook::bid_level_count() const noexcept
    {
        return bids_.size();
    }

    std::size_t OrderBook::ask_level_count() const noexcept
    {
        return asks_.size();
    }

    bool OrderBook::empty() const noexcept
    {
        return order_count_ == 0;
    }

    void OrderBook::add_order(const std::shared_ptr<Order> &order)
    {
        if (!order)
        {
            throw std::invalid_argument(
                "cannot add null order to order book");
        }

        if (!order->is_valid())
        {
            throw std::invalid_argument(
                "cannot add invalid order to order book");
        }

        if (!order->is_active())
        {
            throw std::invalid_argument(
                "cannot add inactive order to order book");
        }

        if (order->symbol() != symbol_)
        {
            throw std::invalid_argument(
                "order symbol does not match order book symbol");
        }

        if (order->price() <= 0.0)
        {
            throw std::invalid_argument(
                "order price must be positive");
        }

        if (order->side() == Side::BUY)
        {
            auto [level_it, inserted] = bids_.try_emplace(
                order->price(),
                order->price());

            level_it->second.add_order(order);
        }
        else if (order->side() == Side::SELL)
        {
            auto [level_it, inserted] = asks_.try_emplace(
                order->price(),
                order->price());

            level_it->second.add_order(order);
        }
        else
        {
            throw std::invalid_argument(
                "unsupported order side");
        }

        ++order_count_;
    }

    double OrderBook::best_bid() const
    {
        if (bids_.empty())
        {
            throw std::out_of_range(
                "cannot get best bid from empty bid book");
        }

        return bids_.begin()->first;
    }

    double OrderBook::best_ask() const
    {
        if (asks_.empty())
        {
            throw std::out_of_range(
                "cannot get best ask from empty ask book");
        }

        return asks_.begin()->first;
    }

    const PriceLevel &OrderBook::best_bid_level() const
    {
        if (bids_.empty())
        {
            throw std::out_of_range(
                "cannot get best bid level from empty bid book");
        }

        return bids_.begin()->second;
    }

    const PriceLevel &OrderBook::best_ask_level() const
    {
        if (asks_.empty())
        {
            throw std::out_of_range(
                "cannot get best ask level from empty ask book");
        }

        return asks_.begin()->second;
    }

    const std::map<double, PriceLevel, std::greater<double>> &
    OrderBook::bids() const noexcept
    {
        return bids_;
    }

    const std::map<double, PriceLevel, std::less<double>> &
    OrderBook::asks() const noexcept
    {
        return asks_;
    }

} // namespace engine