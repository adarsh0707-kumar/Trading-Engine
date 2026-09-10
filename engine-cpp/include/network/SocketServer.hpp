#pragma once

#include "network/ClientConnection.hpp"
#include "serialization/Message.hpp"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>

namespace trading
{
namespace network
{

class SocketServer
{
public:
    explicit SocketServer(
        std::uint16_t port = 9000,
        std::uint64_t heartbeat_interval_ms = 10000,
        std::uint64_t heartbeat_timeout_sec = 30);

    ~SocketServer();

    SocketServer(const SocketServer &) = delete;
    SocketServer &operator=(
        const SocketServer &) = delete;

    bool start();

    void stop();

    bool isRunning() const;

    std::uint16_t port() const;

    std::size_t clientCount() const;

    void broadcast(
        const serialization::Message &message);

private:
    void acceptLoop();

    void heartbeatLoop();

    void handleMessage(
        std::shared_ptr<ClientConnection> client,
        const serialization::Message &message);

    void handleDisconnect(
        std::shared_ptr<ClientConnection> client);

    int createListeningSocket();

    std::uint16_t requestedPort_;

    std::uint16_t boundPort_{0};

    int serverFd_{-1};

    std::atomic<bool> running_{false};

    std::thread acceptThread_;
    std::thread heartbeatThread_;

    mutable std::mutex clientsMutex_;

    std::unordered_map<
        std::uint64_t,
        std::shared_ptr<ClientConnection>>
        clients_;

    std::atomic<std::uint64_t> nextConnectionId_{1};

    std::uint64_t heartbeatIntervalMs_;
    std::uint64_t heartbeatTimeoutSec_;
};

} // namespace network
} // namespace trading
