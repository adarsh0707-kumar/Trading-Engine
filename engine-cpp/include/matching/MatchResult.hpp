#pragma once

#include "orderbook/Trade.hpp"

#include <memory>
#include <vector>

namespace engine
{

    struct MatchResult
    {
        bool matched{false};
        std::vector<std::shared_ptr<Trade>> trades;
    };

} // namespace engine