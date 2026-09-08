#pragma once

#include "orderbook/Order.hpp"
#include "orderbook/PriceLevel.hpp"

#include <cstddef>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace engine
{

    class OrderBook
    {
    public:
        explicit OrderBook(std::string symbol);

        const std::string &symbol() const noexcept;

        std::size_t order_count() const noexcept;
        std::size_t bid_level_count() const noexcept;
        std::size_t ask_level_count() const noexcept;

        bool empty() const noexcept;

        void add_order(const std::shared_ptr<Order> &order);

        double best_bid() const;
        double best_ask() const;

        const PriceLevel &best_bid_level() const;
        const PriceLevel &best_ask_level() const;

        const std::map<double, PriceLevel, std::greater<double>> &bids() const noexcept;
        const std::map<double, PriceLevel, std::less<double>> &asks() const noexcept;

    private:
        std::string symbol_;

        std::map<double, PriceLevel, std::greater<double>> bids_;
        std::map<double, PriceLevel, std::less<double>> asks_;

        std::size_t order_count_;
    };

} // namespace engine