#include "matching/MatchingEngine.hpp"

#include <algorithm>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>

namespace engine
{

    std::string MatchingEngine::next_trade_id(
        const std::string &taker_order_id,
        const std::string &maker_order_id) const
    {
        /*
         * The taker/maker pair alone does not identify a trade: the same
         * pair matches again whenever a partially filled order trades
         * with the same counterparty, and order identifiers repeat
         * across engine restarts. The sequence number makes every trade
         * identifier unique for the lifetime of the engine.
         */
        std::ostringstream trade_id;

        trade_id
            << "trade-"
            << std::setw(8)
            << std::setfill('0')
            << ++trade_sequence_
            << "-"
            << taker_order_id
            << "-"
            << maker_order_id;

        return trade_id.str();
    }

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
                "only LIMIT orders are supported");
        }

        MatchResult result;

        while (incoming_order->remaining_quantity() > 0)
        {
            if (incoming_order->side() == Side::BUY)
            {
                if (order_book.asks().empty())
                {
                    break;
                }

                const double best_ask_price =
                    order_book.asks().begin()->first;

                if (incoming_order->price() < best_ask_price)
                {
                    break;
                }

                PriceLevel &resting_level =
                    order_book.best_ask_level();

                if (resting_level.empty())
                {
                    break;
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
                    next_trade_id(
                        incoming_order->order_id(),
                        resting_order->order_id());

                auto trade = std::make_shared<Trade>(
                    trade_id,
                    order_book.symbol(),
                    incoming_order->order_id(),
                    resting_order->order_id(),
                    trade_price,
                    trade_quantity);

                incoming_order->fill(trade_quantity);
                resting_order->fill(trade_quantity);

                result.matched = true;
                result.trades.push_back(trade);

                if (resting_order->is_fully_filled())
                {
                    order_book.remove_filled_best_ask_order();
                }
                else
                {
                    resting_level.reduce_quantity(trade_quantity);
                }

                continue;
            }

            if (incoming_order->side() == Side::SELL)
            {
                if (order_book.bids().empty())
                {
                    break;
                }

                const double best_bid_price =
                    order_book.bids().begin()->first;

                if (incoming_order->price() > best_bid_price)
                {
                    break;
                }

                PriceLevel &resting_level =
                    order_book.best_bid_level();

                if (resting_level.empty())
                {
                    break;
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
                    next_trade_id(
                        incoming_order->order_id(),
                        resting_order->order_id());

                auto trade = std::make_shared<Trade>(
                    trade_id,
                    order_book.symbol(),
                    incoming_order->order_id(),
                    resting_order->order_id(),
                    trade_price,
                    trade_quantity);

                incoming_order->fill(trade_quantity);
                resting_order->fill(trade_quantity);

                result.matched = true;
                result.trades.push_back(trade);

                if (resting_order->is_fully_filled())
                {
                    order_book.remove_filled_best_bid_order();
                }
                else
                {
                    resting_level.reduce_quantity(trade_quantity);
                }

                continue;
            }

            throw std::invalid_argument(
                "unsupported incoming order side");
        }

        /*
         * Phase 1.12:
         *
         * Automatically rest any unfilled GTC LIMIT order.
         *
         * A fully filled order has remaining quantity == 0 and
         * therefore is never inserted into the order book.
         *
         * IOC is intentionally not rested because IOC semantics
         * are reserved for a future phase.
         */
        if (incoming_order->remaining_quantity() > 0 &&
            incoming_order->time_in_force() == TimeInForce::GTC)
        {
            order_book.add_order(incoming_order);
        }

        return result;
    }

} // namespace engine
