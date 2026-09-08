#include "market/MarketData.hpp"

#include <utility>

namespace engine
{

MarketData::MarketData(std::vector<Tick> ticks)
    : ticks_(std::move(ticks))
{
}

const std::vector<Tick> &MarketData::ticks() const noexcept
{
    return ticks_;
}

std::size_t MarketData::size() const noexcept
{
    return ticks_.size();
}

bool MarketData::empty() const noexcept
{
    return ticks_.empty();
}

void MarketData::add(const Tick &tick)
{
    ticks_.push_back(tick);
}

} // namespace engine
