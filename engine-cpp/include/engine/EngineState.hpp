#pragma once

#include "matching/MatchingEngine.hpp"
#include "orderbook/OrderBook.hpp"

#include <memory>
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

private:
    ::engine::OrderBook order_book_;
    ::engine::MatchingEngine matching_engine_;
};

} // namespace engine_runtime
} // namespace trading
