#pragma once

#include "matching/MatchingEngine.hpp"
#include "orderbook/BookSnapshot.hpp"
#include "orderbook/OrderBook.hpp"

#include <memory>
#include <mutex>
#include <string>

namespace trading
{
namespace engine_runtime
{

class EngineState
{
public:
    explicit EngineState(const std::string &symbol);

    ::engine::OrderBook &order_book();
    const ::engine::OrderBook &order_book() const;

    const ::engine::MatchingEngine &matching_engine() const;

    ::engine::MatchResult match(
        const std::shared_ptr<::engine::Order> &incoming_order);

    ::engine::BookSnapshot snapshot() const;

private:
    ::engine::OrderBook order_book_;
    ::engine::MatchingEngine matching_engine_;
    mutable std::mutex mutex_;
};

} // namespace engine_runtime
} // namespace trading
