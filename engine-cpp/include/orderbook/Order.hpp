#pragma once

#include <cstdint>
#include <string>

namespace engine
{

    // -- Enumerations (mirrors docs/03-data-model.md §3) -----------------------

    enum class Side
    {
        BUY,
        SELL
    };

    enum class OrderType
    {
        LIMIT,
        MARKET // MVP implements LIMIT only; MARKET is reserved.
    };

    enum class TimeInForce
    {
        GTC, // Good-Til-Cancelled — the only mode the MVP implements.
        IOC  // Immediate-Or-Cancel — reserved for a future phase.
    };

    enum class OrderStatus
    {
        NEW,
        PARTIALLY_FILLED,
        FILLED,
        CANCELLED,
        REJECTED
    };

    std::string to_string(Side side);
    std::string to_string(OrderType type);
    std::string to_string(TimeInForce tif);
    std::string to_string(OrderStatus status);

    // -- Order -------------------------------------------------------------
    //
    // A single resting or incoming limit order. Order owns its own state
    // (remaining quantity, status) but never touches the book or the matching
    // loop directly — those live in OrderBook / MatchingEngine. Keeping this
    // separation is what docs/06-development-guide.md calls "keep I/O and
    // control flow separate from business logic".

    class Order
    {
    public:
        Order(std::string order_id,
              std::string symbol,
              Side side,
              OrderType type,
              double price,
              std::int64_t quantity,
              std::int64_t sequence,
              TimeInForce tif = TimeInForce::GTC);

        // FR-003 / docs/03-data-model.md §4 validation rules:
        //   - price must be positive for a LIMIT order
        //   - quantity must be a positive integer
        // An order that fails validation is constructed already REJECTED
        // rather than throwing, so the caller can still log/emit an
        // ORDER_REJECTED event with the original fields.
        bool is_valid() const;

        const std::string &order_id() const { return order_id_; }
        const std::string &symbol() const { return symbol_; }
        Side side() const { return side_; }
        OrderType type() const { return type_; }
        double price() const { return price_; }
        std::int64_t quantity() const { return quantity_; }
        std::int64_t remaining_quantity() const { return remaining_quantity_; }
        std::int64_t sequence() const { return sequence_; }
        TimeInForce time_in_force() const { return tif_; }
        OrderStatus status() const { return status_; }

        bool is_fully_filled() const { return remaining_quantity_ == 0; }
        bool is_active() const
        {
            return status_ == OrderStatus::NEW ||
                   status_ == OrderStatus::PARTIALLY_FILLED;
        }

        // Mutators — intended to be called only by MatchingEngine/OrderBook,
        // which own the invariant that fill_quantity <= remaining_quantity.
        void fill(std::int64_t fill_quantity);
        void cancel();
        void reject();

    private:
        std::string order_id_;
        std::string symbol_;
        Side side_;
        OrderType type_;
        double price_;
        std::int64_t quantity_;
        std::int64_t remaining_quantity_;
        std::int64_t sequence_;
        TimeInForce tif_;
        OrderStatus status_;
    };

} // namespace engine
