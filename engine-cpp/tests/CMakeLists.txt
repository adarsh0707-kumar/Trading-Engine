add_executable(
    test_market_pipeline
    integration/test_market_pipeline.cpp
)

target_link_libraries(
    test_market_pipeline
    PRIVATE
    engine_core
)

add_test(
    NAME market_pipeline
    COMMAND test_market_pipeline
)