#include "matching/MatchingEngine.hpp"

#include <algorithm>
#include <stdexcept>
#include <string>

namespace engine
{

    MatchResult MatchingEngine::match(
        OrderBook &order_book,
        const std::shared_ptr<Order> &incoming_order) const
    {
        if (!incoming_order)
        {
            throw std::invalid_argument(
                "incoming order cannot be null");
        }

        if (!incoming_order->is_valid())
        {
            throw std::invalid_argument(
                "incoming order must be valid");
        }

        if (!incoming_order->is_active())
        {
            throw std::invalid_argument(
                "incoming order must be active");
        }

        if (incoming_order->symbol() != order_book.symbol())
        {
            throw std::invalid_argument(
                "incoming order symbol does not match order book");
        }

        if (incoming_order->type() != OrderType::LIMIT)
        {
            throw std::invalid_argument(
                "only LIMIT orders are supported by Step 1.5");
        }

        MatchResult result;

        // ========================================================
        // Incoming BUY
        // ========================================================

        if (incoming_order->side() == Side::BUY)
        {
            if (order_book.asks().empty())
            {
                return result;
            }

            const double best_ask_price =
                order_book.asks().begin()->first;

            // BUY crosses ASK when BUY price >= ASK price.
            if (incoming_order->price() < best_ask_price)
            {
                return result;
            }

            PriceLevel &resting_level =
                order_book.best_ask_level();

            if (resting_level.empty())
            {
                return result;
            }

            const std::shared_ptr<Order> &resting_order =
                resting_level.front();

            const std::int64_t trade_quantity =
                std::min(
                    incoming_order->remaining_quantity(),
                    resting_order->remaining_quantity());

            const double trade_price =
                resting_order->price();

            const std::string trade_id =
                "trade-" +
                incoming_order->order_id() +
                "-" +
                resting_order->order_id();

            auto trade = std::make_shared<Trade>(
                trade_id,
                order_book.symbol(),
                incoming_order->order_id(),
                resting_order->order_id(),
                trade_price,
                trade_quantity);

            // Apply fills.
            incoming_order->fill(trade_quantity);
            resting_order->fill(trade_quantity);

            // Keep aggregate price-level quantity synchronized.
            resting_level.reduce_quantity(trade_quantity);

            // Remove fully consumed resting order.
            if (resting_order->is_fully_filled())
            {
                resting_level.remove_front();

                if (resting_level.empty())
                {
                    order_book.remove_best_ask_level();
                }
            }

            result.matched = true;
            result.trades.push_back(trade);

            return result;
        }

        // ========================================================
        // Incoming SELL
        // ========================================================

        if (incoming_order->side() == Side::SELL)
        {
            if (order_book.bids().empty())
            {
                return result;
            }

            const double best_bid_price =
                order_book.bids().begin()->first;

            // SELL crosses BID when SELL price <= BID price.
            if (incoming_order->price() > best_bid_price)
            {
                return result;
            }

            PriceLevel &resting_level =
                order_book.best_bid_level();

            if (resting_level.empty())
            {
                return result;
            }

            const std::shared_ptr<Order> &resting_order =
                resting_level.front();

            const std::int64_t trade_quantity =
                std::min(
                    incoming_order->remaining_quantity(),
                    resting_order->remaining_quantity());

            const double trade_price =
                resting_order->price();

            const std::string trade_id =
                "trade-" +
                incoming_order->order_id() +
                "-" +
                resting_order->order_id();

            auto trade = std::make_shared<Trade>(
                trade_id,
                order_book.symbol(),
                incoming_order->order_id(),
                resting_order->order_id(),
                trade_price,
                trade_quantity);

            // Apply fills.
            incoming_order->fill(trade_quantity);
            resting_order->fill(trade_quantity);

            // Keep aggregate price-level quantity synchronized.
            resting_level.reduce_quantity(trade_quantity);

            // Remove fully consumed resting order.
            if (resting_order->is_fully_filled())
            {
                resting_level.remove_front();

                if (resting_level.empty())
                {
                    order_book.remove_best_bid_level();
                }
            }

            result.matched = true;
            result.trades.push_back(trade);

            return result;
        }

        throw std::invalid_argument(
            "unsupported incoming order side");
    }

} // namespace engine