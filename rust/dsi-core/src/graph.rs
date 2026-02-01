//! Graph computations - PageRank, risk propagation, exposure aggregation
//!
//! Rust implementation of the graph propagation algorithms from
//! signal_architecture/graph/propagation/algorithms.py
//!
//! Target: 10-50x speedup over Python for large graphs.

use pyo3::prelude::*;
use std::collections::HashMap;

/// A node in the organisational graph (Python-visible)
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyNode {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub node_type: String,
    #[pyo3(get, set)]
    pub signal_mean: f64,
}

#[pymethods]
impl PyNode {
    #[new]
    fn new(id: String, node_type: String, signal_mean: f64) -> Self {
        PyNode { id, node_type, signal_mean }
    }
}

/// An edge in the organisational graph (Python-visible)
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyEdge {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub edge_type: String,
    #[pyo3(get, set)]
    pub source_id: String,
    #[pyo3(get, set)]
    pub target_id: String,
    #[pyo3(get, set)]
    pub weight: f64,
}

#[pymethods]
impl PyEdge {
    #[new]
    fn new(id: String, edge_type: String, source_id: String, target_id: String, weight: f64) -> Self {
        PyEdge { id, edge_type, source_id, target_id, weight }
    }
}

/// Graph container for Rust computations (Python-visible)
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyGraph {
    pub nodes: HashMap<String, PyNode>,
    pub edges: HashMap<String, PyEdge>,
}

#[pymethods]
impl PyGraph {
    #[new]
    fn new() -> Self {
        PyGraph {
            nodes: HashMap::new(),
            edges: HashMap::new(),
        }
    }

    fn add_node(&mut self, node: PyNode) {
        self.nodes.insert(node.id.clone(), node);
    }

    fn add_edge(&mut self, edge: PyEdge) {
        self.edges.insert(edge.id.clone(), edge);
    }

    #[getter]
    fn node_count(&self) -> usize {
        self.nodes.len()
    }

    #[getter]
    fn edge_count(&self) -> usize {
        self.edges.len()
    }
}

/// PageRank authority propagation through trust/ownership edges.
///
/// Returns a HashMap of node_id → authority score.
///
/// Parameters:
/// - node_ids: List of all node IDs in the graph
/// - edges: List of (source_id, target_id, weight, edge_type) tuples
/// - damping_factor: PageRank damping (default 0.85)
/// - max_iterations: Maximum iterations (default 100)
/// - convergence_threshold: Convergence check (default 0.0001)
#[pyfunction]
#[pyo3(signature = (node_ids, edges, damping_factor=0.85, max_iterations=100, convergence_threshold=0.0001))]
pub fn pagerank(
    node_ids: Vec<String>,
    edges: Vec<(String, String, f64, String)>,
    damping_factor: f64,
    max_iterations: usize,
    convergence_threshold: f64,
) -> PyResult<HashMap<String, f64>> {
    let n = node_ids.len();
    if n == 0 {
        return Ok(HashMap::new());
    }

    // Build node index
    let node_index: HashMap<&str, usize> = node_ids.iter()
        .enumerate()
        .map(|(i, id)| (id.as_str(), i))
        .collect();

    // Filter applicable edges (trust/ownership)
    let applicable: Vec<&(String, String, f64, String)> = edges.iter()
        .filter(|(_, _, _, et)| et == "trust" || et == "ownership")
        .collect();

    if applicable.is_empty() {
        let uniform = 1.0 / n as f64;
        return Ok(node_ids.into_iter().map(|id| (id, uniform)).collect());
    }

    // Build adjacency: incoming[target] = vec![(source_idx, weight)]
    let mut incoming: Vec<Vec<(usize, f64)>> = vec![Vec::new(); n];
    let mut outgoing_count: Vec<usize> = vec![0; n];

    for (src, tgt, weight, edge_type) in &applicable {
        if let (Some(&si), Some(&ti)) = (node_index.get(src.as_str()), node_index.get(tgt.as_str())) {
            incoming[ti].push((si, *weight));
            outgoing_count[si] += 1;

            // Bidirectional for trust edges
            if *edge_type == "trust" {
                incoming[si].push((ti, *weight));
                outgoing_count[ti] += 1;
            }
        }
    }

    // Initialize scores
    let init = 1.0 / n as f64;
    let mut scores: Vec<f64> = vec![init; n];
    let mut new_scores: Vec<f64> = vec![0.0; n];

    let teleport = (1.0 - damping_factor) / n as f64;
    let mut converged = false;

    for _iteration in 0..max_iterations {

        for i in 0..n {
            let mut rank_sum = 0.0;
            for &(source_idx, weight) in &incoming[i] {
                let out = outgoing_count[source_idx].max(1) as f64;
                rank_sum += (scores[source_idx] / out) * weight;
            }
            new_scores[i] = teleport + damping_factor * rank_sum;
        }

        // Check convergence
        let delta: f64 = scores.iter()
            .zip(new_scores.iter())
            .map(|(a, b)| (a - b).abs())
            .sum();

        std::mem::swap(&mut scores, &mut new_scores);

        if delta < convergence_threshold {
            converged = true;
            break;
        }
    }

    let _ = converged; // Used for logging in Python layer

    Ok(node_ids.into_iter()
        .enumerate()
        .map(|(i, id)| (id, scores[i]))
        .collect())
}

