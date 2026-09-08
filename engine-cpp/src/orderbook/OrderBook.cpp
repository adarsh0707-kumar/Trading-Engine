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
            auto result = bids_.try_emplace(
                order->price(),
                order->price());

            result.first->second.add_order(order);
        }
        else if (order->side() == Side::SELL)
        {
            auto result = asks_.try_emplace(
                order->price(),
                order->price());

            result.first->second.add_order(order);
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

    

    PriceLevel &OrderBook::best_bid_level()
    {
        if (bids_.empty())
        {
            throw std::out_of_range(
                "cannot get best bid level from empty bid book");
        }

        return bids_.begin()->second;
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

    

    PriceLevel &OrderBook::best_ask_level()
    {
        if (asks_.empty())
        {
            throw std::out_of_range(
                "cannot get best ask level from empty ask book");
        }

        return asks_.begin()->second;
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

    void OrderBook::remove_best_bid_level()
    {
        if (bids_.empty())
        {
            throw std::out_of_range(
                "cannot remove best bid level from empty bid book");
        }

        if (!bids_.begin()->second.empty())
        {
            throw std::logic_error(
                "cannot remove non-empty best bid level");
        }

        bids_.erase(bids_.begin());

        if (order_count_ == 0)
        {
            throw std::logic_error(
                "order count invariant violated");
        }

        --order_count_;
    }

    void OrderBook::remove_best_ask_level()
    {
        if (asks_.empty())
        {
            throw std::out_of_range(
                "cannot remove best ask level from empty ask book");
        }

        if (!asks_.begin()->second.empty())
        {
            throw std::logic_error(
                "cannot remove non-empty best ask level");
        }

        asks_.erase(asks_.begin());

        if (order_count_ == 0)
        {
            throw std::logic_error(
                "order count invariant violated");
        }

        --order_count_;
    }

    void OrderBook::remove_filled_best_ask_order()
    {
        if (asks_.empty())
        {
            throw std::out_of_range(
                "cannot remove filled ask order from empty book");
        }

        PriceLevel &level = asks_.begin()->second;

        if (level.empty())
        {
            throw std::logic_error(
                "cannot remove filled ask order from empty price level");
        }

        if (!level.front()->is_fully_filled())
        {
            throw std::logic_error(
                "cannot remove partially filled ask order");
        }

        level.remove_front();

        if (order_count_ == 0)
        {
            throw std::logic_error(
                "order count underflow while removing ask order");
        }

        --order_count_;

        if (level.empty())
        {
            asks_.erase(asks_.begin());
        }
    }

    void OrderBook::remove_filled_best_bid_order()
    {
        if (bids_.empty())
        {
            throw std::out_of_range(
                "cannot remove filled bid order from empty book");
        }

        PriceLevel &level = bids_.begin()->second;

        if (level.empty())
        {
            throw std::logic_error(
                "cannot remove filled bid order from empty price level");
        }

        if (!level.front()->is_fully_filled())
        {
            throw std::logic_error(
                "cannot remove partially filled bid order");
        }

        level.remove_front();

        if (order_count_ == 0)
        {
            throw std::logic_error(
                "order count underflow while removing bid order");
        }

        --order_count_;

        if (level.empty())
        {
            bids_.erase(bids_.begin());
        }
    }

    bool OrderBook::cancel_order(const std::string &order_id)
    {
        if (order_id.empty())
        {
            throw std::invalid_argument(
                "cannot cancel order with empty order id");
        }

        for (auto level_it = bids_.begin();
             level_it != bids_.end();
             ++level_it)
        {
            PriceLevel &level = level_it->second;

            if (level.cancel_order(order_id))
            {
                if (order_count_ == 0)
                {
                    throw std::logic_error(
                        "order count underflow during bid cancellation");
                }

                --order_count_;

                if (level.empty())
                {
                    bids_.erase(level_it);
                }

                return true;
            }
        }

        for (auto level_it = asks_.begin();
             level_it != asks_.end();
             ++level_it)
        {
            PriceLevel &level = level_it->second;

            if (level.cancel_order(order_id))
            {
                if (order_count_ == 0)
                {
                    throw std::logic_error(
                        "order count underflow during ask cancellation");
                }

                --order_count_;

                if (level.empty())
                {
                    asks_.erase(level_it);
                }

                return true;
            }
        }

        return false;
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
