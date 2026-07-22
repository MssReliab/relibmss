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

    pub fn _dot(&self) -> String {
        self.0.dot()
    }

    pub fn _labels(&self) -> Vec<i32> {
        self.0.labels()
    }

    pub fn _is_cut(&self) -> bool {
        self.0.is_cut()
    }

    pub fn _extract_level(&self, level: i32) -> Vec<HashMap<String, usize>> {
        self.0.extract_level(level)
    }
}

#[pyclass(unsendable)]
pub struct PyZmddPath {
    zmddnode: ZmddNode<i32>,
    path: ZmddPath<i32>,
    domain: HashSet<i32>,
}

#[pymethods]
impl PyZmddPath {
    #[new]
    fn new(node: &PyZmddNode, ss: Vec<i32>) -> Self {
        let ssv: HashSet<i32> = ss.into_iter().collect();
        PyZmddPath {
            zmddnode: node.0.clone(),
            path: node.0.extract(&ssv),
            domain: ssv,
        }
    }

    fn __len__(&self) -> usize {
        self.zmddnode.count(&self.domain) as usize
    }

    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> Option<HashMap<String, usize>> {
        slf.path.next()
    }
}
