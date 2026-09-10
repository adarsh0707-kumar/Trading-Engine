#pragma once

#include <iostream>
#include <memory>
#include <mutex>
#include <string>

namespace trading
{
namespace logging
{

enum class LogLevel
{
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
};

class Logger
{
public:
    explicit Logger(
        const std::string &name,
        LogLevel level = LogLevel::INFO);

    void debug(const std::string &message);
    void info(const std::string &message);
    void warn(const std::string &message);
    void error(const std::string &message);

private:
    void log(
        LogLevel level,
        const std::string &message);

    std::string name_;
    LogLevel level_;
    mutable std::mutex mutex_;
};

} // namespace logging
} // namespace trading
