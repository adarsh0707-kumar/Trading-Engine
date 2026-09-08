#pragma once

#include "orderbook/Order.hpp"

#include <cstddef>
#include <cstdint>
#include <deque>
#include <memory>
#include <string>

namespace engine
{

    class PriceLevel
    {
    public:
        explicit PriceLevel(double price);

        double price() const noexcept;

        std::int64_t total_quantity() const noexcept;

        std::size_t order_count() const noexcept;

        bool empty() const noexcept;

        void add_order(const std::shared_ptr<Order> &order);

        void reduce_quantity(std::int64_t quantity);

        std::shared_ptr<Order> &front();

        const std::shared_ptr<Order> &front() const;

        void remove_front();

        bool cancel_order(const std::string &order_id);

    private:
        double price_;

        std::int64_t total_quantity_;

        std::deque<std::shared_ptr<Order>> orders_;
    };

} // namespace engine