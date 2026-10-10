#include "engine/Engine.hpp"
#include "engine/EngineConfig.hpp"
#include <csignal>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
static volatile std::sig_atomic_t running=1;
static void signalHandler(int) { running=0; }
int main() {
    std::signal(SIGINT,signalHandler);
    trading::engine_runtime::EngineConfig config;
    config.risk_state_file_path="./data/risk-state.snapshot";
    if(const char *v=std::getenv("ENGINE_BIND_ADDRESS");v&&*v) config.bind_address=v;
    if(const char *v=std::getenv("ENGINE_RISK_STATE_FILE");v&&*v) config.risk_state_file_path=v;\n    if(const char *v=std::getenv("ENGINE_TRADE_JOURNAL_FILE");v&&*v) config.risk_trade_journal_file_path=v;
    if(const char *v=std::getenv("ENGINE_RISK_MAX_POSITION");v&&*v) config.risk_max_position=std::stoll(v);
    if(const char *v=std::getenv("ENGINE_RISK_MAX_POSITION_VALUE");v&&*v) config.risk_max_position_value=std::stod(v);
    if(const char *v=std::getenv("ENGINE_RISK_MAX_DRAWDOWN");v&&*v) config.risk_max_drawdown=std::stod(v);
    if(const char *v=std::getenv("ENGINE_RISK_MAX_DAILY_LOSS");v&&*v) config.risk_max_daily_loss=std::stod(v);
    if(const char *v=std::getenv("ENGINE_RISK_INITIAL_EQUITY");v&&*v) config.risk_initial_equity=std::stod(v);
    config.symbol="SIM"; config.port=9000; config.tick_interval_ms=100; config.market_seed=42;
    config.min_price=95.0; config.max_price=105.0; config.min_quantity=1; config.max_quantity=100;
    try {
        trading::engine_runtime::Engine engine(config);
        const char *resume=std::getenv("ENGINE_RISK_RESUME_AUTHORIZATION");
        if(resume&&std::string(resume)=="I_ACKNOWLEDGE_RISK_HALT") engine.authorize_risk_resume(true);
        if(!engine.start()) { std::cerr<<"Failed to start engine\n"; return 1; }
        std::cout<<"Trading Engine running\nSymbol: "<<config.symbol<<"\nBind: "<<config.bind_address
            <<"\nTransport: "<<config.bind_address<<":"<<engine.port()<<"\nRisk max position: "<<config.risk_max_position
            <<"\nRisk max position value: "<<config.risk_max_position_value<<"\nRisk max drawdown: "<<config.risk_max_drawdown
            <<"\nRisk max daily loss: "<<config.risk_max_daily_loss<<"\nRisk initial equity: "<<config.risk_initial_equity
            <<"\nPress Ctrl+C to stop.\n"<<std::flush;
        while(running&&engine.is_running()) std::this_thread::sleep_for(std::chrono::milliseconds(100));
        engine.stop(); std::cout<<"Engine stopped cleanly.\n";
    } catch(const std::exception &error) {
        std::cerr<<"Engine startup failed closed: "<<error.what()<<"\n"; return 2;
    }
    return 0;
}
