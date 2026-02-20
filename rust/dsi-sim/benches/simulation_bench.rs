//! DSI Simulation Benchmarks
//!
//! Benchmarks for portfolio simulation performance.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use dsi_sim::{
    portfolio::{Entity, PortfolioSnapshot, Signal},
    shock::ShockParameter,
    simulation::Simulator,
};

fn create_portfolio(size: usize) -> PortfolioSnapshot {
    let mut snapshot = PortfolioSnapshot::new();

    for i in 0..size {
        snapshot.entities.push(Entity {
            entity_id: format!("entity_{}", i),
            entity_name: format!("Test Corp {}", i),
            coverage: "cyber".to_string(),
            configuration: "cyber_general".to_string(),
            industry: if i % 3 == 0 { "Technology" }
                else if i % 3 == 1 { "Healthcare" }
                else { "Financial" }.to_string(),
            country: "US".to_string(),
            composite_score: 300.0 + (i as f64 * 700.0 / size as f64),
            tier: ((i * 5 / size) + 1).min(5) as u8,
            premium: 10_000.0 + (i as f64 * 100.0),
            signals: vec![
                Signal {
                    signal_id: "tls_configuration".to_string(),
                    score: 30.0 + (i as f64 * 70.0 / size as f64),
                    weight: 0.15,
                    group_id: "tech".to_string(),
                    confidence: 1.0,
                },
                Signal {
                    signal_id: "security_headers".to_string(),
                    score: 40.0 + (i as f64 * 60.0 / size as f64),
                    weight: 0.10,
                    group_id: "tech".to_string(),
                    confidence: 1.0,
                },
                Signal {
                    signal_id: "financial_stability".to_string(),
                    score: 50.0 + (i as f64 * 50.0 / size as f64),
                    weight: 0.20,
                    group_id: "governance".to_string(),
                    confidence: 1.0,
                },
            ],
            modifiers: vec![],
            limit: 1_000_000.0,
            deductible: 10_000.0,
            product_type: "standard".to_string(),
        });
    }

    snapshot.refresh_metadata();
    snapshot
}

fn benchmark_simulation_sizes(c: &mut Criterion) {
    let mut group = c.benchmark_group("simulation_by_portfolio_size");

    for size in [100, 1000, 10_000].iter() {
        let portfolio = create_portfolio(*size);
        let mut sim = Simulator::new();
        sim.load_portfolio(portfolio);

        let shock = ShockParameter::signal_override("tls_configuration", 20.0);

        group.bench_with_input(
            BenchmarkId::new("portfolio", size),
            size,
            |b, _| {
                b.iter(|| {
                    sim.run_simulation(black_box(&shock), 1).unwrap()
                })
            },
        );
    }

    group.finish();
}

fn benchmark_filtered_vs_unfiltered(c: &mut Criterion) {
    let portfolio = create_portfolio(10_000);
    let mut sim = Simulator::new();
    sim.load_portfolio(portfolio);

    let mut group = c.benchmark_group("filtered_vs_unfiltered");

    // Unfiltered shock (affects all)
    let unfiltered = ShockParameter::signal_override("tls_configuration", 20.0);
    group.bench_function("unfiltered_10k", |b| {
        b.iter(|| {
            sim.run_simulation(black_box(&unfiltered), 1).unwrap()
        })
    });

    // Filtered shock (affects ~33%)
    let mut filtered = ShockParameter::signal_override("tls_configuration", 20.0);
    filtered.filter_industry("Technology");
    group.bench_function("filtered_tech_10k", |b| {
        b.iter(|| {
            sim.run_simulation(black_box(&filtered), 1).unwrap()
        })
    });

    group.finish();
}

fn benchmark_multi_shock(c: &mut Criterion) {
    let portfolio = create_portfolio(5000);
    let mut sim = Simulator::new();
    sim.load_portfolio(portfolio);

    let mut group = c.benchmark_group("multi_shock");

    // Single shock
    let single_shock = ShockParameter::signal_multiplier("tls_configuration", 0.5);
    group.bench_function("single_shock_5k", |b| {
        b.iter(|| {
            sim.run_simulation(black_box(&single_shock), 1).unwrap()
        })
    });

    // Multiple shocks
    let multi_shocks = vec![
        ShockParameter::signal_multiplier("tls_configuration", 0.5),
        ShockParameter::signal_multiplier("security_headers", 0.6),
        ShockParameter::signal_multiplier("financial_stability", 0.7),
    ];
    group.bench_function("triple_shock_5k", |b| {
        b.iter(|| {
            sim.run_multi_shock_simulation(black_box(&multi_shocks)).unwrap()
        })
    });

    group.finish();
}

criterion_group!(
    benches,
    benchmark_simulation_sizes,
    benchmark_filtered_vs_unfiltered,
    benchmark_multi_shock,
);
criterion_main!(benches);
