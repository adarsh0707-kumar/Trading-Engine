#pragma once

#include "orderbook/Order.hpp"
#include "orderbook/PriceLevel.hpp"

#include <cstddef>
#include <functional>
#include <map>
#include <memory>
#include <string>

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

        void add_order(
            const std::shared_ptr<Order> &order);

        double best_bid() const;

        double best_ask() const;

        PriceLevel &best_bid_level();

        const PriceLevel &best_bid_level() const;

        PriceLevel &best_ask_level();

        const PriceLevel &best_ask_level() const;

        void remove_best_bid_level();

        void remove_best_ask_level();

        void remove_filled_best_ask_order();
        void remove_filled_best_bid_order();

        const std::map<double, PriceLevel, std::greater<double>> &
        bids() const noexcept;

        const std::map<double, PriceLevel, std::less<double>> &
        asks() const noexcept;

    private:
        std::string symbol_;

        /*
         * BUY prices are ordered from highest to lowest.
         *
         * Example:
         *
         * 105.00
         * 103.00
         * 101.00
         */
        std::map<double, PriceLevel, std::greater<double>> bids_;

        /*
         * SELL prices are ordered from lowest to highest.
         *
         * Example:
         *
         * 106.00
         * 108.00
         * 110.00
         */
        std::map<double, PriceLevel, std::less<double>> asks_;

        std::size_t order_count_;
    };

} // namespace engine