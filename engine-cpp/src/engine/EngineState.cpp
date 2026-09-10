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

} // namespace engine_runtime
} // namespace trading
