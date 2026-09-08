#pragma once

#include "market/Tick.hpp"

#include <cstddef>
#include <vector>

namespace engine
{

class MarketData
{
public:
    MarketData() = default;

    explicit MarketData(std::vector<Tick> ticks);

    const std::vector<Tick> &ticks() const noexcept;

    std::size_t size() const noexcept;

    bool empty() const noexcept;

    void add(const Tick &tick);

private:
    std::vector<Tick> ticks_;
};

} // namespace engine
