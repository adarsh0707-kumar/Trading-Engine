#pragma once

#include <chrono>
#include <string>

namespace trading
{
namespace utils
{

class Time
{
public:
    static std::string iso8601();

    static std::chrono::system_clock::time_point now();
};

} // namespace utils
} // namespace trading
