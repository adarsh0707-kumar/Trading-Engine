#include "engine/Engine.hpp"

#include "serialization/JsonSerializer.hpp"
#include "utils/Time.hpp"

#include <algorithm>
#include <chrono>
#include <cstring>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <thread>

namespace trading
{
namespace engine_runtime
{

Engine::Engine(const EngineConfig &config)
    : config_(config),
      risk_guard_(RiskGuardConfig{
          config.risk_max_position,
          config.risk_max_position_value}),
      state_(std::make_unique<EngineState>(config.symbol)),
      server_(std::make_unique<network::SocketServer>(
          config.port,
          10000,
          30,
          config.bind_address)),
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

    server_->setMessageHandler(
        [this](
            std::shared_ptr<network::ClientConnection> client,
            const serialization::Message &message)
        {
            handle_book_snapshot(
                std::move(client),
                message);
        });
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

        const RiskDecision risk_decision =
            risk_guard_.check_order(*incoming_order);

        if (!risk_decision.allowed)
        {
            incoming_order->reject();
            logger_->warn(
                "risk_order_rejected order_id=" +
                tick.order_id +
                " symbol=" + tick.symbol +
                " side=" + ::engine::to_string(tick.side) +
                " quantity=" + std::to_string(tick.quantity) +
                " current_position=" + std::to_string(risk_guard_.position()) +
                " reason=" + risk_decision.reason);
            std::this_thread::sleep_for(
                std::chrono::milliseconds(config_.tick_interval_ms));
            continue;
        }

        ::engine::MatchResult result;

        try
        {
            result = state_->match(incoming_order);
        }
        catch (const std::exception &error)
        {
            logger_->warn(
                "Rejected order " +
                tick.order_id +
                ": " +
                error.what());

            continue;
        }

        for (const auto &trade : result.trades)
        {
            risk_guard_.record_trade(
                trade->symbol(),
                trade->taker_side(),
                trade->quantity());

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
                << "\","
                << "\"taker_side\":\""
                << ::engine::to_string(trade->taker_side())
                << "\","
                << "\"buy_order_id\":\""
                << trade->buy_order_id()
                << "\","
                << "\"sell_order_id\":\""
                << trade->sell_order_id()
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

void Engine::handle_book_snapshot(
    std::shared_ptr<network::ClientConnection> client,
    const serialization::Message &request)
{
    if (!client || request.type != serialization::MessageType::BOOK_SNAPSHOT)
    {
        return;
    }

    const ::engine::BookSnapshot snapshot = state_->snapshot();

    serialization::Message response;
    response.type = serialization::MessageType::BOOK_SNAPSHOT;
    response.requestId = request.requestId;
    response.timestamp = utils::Time::iso8601();

    constexpr std::size_t MAX_LEVELS = 20;
    const auto append_levels = [](
        std::ostringstream &payload,
        const auto &levels,
        std::size_t limit)
    {
        payload << "[";
        const std::size_t count = std::min(levels.size(), limit);
        for (std::size_t index = 0; index < count; ++index)
        {
            if (index > 0)
            {
                payload << ",";
            }

            const auto &level = levels[index];
            payload << "{\"price\":"
                    << std::fixed << std::setprecision(8)
                    << level.price
                    << ",\"quantity\":"
                    << level.quantity
                    << "}";
        }
        payload << "]";
    };

    std::ostringstream payload;
    payload << "{\"symbol\":\""
            << config_.symbol
            << "\",\"bids\":";
    append_levels(payload, snapshot.bids, MAX_LEVELS);
    payload << ",\"asks\":";
    append_levels(payload, snapshot.asks, MAX_LEVELS);
    payload << "}";

    response.payload = payload.str();
    client->sendMessage(response);
}

} // namespace engine_runtime
} // namespace trading
