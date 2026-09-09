#pragma once

#include "serialization/Message.hpp"

#include <atomic>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace trading
{
namespace network
{

class ClientConnection
    : public std::enable_shared_from_this<ClientConnection>
{
public:
    using MessageHandler =
        std::function<void(
            std::shared_ptr<ClientConnection>,
            const serialization::Message &)>;

    using DisconnectHandler =
        std::function<void(
            std::shared_ptr<ClientConnection>)>;

    ClientConnection(
        int socketFd,
        std::uint64_t connectionId);

    ~ClientConnection();

    ClientConnection(const ClientConnection &) = delete;
    ClientConnection &operator=(
        const ClientConnection &) = delete;

    std::uint64_t id() const;

    int socketFd() const;

    bool sendMessage(
        const serialization::Message &message);

    void start(
        MessageHandler messageHandler,
        DisconnectHandler disconnectHandler);

    void stop();

    bool isRunning() const;

private:
    void receiveLoop();

    bool sendAll(
        const std::vector<std::uint8_t> &data);

    bool receiveSome();

    int socketFd_;
    std::uint64_t connectionId_;

    std::atomic<bool> running_{false};

    std::mutex sendMutex_;

    std::vector<std::uint8_t> receiveBuffer_;

    MessageHandler messageHandler_;
    DisconnectHandler disconnectHandler_;
};

} // namespace network
} // namespace trading
