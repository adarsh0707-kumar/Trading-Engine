#include "engine/Engine.hpp"
#include "engine/EngineConfig.hpp"

#include <csignal>
#include <cstdlib>
#include <iostream>
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
