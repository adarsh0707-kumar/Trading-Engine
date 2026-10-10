#include "engine/RiskGuard.hpp"
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <stdexcept>
namespace trading { namespace engine_runtime {
namespace { constexpr int STATE_VERSION=1; }
RiskGuard::RiskGuard(const RiskGuardConfig &config):config_(config),peak_equity_(config.initial_equity),day_start_equity_(config.initial_equity) {
 if(config_.max_position<=0) throw std::invalid_argument("max_position must be positive");
 if(!std::isfinite(config_.max_position_value)||config_.max_position_value<=0) throw std::invalid_argument("max_position_value must be finite and positive");
 if(!std::isfinite(config_.max_drawdown)||config_.max_drawdown<=0) throw std::invalid_argument("max_drawdown must be finite and positive");
 if(!std::isfinite(config_.max_daily_loss)||config_.max_daily_loss<=0) throw std::invalid_argument("max_daily_loss must be finite and positive");
 if(!std::isfinite(config_.initial_equity)||config_.initial_equity<=0) throw std::invalid_argument("initial_equity must be finite and positive");
 load_state(); if(utc_day_==-1) roll_daily_window(std::chrono::system_clock::now()); save_state();
}
void RiskGuard::load_state() {
 if(config_.state_file_path.empty()) return;
 const std::filesystem::path path(config_.state_file_path); if(!std::filesystem::exists(path)) return;
 std::ifstream in(path); int version=0,halted=0; std::int64_t pos=0,day=-1;
 double avg=0,realized=0,mark=0,peak=0,day_start=0; std::string reason;
 if(!(in>>version>>pos>>avg>>realized>>mark>>peak>>day_start>>day>>halted>>reason)||version!=STATE_VERSION||(halted!=0&&halted!=1)||
 pos>config_.max_position||pos< -config_.max_position||!std::isfinite(avg)||avg<0||
 !std::isfinite(realized)||!std::isfinite(mark)||mark<0||!std::isfinite(peak)||peak<=0||
 !std::isfinite(day_start)||day_start<=0||day<0||(halted==1&&reason=="-"))
 throw std::runtime_error("risk state is corrupt or incompatible; refusing startup");
 std::string extra; if(in>>extra) throw std::runtime_error("risk state has unexpected trailing data; refusing startup");
 position_=pos; average_entry_price_=avg; realized_pnl_=realized; mark_price_=mark; peak_equity_=peak;
 day_start_equity_=day_start; utc_day_=day; halted_=halted==1; halt_reason_=reason=="-"?"":reason;
}
void RiskGuard::save_state() const {
 if(config_.state_file_path.empty()) return;
 const std::filesystem::path path(config_.state_file_path);
 if(!path.parent_path().empty()) std::filesystem::create_directories(path.parent_path());
 const std::filesystem::path temp(path.string()+".tmp");
 { std::ofstream out(temp,std::ios::trunc); if(!out) throw std::runtime_error("cannot open temporary risk-state file");
 out<<STATE_VERSION<<' '<<position_<<' '<<std::setprecision(std::numeric_limits<double>::max_digits10)
 <<average_entry_price_<<' '<<realized_pnl_<<' '<<mark_price_<<' '<<peak_equity_<<' '<<day_start_equity_<<' '
 <<utc_day_<<' '<<(halted_?1:0)<<' '<<(halt_reason_.empty()?"-":halt_reason_)<<'\n'; out.flush();
 if(!out) throw std::runtime_error("failed to flush risk-state snapshot"); }
 std::error_code ec; std::filesystem::rename(temp,path,ec);
 if(ec) { std::filesystem::remove(temp); throw std::runtime_error("cannot atomically replace risk-state snapshot: "+ec.message()); }
}
RiskDecision RiskGuard::check_order(const ::engine::Order &order) const {
 RiskDecision d; d.projected_position=position_;
 if(halted_) { d.reason="risk halt active: "+halt_reason_; return d; }
 if(!order.is_valid()||!order.is_active()||!std::isfinite(order.price())) { d.reason="order is invalid or inactive"; return d; }
 const std::int64_t qty=order.side()==::engine::Side::BUY?order.quantity():-order.quantity();
 const long double projected=static_cast<long double>(position_)+qty;
 if(projected>config_.max_position||projected< -config_.max_position) { d.reason="projected position exceeds max_position"; return d; }
 d.projected_position=static_cast<std::int64_t>(projected);
 d.projected_position_value=std::abs(static_cast<double>(d.projected_position))*order.price();
 if(!std::isfinite(d.projected_position_value)||d.projected_position_value>config_.max_position_value) { d.reason="projected position value exceeds max_position_value"; return d; }
 d.allowed=true; return d;
}
void RiskGuard::update_mark_price(double price,std::chrono::system_clock::time_point now) {
 if(!std::isfinite(price)||price<=0) throw std::invalid_argument("mark price must be finite and positive");
 roll_daily_window(now); mark_price_=price; evaluate_limits(); save_state();
}
void RiskGuard::record_trade(const std::string &symbol,::engine::Side side,std::int64_t quantity,double price) {
 if(symbol.empty()) throw std::invalid_argument("trade symbol cannot be empty");
 if(quantity<=0) throw std::invalid_argument("trade quantity must be positive");
 if(!std::isfinite(price)||price<=0) throw std::invalid_argument("trade price must be finite and positive");
 const std::int64_t signed_qty=side==::engine::Side::BUY?quantity:-quantity;
 const long double projected=static_cast<long double>(position_)+signed_qty;
 if(projected>config_.max_position||projected< -config_.max_position) throw std::logic_error("executed trade would violate max_position");
 const auto old=position_; const auto next=static_cast<std::int64_t>(projected);
 if(old==0||(old>0)==(signed_qty>0)) {
  const long double old_notional=static_cast<long double>(std::abs(old))*average_entry_price_;
  const long double add=static_cast<long double>(quantity)*price;
  average_entry_price_=static_cast<double>((old_notional+add)/static_cast<long double>(std::abs(next)));
 } else {
  const auto closing=std::min<std::int64_t>(std::abs(old),quantity);
  realized_pnl_+=static_cast<double>(closing)*(old>0?price-average_entry_price_:average_entry_price_-price);
  if(next==0) average_entry_price_=0; else if((next>0)!=(old>0)) average_entry_price_=price;
 }
 position_=next; mark_price_=price; evaluate_limits(); save_state();
}
void RiskGuard::resume_after_operator_authorization(bool authorized) {
 if(!authorized) throw std::runtime_error("operator authorization required to resume risk halt");
 if(!halted_) return;
 halted_=false; halt_reason_.clear(); peak_equity_=equity(); day_start_equity_=equity();
 const auto seconds=std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 utc_day_=seconds/86400; save_state();
}
void RiskGuard::roll_daily_window(std::chrono::system_clock::time_point now) noexcept {
 const auto seconds=std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count(); const auto day=seconds/86400;
 if(utc_day_==-1) utc_day_=day; else if(day!=utc_day_) { utc_day_=day; day_start_equity_=equity(); }
}
void RiskGuard::evaluate_limits() noexcept {
 const double e=equity(); peak_equity_=std::max(peak_equity_,e);
 if(!halted_&&peak_equity_-e>=config_.max_drawdown) { halted_=true; halt_reason_="max_drawdown"; }
 if(!halted_&&day_start_equity_-e>=config_.max_daily_loss) { halted_=true; halt_reason_="max_daily_loss"; }
}
std::int64_t RiskGuard::position() const noexcept { return position_; }
bool RiskGuard::is_halted() const noexcept { return halted_; }
const std::string &RiskGuard::halt_reason() const noexcept { return halt_reason_; }
double RiskGuard::equity() const noexcept { const double u=position_==0||mark_price_<=0?0:static_cast<double>(position_)*(mark_price_-average_entry_price_); return config_.initial_equity+realized_pnl_+u; }
double RiskGuard::drawdown() const noexcept { return peak_equity_-equity(); }
double RiskGuard::daily_loss() const noexcept { return std::max(0.0,day_start_equity_-equity()); }
} }