/// Risk propagation through dependency/data_flow edges.
///
/// Returns HashMap of node_id → risk score (0-100).
#[pyfunction]
#[pyo3(signature = (node_ids, signal_means, edges, max_hops=3))]
pub fn risk_propagation(
    node_ids: Vec<String>,
    signal_means: Vec<f64>,
    edges: Vec<(String, String, f64, String)>,
    max_hops: usize,
) -> PyResult<HashMap<String, f64>> {
    let n = node_ids.len();
    if n == 0 {
        return Ok(HashMap::new());
    }

    let node_index: HashMap<&str, usize> = node_ids.iter()
        .enumerate()
        .map(|(i, id)| (id.as_str(), i))
        .collect();

    // Initialize risk: inverted signal scores
    let mut risk: Vec<f64> = signal_means.iter()
        .map(|s| (100.0 - s).max(0.0))
        .collect();

    // Build downstream: target → vec![(source, weight)]
    let applicable: Vec<&(String, String, f64, String)> = edges.iter()
        .filter(|(_, _, _, et)| et == "dependency" || et == "data_flow")
        .collect();

    let mut downstream: Vec<Vec<(usize, f64)>> = vec![Vec::new(); n];
    for (src, tgt, weight, _) in &applicable {
        if let (Some(&si), Some(&ti)) = (node_index.get(src.as_str()), node_index.get(tgt.as_str())) {
            downstream[ti].push((si, *weight));
        }
    }

    // Propagate
    for hop in 0..max_hops {
        let decay = 1.0 / (hop as f64 + 1.0);
        let mut updates: Vec<f64> = vec![0.0; n];

        for target_idx in 0..n {
            let target_risk = risk[target_idx];
            if target_risk > 0.0 {
                for &(source_idx, weight) in &downstream[target_idx] {
                    updates[source_idx] += target_risk * weight * decay;
                }
            }
        }

        for i in 0..n {
            risk[i] += updates[i];
        }
    }

    // Normalize to 0-100
    let max_risk = risk.iter().cloned().fold(0.0f64, f64::max);
    if max_risk > 0.0 {
        for r in risk.iter_mut() {
            *r = (*r / max_risk * 100.0).min(100.0);
        }
    }

    Ok(node_ids.into_iter()
        .enumerate()
        .map(|(i, id)| (id, risk[i]))
        .collect())
}

/// Exposure aggregation across jurisdictions and assets.
///
/// Returns HashMap of node_id → exposure score.
#[pyfunction]
pub fn exposure_aggregation(
    node_ids: Vec<String>,
    node_types: Vec<String>,
    node_attributes: Vec<HashMap<String, String>>,
    edges: Vec<(String, String, f64, String)>,
) -> PyResult<HashMap<String, f64>> {
    let mut scores: HashMap<String, f64> = HashMap::new();

    // Find organisation node
    let org_idx = node_types.iter().position(|t| t == "organisation");

    // Process jurisdiction edges (operates_in)
    let presence_weights: HashMap<&str, f64> = [
        ("headquarters", 1.0), ("subsidiary", 0.8), ("branch", 0.5),
        ("remote_workforce", 0.3), ("customers_only", 0.1),
    ].into_iter().collect();

    // Process asset edges (ownership)
    let asset_weights: HashMap<&str, f64> = [
        ("data_store", 1.0), ("application", 0.8), ("cloud_resource", 0.7),
        ("domain", 0.3), ("certificate", 0.2), ("ip_address", 0.1),
    ].into_iter().collect();

    let node_index: HashMap<&str, usize> = node_ids.iter()
        .enumerate()
        .map(|(i, id)| (id.as_str(), i))
        .collect();

    let mut total_exposure = 0.0;

    for (_src, tgt, _, edge_type) in &edges {
        if let Some(&ti) = node_index.get(tgt.as_str()) {
            if edge_type == "operates_in" && node_types[ti] == "jurisdiction" {
                let complexity: f64 = node_attributes[ti].get("complexity_weight")
                    .and_then(|v| v.parse().ok())
                    .unwrap_or(1.0);
                let presence = node_attributes[ti].get("presence_type")
                    .map(|s| s.as_str())
                    .unwrap_or("branch");
                let pw = presence_weights.get(presence).copied().unwrap_or(0.5);
                let score = complexity * pw;
                scores.insert(tgt.clone(), score);
                total_exposure += score;
            } else if edge_type == "ownership" && node_types[ti] == "asset" {
                let subtype = node_attributes[ti].get("asset_subtype")
                    .map(|s| s.as_str())
                    .unwrap_or("");
                let score = asset_weights.get(subtype).copied().unwrap_or(0.5);
                scores.insert(tgt.clone(), score);
                total_exposure += score;
            }
        }
    }

    // Set org total
    if let Some(oi) = org_idx {
        scores.insert(node_ids[oi].clone(), total_exposure);
    }

    Ok(scores)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pagerank_simple() {
        let node_ids = vec!["a".into(), "b".into(), "c".into()];
        let edges = vec![
            ("a".into(), "b".into(), 0.85, "trust".into()),
            ("b".into(), "c".into(), 0.85, "trust".into()),
        ];

        let result = pagerank(node_ids, edges, 0.85, 100, 0.0001).unwrap();
        assert!(result.len() == 3);
        // All nodes should have positive scores
        assert!(result.values().all(|&v| v > 0.0));
    }

    #[test]
    fn test_pagerank_empty() {
        let result = pagerank(vec![], vec![], 0.85, 100, 0.0001).unwrap();
        assert!(result.is_empty());
    }

    #[test]
    fn test_risk_propagation_simple() {
        let node_ids = vec!["a".into(), "b".into()];
        let signal_means = vec![80.0, 30.0]; // b has low score = high risk
        let edges = vec![
            ("a".into(), "b".into(), 0.7, "dependency".into()),
        ];

        let result = risk_propagation(node_ids, signal_means, edges, 3).unwrap();
        assert!(result.len() == 2);
        // a depends on b, b has high risk → a should receive propagated risk
    }
}
