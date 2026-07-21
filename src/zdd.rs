use pyo3::prelude::*;
use bss::prelude::*;

/// Standalone ZDD manager: build set families from scratch with `_empty`/`_base`/
/// `_singleton`/`_from_sets`, then operate on the resulting [`PyZddNode`]s.
#[pyclass(unsendable)]
pub struct PyZddMgr(ZddMgr);

#[pymethods]
impl PyZddMgr {
    #[new]
    pub fn new() -> Self {
        PyZddMgr(ZddMgr::new())
    }

    pub fn _size(&self) -> (usize, usize, usize) {
        self.0.size()
    }

    pub fn _clear_cache(&mut self) {
        self.0.clear_cache()
    }

    pub fn _empty(&self) -> PyZddNode {
        PyZddNode(self.0.empty())
    }

    pub fn _base(&self) -> PyZddNode {
        PyZddNode(self.0.base())
    }

    pub fn _singleton(&mut self, label: &str) -> PyZddNode {
        PyZddNode(self.0.singleton(label))
    }

    pub fn _from_sets(&mut self, sets: Vec<Vec<String>>) -> PyZddNode {
        PyZddNode(self.0.from_sets(&sets))
    }
}

/// A set family as a genuine ZDD — produced by `PyBddMgr::_minpath` / `_mincut` or built
/// from scratch via [`PyZddMgr`]. Supports the set algebra
/// (`union`/`intersect`/`setdiff`/`product`/`divide`).
#[pyclass(unsendable)]
#[derive(Clone)]
pub struct PyZddNode(pub ZddNode);

#[pymethods]
impl PyZddNode {
    pub fn _get_id(&self) -> usize {
        self.0.get_id()
    }

    pub fn _get_label(&self) -> Option<String> {
        self.0.get_label()
    }

    pub fn _get_level(&self) -> Option<usize> {
        self.0.get_level()
    }

    pub fn _get_children(&self) -> Option<(PyZddNode, PyZddNode)> {
        self.0
            .get_children()
            .map(|(f0, f1)| (PyZddNode(f0), PyZddNode(f1)))
    }

    pub fn _dot(&self) -> String {
        self.0.dot()
    }

    pub fn _union(&self, other: &PyZddNode) -> PyZddNode {
        PyZddNode(self.0.union(&other.0))
    }

    pub fn _intersect(&self, other: &PyZddNode) -> PyZddNode {
        PyZddNode(self.0.intersect(&other.0))
    }

    pub fn _setdiff(&self, other: &PyZddNode) -> PyZddNode {
        PyZddNode(self.0.setdiff(&other.0))
    }

    pub fn _product(&self, other: &PyZddNode) -> PyZddNode {
        PyZddNode(self.0.product(&other.0))
    }

    pub fn _divide(&self, other: &PyZddNode) -> PyZddNode {
        PyZddNode(self.0.divide(&other.0))
    }

    pub fn _count(&self, ss: Vec<bool>) -> u64 {
        self.0.count(&ss)
    }

    pub fn _extract(&self, ss: Vec<bool>) -> PyZddPath {
        PyZddPath::new(self, ss)
    }

    pub fn _size(&self) -> (u64, u64, u64) {
        self.0.size()
    }
}

#[pyclass(unsendable)]
pub struct PyZddPath {
    zddnode: ZddNode,
    path: ZddPath,
    domain: Vec<bool>,
}

#[pymethods]
impl PyZddPath {
    #[new]
    fn new(node: &PyZddNode, ss: Vec<bool>) -> Self {
        let path = node.0.extract(&ss);
        PyZddPath {
            zddnode: node.0.clone(),
            path,
            domain: ss,
        }
    }

    fn __len__(&self) -> usize {
        self.zddnode.count(&self.domain) as usize
    }

    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> Option<Vec<String>> {
        slf.path.next()
    }
}
