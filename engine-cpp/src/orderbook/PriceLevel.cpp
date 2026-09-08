#include "orderbook/PriceLevel.hpp"

#include <stdexcept>

namespace engine
{

    PriceLevel::PriceLevel(double price)
        : price_(price),
          total_quantity_(0),
          orders_()
    {
        if (price <= 0.0)
        {
            throw std::invalid_argument(
                "price level price must be positive");
        }
    }

    double PriceLevel::price() const noexcept
    {
        return price_;
    }

    std::int64_t PriceLevel::total_quantity() const noexcept
    {
        return total_quantity_;
    }

    std::size_t PriceLevel::order_count() const noexcept
    {
        return orders_.size();
    }

    bool PriceLevel::empty() const noexcept
    {
        return orders_.empty();
    }

    void PriceLevel::add_order(
        const std::shared_ptr<Order> &order)
    {
        if (!order)
        {
            throw std::invalid_argument(
                "cannot add null order to price level");
        }

        if (!order->is_valid())
        {
            throw std::invalid_argument(
                "cannot add invalid order to price level");
        }

        if (!order->is_active())
        {
            throw std::invalid_argument(
                "cannot add inactive order to price level");
        }

        if (order->price() != price_)
        {
            throw std::invalid_argument(
                "order price does not match price level");
        }

        orders_.push_back(order);
        total_quantity_ += order->remaining_quantity();
    }

    void PriceLevel::reduce_quantity(std::int64_t quantity)
    {
        if (quantity <= 0)
        {
            throw std::invalid_argument(
                "quantity reduction must be positive");
        }

        if (quantity > total_quantity_)
        {
            throw std::invalid_argument(
                "quantity reduction exceeds price level quantity");
        }

        total_quantity_ -= quantity;
    }

    std::shared_ptr<Order> &PriceLevel::front()
    {
        if (orders_.empty())
        {
            throw std::out_of_range(
                "cannot access front of empty price level");
        }

        return orders_.front();
    }

    const std::shared_ptr<Order> &PriceLevel::front() const
    {
        if (orders_.empty())
        {
            throw std::out_of_range(
                "cannot access front of empty price level");
        }

        return orders_.front();
    }

    void PriceLevel::remove_front()
    {
        if (orders_.empty())
        {
            throw std::out_of_range(
                "cannot remove from empty price level");
        }

        if (!orders_.front()->is_fully_filled())
        {
            throw std::logic_error(
                "cannot remove partially filled order from price level");
        }

        orders_.pop_front();
    }

    bool PriceLevel::cancel_order(const std::string &order_id)
    {
        if (order_id.empty())
        {
            throw std::invalid_argument(
                "cannot cancel order with empty order id");
        }

        for (auto it = orders_.begin(); it != orders_.end(); ++it)
        {
            const auto &order = *it;

            if (!order || order->order_id() != order_id)
            {
                continue;
            }

            if (!order->is_active())
            {
                throw std::logic_error(
                    "cannot cancel inactive order");
            }

            const std::int64_t remaining_quantity =
                order->remaining_quantity();

            order->cancel();

            if (remaining_quantity > total_quantity_)
            {
                throw std::logic_error(
                    "price level quantity underflow during cancellation");
            }

            total_quantity_ -= remaining_quantity;

            orders_.erase(it);

            return true;
        }

        return false;
    }

} // namespace engine