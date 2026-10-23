#include "engine/Engine.hpp"
#include "serialization/JsonSerializer.hpp"
#include "utils/Time.hpp"
#include <algorithm>
#include <chrono>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <thread>
namespace trading { namespace engine_runtime {
Engine::Engine(const EngineConfig &config)
    : config_(config),
      risk_guard_(RiskGuardConfig{config.risk_max_position, config.risk_max_position_value,
          config.risk_max_drawdown, config.risk_max_daily_loss, config.risk_initial_equity,
          config.risk_state_file_path, config.risk_trade_journal_file_path}),
      state_(std::make_unique<EngineState>(config.symbol, risk_guard_.journal_sequence())),
      server_(std::make_unique<network::SocketServer>(config.port, 10000, 30, config.bind_address)),
      logger_(std::make_unique<logging::Logger>("Engine"))
{
    ::engine::MarketGeneratorConfig gen_config;
    gen_config.seed=config.market_seed; gen_config.symbol=config.symbol;
    gen_config.min_price=config.min_price; gen_config.max_price=config.max_price;
    gen_config.min_quantity=config.min_quantity; gen_config.max_quantity=config.max_quantity;
    generator_=std::make_unique<::engine::MockMarketGenerator>(gen_config);
    server_->setMessageHandler([this](std::shared_ptr<network::ClientConnection> client,
        const serialization::Message &message) { handle_book_snapshot(std::move(client), message); });
}
Engine::~Engine() { stop(); }
bool Engine::start() {
    if (running_.exchange(true)) return false;
    if (!server_->start()) { running_=false; logger_->error("Failed to start SocketServer"); return false; }
    logger_->info("Engine started on port "+std::to_string(server_->port()));
    logger_->info("risk_journal_reconciliation replayed_records="+std::to_string(risk_guard_.replayed_trade_count())+
        " last_sequence="+std::to_string(risk_guard_.journal_sequence()));
    engine_thread_=std::thread(&Engine::run_loop,this); return true;
}
void Engine::stop() {
    running_.store(false);
    if (engine_thread_.joinable()) engine_thread_.join();
    server_->stop();
    logger_->info("Engine stopped");
}
bool Engine::is_running() const { return running_.load(); }
bool Engine::is_risk_halted() const { return risk_halted_.load(); }
bool Engine::authorize_risk_resume(bool authorized) {
    risk_guard_.resume_after_operator_authorization(authorized);
    risk_halted_.store(risk_guard_.is_halted());
    return !risk_guard_.is_halted();
}
std::uint16_t Engine::port() const { return server_->port(); }
void Engine::run_loop() {
    logger_->info("Engine loop started");
    bool risk_halt_logged=false;
    const auto log_risk_halt = [this](const std::string &event) {
        const auto &diagnostics = risk_guard_.halt_diagnostics();
        std::ostringstream message;
        message << std::setprecision(17);
        if (diagnostics.triggered) {
            message << event
                    << " reason=" << diagnostics.reason
                    << " trigger_timestamp_ms=" << diagnostics.timestamp_ms
                    << " trigger_equity=" << diagnostics.equity
                    << " trigger_drawdown=" << diagnostics.drawdown
                    << " trigger_daily_loss=" << diagnostics.daily_loss;
        } else {
            message << event
                    << " trigger_diagnostics=unavailable"
                    << " reason=" << risk_guard_.halt_reason()
                    << " current_equity=" << risk_guard_.equity()
                    << " current_drawdown=" << risk_guard_.drawdown()
                    << " current_daily_loss=" << risk_guard_.daily_loss();
        }
        logger_->error(message.str());
    };
    try {
    while (running_) {
        const ::engine::Tick tick=generator_->next();
        auto incoming_order=std::make_shared<::engine::Order>(tick.order_id,tick.symbol,tick.side,
            tick.order_type,tick.price,tick.quantity,static_cast<std::int64_t>(tick.sequence),tick.time_in_force);
        if (!incoming_order->is_valid()) { logger_->warn("Skipped invalid order: "+tick.order_id); continue; }
        risk_guard_.update_mark_price(tick.price);

        const bool risk_halted = risk_guard_.is_halted();
        if (risk_halted) {
            risk_halted_.store(true);
            if (!risk_halt_logged) {
                log_risk_halt("risk_halt_active");
                risk_halt_logged=true;
            }

            // A halted engine may submit only a bounded reducing order. IOC
            // prevents any unfilled remainder from resting in the book.
            incoming_order = std::make_shared<::engine::Order>(
                tick.order_id, tick.symbol, tick.side, tick.order_type,
                tick.price, tick.quantity, static_cast<std::int64_t>(tick.sequence),
                ::engine::TimeInForce::IOC);
        }

        // Market data is independent of order matching and must remain available
        // while risk controls halt trading.
        serialization::Message market_message;
        market_message.type = serialization::MessageType::MARKET_DATA;
        market_message.requestId = "market-" + std::to_string(tick.sequence);
        market_message.timestamp = utils::Time::iso8601();
        std::ostringstream market_payload;
        market_payload << "{\"symbol\":\"" << tick.symbol
            << "\",\"price\":" << std::fixed << std::setprecision(8) << tick.price
            << ",\"sequence\":" << tick.sequence << "}";
        market_message.payload = market_payload.str();
        server_->broadcast(market_message);
        const RiskDecision decision=risk_guard_.check_order(*incoming_order);
        if (!decision.allowed) {
            incoming_order->reject();
            logger_->warn("risk_order_rejected order_id="+tick.order_id+" symbol="+tick.symbol+
                " side="+::engine::to_string(tick.side)+" quantity="+std::to_string(tick.quantity)+
                " current_position="+std::to_string(risk_guard_.position())+" reason="+decision.reason);
            std::this_thread::sleep_for(std::chrono::milliseconds(config_.tick_interval_ms)); continue;
        }
        if (risk_halted) {
            logger_->info("risk_halt_reducing_order_allowed order_id=" + tick.order_id +
                " side=" + ::engine::to_string(tick.side) +
                " quantity=" + std::to_string(tick.quantity) +
                " current_position=" + std::to_string(risk_guard_.position()));
        }
        ::engine::MatchResult result;
        try { result=state_->match(incoming_order); }
        catch (const std::exception &error) { logger_->warn("Rejected order "+tick.order_id+": "+error.what()); continue; }
        for (const auto &trade:result.trades) {
            risk_guard_.record_trade(trade->symbol(),trade->taker_side(),trade->quantity(),trade->price(),
                trade->trade_id(),trade->taker_order_id(),trade->maker_order_id());
            if (risk_guard_.is_halted()) {
                risk_halted_.store(true);
                if (!risk_halt_logged) {
                    log_risk_halt("risk_halt_triggered");
                    risk_halt_logged=true;
                }
            }
            serialization::Message message;
            message.type=serialization::MessageType::TRADE; message.requestId=trade->trade_id(); message.timestamp=utils::Time::iso8601();
            std::ostringstream payload;
            payload<<"{\"symbol\":\""<<trade->symbol()<<"\",\"price\":"<<std::fixed<<std::setprecision(2)<<trade->price()
                <<",\"quantity\":"<<trade->quantity()<<",\"taker_order_id\":\""<<trade->taker_order_id()
                <<"\",\"maker_order_id\":\""<<trade->maker_order_id()<<"\",\"taker_side\":\""<<::engine::to_string(trade->taker_side())
                <<"\",\"buy_order_id\":\""<<trade->buy_order_id()<<"\",\"sell_order_id\":\""<<trade->sell_order_id()<<"\"}";
            message.payload=payload.str(); server_->broadcast(message);
            logger_->info("Trade: "+trade->symbol()+" @ "+std::to_string(trade->price())+" x "+std::to_string(trade->quantity()));
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(config_.tick_interval_ms));
    }
    } catch (const std::exception &error) {
        logger_->error(std::string("engine_loop_fatal; stopping engine fail-closed: ") + error.what());
        running_.store(false);
        server_->stop();
    } catch (...) {
        logger_->error("engine_loop_fatal; stopping engine after unknown failure");
        running_.store(false);
        server_->stop();
    }
    logger_->info("Engine loop stopped");
}
void Engine::handle_book_snapshot(std::shared_ptr<network::ClientConnection> client,const serialization::Message &request) {
    if (!client || request.type!=serialization::MessageType::BOOK_SNAPSHOT) return;
    const ::engine::BookSnapshot snapshot=state_->snapshot();
    serialization::Message response; response.type=serialization::MessageType::BOOK_SNAPSHOT;
    response.requestId=request.requestId; response.timestamp=utils::Time::iso8601();
    constexpr std::size_t MAX_LEVELS=20;
    const auto append_levels=[](std::ostringstream &out,const auto &levels,std::size_t limit) {
        out<<"["; const std::size_t count=std::min(levels.size(),limit);
        for (std::size_t i=0;i<count;++i) { if(i>0) out<<","; const auto &level=levels[i];
            out<<"{\"price\":"<<std::fixed<<std::setprecision(8)<<level.price<<",\"quantity\":"<<level.quantity<<"}"; }
        out<<"]";
    };
    std::ostringstream payload; payload<<"{\"symbol\":\""<<config_.symbol<<"\",\"bids\":";
    append_levels(payload,snapshot.bids,MAX_LEVELS); payload<<",\"asks\":"; append_levels(payload,snapshot.asks,MAX_LEVELS);
    payload<<"}"; response.payload=payload.str(); client->sendMessage(response);
}
} }
