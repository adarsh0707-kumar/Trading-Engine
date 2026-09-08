#include "orderbook/Order.hpp"

#include <stdexcept>

namespace engine
{

    std::string to_string(Side side)
    {
        switch (side)
        {
        case Side::BUY:
            return "BUY";
        case Side::SELL:
            return "SELL";
        }
        return "UNKNOWN";
    }

    std::string to_string(OrderType type)
    {
        switch (type)
        {
        case OrderType::LIMIT:
            return "LIMIT";
        case OrderType::MARKET:
            return "MARKET";
        }
        return "UNKNOWN";
    }

    std::string to_string(TimeInForce tif)
    {
        switch (tif)
        {
        case TimeInForce::GTC:
            return "GTC";
        case TimeInForce::IOC:
            return "IOC";
        }
        return "UNKNOWN";
    }

    std::string to_string(OrderStatus status)
    {
        switch (status)
        {
        case OrderStatus::NEW:
            return "NEW";
        case OrderStatus::PARTIALLY_FILLED:
            return "PARTIALLY_FILLED";
        case OrderStatus::FILLED:
            return "FILLED";
        case OrderStatus::CANCELLED:
            return "CANCELLED";
        case OrderStatus::REJECTED:
            return "REJECTED";
        }
        return "UNKNOWN";
    }

    Order::Order(std::string order_id,
                 std::string symbol,
                 Side side,
                 OrderType type,
                 double price,
                 std::int64_t quantity,
                 std::int64_t sequence,
                 TimeInForce tif)
        : order_id_(std::move(order_id)),
          symbol_(std::move(symbol)),
          side_(side),
          type_(type),
          price_(price),
          quantity_(quantity),
          remaining_quantity_(quantity),
          sequence_(sequence),
          tif_(tif),
          status_(OrderStatus::NEW)
    {
        // Validate at construction time. An invalid order still exists as an
        // object (so the caller can emit ORDER_REJECTED with its fields) but
        // starts life REJECTED rather than NEW, so it can never enter the book.
        if (!is_valid())
        {
            status_ = OrderStatus::REJECTED;
        }
    }

    bool Order::is_valid() const
    {
        if (order_id_.empty() || symbol_.empty())
        {
            return false;
        }
        if (quantity_ <= 0)
        {
            return false;
        }
        if (type_ == OrderType::LIMIT && price_ <= 0.0)
        {
            return false;
        }
        return true;
    }

    void Order::fill(std::int64_t fill_quantity)
    {
        if (!is_active())
        {
            throw std::logic_error("cannot fill an order that is not NEW/PARTIALLY_FILLED");
        }
        if (fill_quantity <= 0 || fill_quantity > remaining_quantity_)
        {
            throw std::invalid_argument("fill quantity must be > 0 and <= remaining_quantity");
        }
        remaining_quantity_ -= fill_quantity;
        status_ = (remaining_quantity_ == 0) ? OrderStatus::FILLED
                                             : OrderStatus::PARTIALLY_FILLED;
    }

    void Order::cancel()
    {
        if (status_ == OrderStatus::FILLED)
        {
            throw std::logic_error("cannot cancel a fully filled order");
        }
        status_ = OrderStatus::CANCELLED;
    }

    void Order::reject()
    {
        status_ = OrderStatus::REJECTED;
    }

} // namespace engine
