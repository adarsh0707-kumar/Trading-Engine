#include "engine/Engine.hpp"

#include "serialization/JsonSerializer.hpp"
#include "utils/Time.hpp"

#include <chrono>
#include <cstring>
#include <iomanip>
#include <memory>
#include <sstream>
#include <thread>

namespace trading
{
namespace engine_runtime
{

Engine::Engine(const EngineConfig &config)
    : config_(config),
      state_(std::make_unique<EngineState>(config.symbol)),
      server_(std::make_unique<network::SocketServer>(config.port)),
      logger_(std::make_unique<logging::Logger>("Engine"))
{
    ::engine::MarketGeneratorConfig gen_config;

    gen_config.seed = config.market_seed;
    gen_config.symbol = config.symbol;
    gen_config.min_price = config.min_price;
    gen_config.max_price = config.max_price;
    gen_config.min_quantity = config.min_quantity;
    gen_config.max_quantity = config.max_quantity;

    generator_ =
        std::make_unique<::engine::MockMarketGenerator>(
            gen_config);
}

Engine::~Engine()
{
    stop();
}

bool Engine::start()
{
    if (running_.exchange(true))
    {
        return false;
    }

    if (!server_->start())
    {
        running_ = false;
        logger_->error("Failed to start SocketServer");
        return false;
    }

    logger_->info(
        "Engine started on port " +
        std::to_string(server_->port()));

    engine_thread_ =
        std::thread(
            &Engine::run_loop,
            this);

    return true;
}

void Engine::stop()
{
    if (!running_.exchange(false))
    {
        return;
    }

    if (engine_thread_.joinable())
    {
        engine_thread_.join();
    }

    server_->stop();

    logger_->info("Engine stopped");
}

bool Engine::is_running() const
{
    return running_.load();
}

std::uint16_t Engine::port() const
{
    return server_->port();
}

void Engine::run_loop()
{
    logger_->info("Engine loop started");

    while (running_)
    {
        const ::engine::Tick tick =
            generator_->next();

        auto incoming_order =
            std::make_shared<::engine::Order>(
                tick.order_id,
                tick.symbol,
                tick.side,
                tick.order_type,
                tick.price,
                tick.quantity,
                static_cast<std::int64_t>(tick.sequence),
                tick.time_in_force);

        if (!incoming_order->is_valid())
        {
            logger_->warn(
                "Skipped invalid order: " +
                tick.order_id);

            continue;
        }

        const ::engine::MatchResult result =
            state_->matching_engine().match(
                state_->order_book(),
                incoming_order);

        for (const auto &trade : result.trades)
        {
            serialization::Message message;

            message.type =
                serialization::MessageType::TRADE;

            message.requestId =
                trade->trade_id();

            message.timestamp =
                utils::Time::iso8601();

            std::ostringstream payload;

            payload
                << "{"
                << "\"symbol\":\"" << trade->symbol()
                << "\","
                << "\"price\":" << std::fixed
                << std::setprecision(2)
                << trade->price()
                << ","
                << "\"quantity\":" << trade->quantity()
                << ","
                << "\"taker_order_id\":\""
                << trade->taker_order_id()
                << "\","
                << "\"maker_order_id\":\""
                << trade->maker_order_id()
                << "\""
                << "}";

            message.payload = payload.str();

            server_->broadcast(message);

            logger_->info(
                "Trade: " +
                trade->symbol() +
                " @ " + std::to_string(trade->price()) +
                " x " + std::to_string(trade->quantity()));
        }

        std::this_thread::sleep_for(
            std::chrono::milliseconds(
                config_.tick_interval_ms));
    }

    logger_->info("Engine loop stopped");
}

} // namespace engine_runtime
} // namespace trading
