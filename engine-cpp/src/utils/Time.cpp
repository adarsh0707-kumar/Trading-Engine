#include "utils/Time.hpp"

#include <iomanip>
#include <sstream>

namespace trading
{
namespace utils
{

std::string Time::iso8601()
{
    const auto now = std::chrono::system_clock::now();
    const auto time_t_now =
        std::chrono::system_clock::to_time_t(now);

    std::ostringstream oss;

    oss << std::put_time(
        std::gmtime(&time_t_now),
        "%Y-%m-%dT%H:%M:%SZ");

    return oss.str();
}

std::chrono::system_clock::time_point Time::now()
{
    return std::chrono::system_clock::now();
}

} // namespace utils
} // namespace trading
