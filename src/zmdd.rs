use pyo3::prelude::*;
use mss::prelude::*;
use std::collections::{HashMap, HashSet};

/// A family of minimal path vectors as a genuine ZMDD, produced by `PyMddMgr::_minpath`.
/// Supports the label-wise set operations `intersect` / `setdiff`.
#[pyclass(unsendable)]
#[derive(Clone)]
pub struct PyZmddNode(pub ZmddNode<i32>);

#[pymethods]
impl PyZmddNode {
    pub fn _get_id(&self) -> usize {
        self.0.get_id()
    }

    pub fn _intersect(&self, other: &PyZmddNode) -> PyZmddNode {
        PyZmddNode(self.0.intersect(&other.0))
    }

    pub fn _setdiff(&self, other: &PyZmddNode) -> PyZmddNode {
        PyZmddNode(self.0.setdiff(&other.0))
    }

    pub fn _count(&self, ss: Vec<i32>) -> u64 {
        let ssv: HashSet<i32> = ss.into_iter().collect();
        self.0.count(&ssv)
    }

    pub fn _extract(&self, ss: Vec<i32>) -> PyZmddPath {
        PyZmddPath::new(self, ss)
    }
}

#[pyclass(unsendable)]
pub struct PyZmddPath {
    path: ZmddPath<i32>,
}

#[pymethods]
impl PyZmddPath {
    #[new]
    fn new(node: &PyZmddNode, ss: Vec<i32>) -> Self {
        let ssv: HashSet<i32> = ss.into_iter().collect();
        PyZmddPath {
            path: node.0.extract(&ssv),
        }
    }

    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> Option<HashMap<String, usize>> {
        slf.path.next()
    }
}
