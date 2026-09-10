#pragma once

#include "engine/EngineConfig.hpp"
#include "engine/EngineState.hpp"
#include "logging/Logger.hpp"
#include "market/MockMarketGenerator.hpp"
#include "network/SocketServer.hpp"

#include <atomic>
#include <memory>
#include <thread>

namespace trading
{
namespace engine_runtime
{

class Engine
{
public:
    explicit Engine(const EngineConfig &config);

    ~Engine();

    Engine(const Engine &) = delete;
    Engine &operator=(const Engine &) = delete;

    bool start();

    void stop();

    bool is_running() const;

    std::uint16_t port() const;

private:
    void run_loop();

    EngineConfig config_;
    std::unique_ptr<EngineState> state_;
    std::unique_ptr<network::SocketServer> server_;
    std::unique_ptr<::engine::MockMarketGenerator> generator_;
    std::unique_ptr<logging::Logger> logger_;

    std::atomic<bool> running_{false};
    std::thread engine_thread_;
};

} // namespace engine_runtime
} // namespace trading
