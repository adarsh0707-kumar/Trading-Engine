#include "engine/EngineState.hpp"

namespace trading
{
namespace engine_runtime
{

EngineState::EngineState(const std::string &symbol)
    : order_book_(symbol)
{
}

::engine::OrderBook &EngineState::order_book()
{
    return order_book_;
}

const ::engine::OrderBook &EngineState::order_book() const
{
    return order_book_;
}

const ::engine::MatchingEngine &EngineState::matching_engine() const
{
    return matching_engine_;
}

::engine::MatchResult EngineState::match(
    const std::shared_ptr<::engine::Order> &incoming_order)
{
    std::lock_guard<std::mutex> lock(mutex_);

    return matching_engine_.match(
        order_book_,
        incoming_order);
}

::engine::BookSnapshot EngineState::snapshot() const
{
    std::lock_guard<std::mutex> lock(mutex_);

    return order_book_.snapshot();
}

} // namespace engine_runtime
} // namespace trading
