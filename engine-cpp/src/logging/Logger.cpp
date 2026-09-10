#include "logging/Logger.hpp"

#include "utils/Time.hpp"

#include <chrono>
#include <iomanip>
#include <sstream>

namespace trading
{
namespace logging
{

static const char *levelToString(LogLevel level)
{
    switch (level)
    {
    case LogLevel::DEBUG:
        return "DEBUG";
    case LogLevel::INFO:
        return "INFO";
    case LogLevel::WARN:
        return "WARN";
    case LogLevel::ERROR:
        return "ERROR";
    default:
        return "UNKNOWN";
    }
}

Logger::Logger(
    const std::string &name,
    LogLevel level)
    : name_(name),
      level_(level)
{
}

void Logger::debug(const std::string &message)
{
    if (level_ <= LogLevel::DEBUG)
    {
        log(LogLevel::DEBUG, message);
    }
}

void Logger::info(const std::string &message)
{
    if (level_ <= LogLevel::INFO)
    {
        log(LogLevel::INFO, message);
    }
}

void Logger::warn(const std::string &message)
{
    if (level_ <= LogLevel::WARN)
    {
        log(LogLevel::WARN, message);
    }
}

void Logger::error(const std::string &message)
{
    if (level_ <= LogLevel::ERROR)
    {
        log(LogLevel::ERROR, message);
    }
}

void Logger::log(
    LogLevel level,
    const std::string &message)
{
    std::lock_guard<std::mutex> lock(mutex_);

    std::cerr
        << "["
        << utils::Time::iso8601()
        << "] ["
        << name_
        << "] "
        << levelToString(level)
        << " : "
        << message
        << "\n";
}

} // namespace logging
} // namespace trading
