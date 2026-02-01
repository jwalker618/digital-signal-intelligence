//! Benchmarks for graph computations
//!
//! Run with: cargo bench --bench graph_bench

use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};
use dsi_core::graph;

fn generate_graph(n_nodes: usize, n_edges: usize) -> (Vec<String>, Vec<(String, String, f64, String)>) {
    let node_ids: Vec<String> = (0..n_nodes).map(|i| format!("node_{}", i)).collect();
    let edges: Vec<(String, String, f64, String)> = (0..n_edges)
        .map(|i| {
            let src = format!("node_{}", i % n_nodes);
            let tgt = format!("node_{}", (i * 7 + 3) % n_nodes);
            let edge_type = if i % 2 == 0 { "trust" } else { "ownership" };
            (src, tgt, 0.85, edge_type.into())
        })
        .collect();
    (node_ids, edges)
}

fn bench_pagerank(c: &mut Criterion) {
    let mut group = c.benchmark_group("pagerank");

    for size in [100, 500, 1000, 5000] {
        let (nodes, edges) = generate_graph(size, size * 3);
        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            &size,
            |b, _| {
                b.iter(|| {
                    graph::pagerank(
                        nodes.clone(),
                        edges.clone(),
                        0.85,
                        100,
                        0.0001,
                    )
                })
            },
        );
    }
    group.finish();
}

fn bench_risk_propagation(c: &mut Criterion) {
    let mut group = c.benchmark_group("risk_propagation");

    for size in [100, 500, 1000, 5000] {
        let (nodes, edges) = generate_graph(size, size * 3);
        let signal_means: Vec<f64> = (0..size).map(|i| (i % 100) as f64).collect();
        let dep_edges: Vec<(String, String, f64, String)> = edges.iter()
            .map(|(s, t, w, _)| (s.clone(), t.clone(), *w, "dependency".into()))
            .collect();

        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            &size,
            |b, _| {
                b.iter(|| {
                    graph::risk_propagation(
                        nodes.clone(),
                        signal_means.clone(),
                        dep_edges.clone(),
                        3,
                    )
                })
            },
        );
    }
    group.finish();
}

criterion_group!(benches, bench_pagerank, bench_risk_propagation);
criterion_main!(benches);
