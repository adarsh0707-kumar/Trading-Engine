#pragma once

#include <cstdint>
#include <vector>

namespace engine
{

struct PriceLevelSnapshot
{
    double price;
    std::int64_t quantity;
};

struct BookSnapshot
{
    std::vector<PriceLevelSnapshot> bids;
    std::vector<PriceLevelSnapshot> asks;

    std::int64_t total_bid_quantity() const noexcept;
    std::int64_t total_ask_quantity() const noexcept;

    bool empty() const noexcept;
};

} // namespace engine
