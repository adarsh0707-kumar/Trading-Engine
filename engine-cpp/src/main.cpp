#include "engine/Engine.hpp"
#include "engine/EngineConfig.hpp"

#include <csignal>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <thread>

static volatile std::sig_atomic_t running = 1;

static void signalHandler(int)
{
    running = 0;
}

int main()
{
    std::signal(
        SIGINT,
        signalHandler);

    trading::engine_runtime::EngineConfig config;

    if (const char *bind_address = std::getenv("ENGINE_BIND_ADDRESS");
        bind_address != nullptr && *bind_address != '\0')
    {
        config.bind_address = bind_address;
    }

    if (const char *max_position = std::getenv("ENGINE_RISK_MAX_POSITION");
        max_position != nullptr && *max_position != '\0')
    {
        config.risk_max_position = std::stoll(max_position);
    }

    if (const char *max_position_value = std::getenv("ENGINE_RISK_MAX_POSITION_VALUE");
        max_position_value != nullptr && *max_position_value != '\0')
    {
        config.risk_max_position_value = std::stod(max_position_value);
    }

    if (const char *max_drawdown = std::getenv("ENGINE_RISK_MAX_DRAWDOWN");
        max_drawdown != nullptr && *max_drawdown != '\0')
    {
        config.risk_max_drawdown = std::stod(max_drawdown);
    }

    if (const char *max_daily_loss = std::getenv("ENGINE_RISK_MAX_DAILY_LOSS");
        max_daily_loss != nullptr && *max_daily_loss != '\0')
    {
        config.risk_max_daily_loss = std::stod(max_daily_loss);
    }

    if (const char *initial_equity = std::getenv("ENGINE_RISK_INITIAL_EQUITY");
        initial_equity != nullptr && *initial_equity != '\0')
    {
        config.risk_initial_equity = std::stod(initial_equity);
    }

    config.symbol = "SIM";
    config.port = 9000;
    config.tick_interval_ms = 100;
    config.market_seed = 42;
    config.min_price = 95.0;
    config.max_price = 105.0;
    config.min_quantity = 1;
    config.max_quantity = 100;

    trading::engine_runtime::Engine engine(config);

    if (!engine.start())
    {
        std::cerr
            << "Failed to start engine\n";

        return 1;
    }

    std::cout
        << "Trading Engine running\n"
        << "Symbol: " << config.symbol << "\n"
        << "Bind: " << config.bind_address << "\n"
        << "Transport: " << config.bind_address << ":" << engine.port() << "\n"
        << "Risk max position: " << config.risk_max_position << "\n"
        << "Risk max position value: " << config.risk_max_position_value << "\n"
        << "Risk max drawdown: " << config.risk_max_drawdown << "\n"
        << "Risk max daily loss: " << config.risk_max_daily_loss << "\n"
        << "Risk initial equity: " << config.risk_initial_equity << "\n"
        << "Press Ctrl+C to stop.\n"
        << std::flush;

    while (running && engine.is_running())
    {
        std::this_thread::sleep_for(
            std::chrono::milliseconds(100));
    }

    engine.stop();

    std::cout
        << "Engine stopped cleanly.\n";

    return 0;
}
