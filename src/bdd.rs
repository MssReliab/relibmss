use crate::interval::Interval;
use crate::zdd::PyZddNode;
use pyo3::{exceptions::PyValueError, prelude::*};
use bss::prelude::*;
use std::collections::HashMap;

#[pyclass(unsendable)]
pub struct PyBddMgr(BssMgr);

#[pyclass(unsendable)]
#[derive(Clone)]
pub struct PyBddNode(BddNode);

#[pymethods]
impl PyBddMgr {
    // constructor
    #[new]
    pub fn new() -> Self {
        PyBddMgr(BssMgr::new())
    }

    pub fn _size(&self) -> (usize, usize, usize) {
        self.0.size()
    }

    pub fn _clear_cache(&mut self) {
        self.0.clear_cache()
    }

    pub fn _value(&self, val: bool) -> PyBddNode {
        if val {
            PyBddNode(self.0.one())
        } else {
            PyBddNode(self.0.zero())
        }
    }

    pub fn _create_node(&self, hid: HeaderId, f0: &PyBddNode, f1: &PyBddNode) -> PyBddNode {
        PyBddNode(self.0.create_node(hid, &f0.0, &f1.0))
    }

    pub fn _defvar(&mut self, var: &str) -> PyBddNode {
        PyBddNode(self.0.defvar(var))
    }

    pub fn _get_varorder(&self) -> Vec<String> {
        self.0.get_varorder()
    }

    pub fn _rpn(&mut self, expr: &str) -> PyResult<PyBddNode> {
        if let Ok(node) = self.0.rpn(expr) {
            Ok(PyBddNode(node))
        } else {
            Err(PyValueError::new_err("Invalid expression"))
        }
    }

    pub fn _and(&self, nodes: Vec<PyBddNode>) -> PyBddNode {
        let xs = nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>();
        PyBddNode(self.0.and(&xs))
    }

    pub fn _or(&self, nodes: Vec<PyBddNode>) -> PyBddNode {
        let xs = nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>();
        PyBddNode(self.0.or(&xs))
    }

    pub fn _kofn(&self, k: usize, nodes: Vec<PyBddNode>) -> PyBddNode {
        let xs = nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>();
        PyBddNode(self.0.kofn(k, &xs))
    }

    /// Minimal path vectors of `node` as a genuine ZDD set family, or `None` if the
    /// structure function is not monotone (coherent).
    pub fn _minpath(&self, node: &PyBddNode) -> Option<PyZddNode> {
        self.0.minpath(&node.0).map(PyZddNode)
    }

    /// Minimal cut vectors of `node` as a genuine ZDD set family, or `None` if the
    /// structure function is not monotone.
    pub fn _mincut(&self, node: &PyBddNode) -> Option<PyZddNode> {
        self.0.mincut(&node.0).map(PyZddNode)
    }
}

#[pymethods]
impl PyBddNode {
    pub fn _get_id(&self) -> usize {
        self.0.get_id()
    }

    pub fn _get_header(&self) -> Option<HeaderId> {
        self.0.get_header()
    }

    pub fn _get_level(&self) -> Option<usize> {
        self.0.get_level()
    }

    pub fn _get_label(&self) -> Option<String> {
        self.0.get_label()
    }

    pub fn _get_children(&self) -> Option<(PyBddNode, PyBddNode)> {
        if let Some(node) = self.0.get_children() {
            let f0 = PyBddNode(node.0.clone());
            let f1 = PyBddNode(node.1.clone());
            Some((f0, f1))
        } else {
            None
        }
    }

    pub fn _dot(&self) -> String {
        self.0.dot()
    }

    pub fn _and(&self, other: &PyBddNode) -> PyBddNode {
        PyBddNode(self.0.and(&other.0))
    }

    pub fn _or(&self, other: &PyBddNode) -> PyBddNode {
        PyBddNode(self.0.or(&other.0))
    }

    pub fn _xor(&self, other: &PyBddNode) -> PyBddNode {
        PyBddNode(self.0.xor(&other.0))
    }

    pub fn _not(&self) -> PyBddNode {
        PyBddNode(self.0.not())
    }

    pub fn _equiv(&self, other: &PyBddNode) -> bool {
        self.0.get_id() == other.0.get_id()
    }

    pub fn _ifelse(&self, then: &PyBddNode, else_: &PyBddNode) -> PyBddNode {
        PyBddNode(self.0.ite(&then.0, &else_.0))
    }

    pub fn _prob(&self, pv: HashMap<String, f64>, ss: Vec<bool>) -> f64 {
        self.0.prob(&pv, &ss)
    }

    pub fn _bmeas(&self, pv: HashMap<String, f64>, ss: Vec<bool>) -> HashMap<String, f64> {
        self.0.bmeas(&pv, &ss)
    }

    pub fn _prob_interval(&self, pv: HashMap<String, Interval>, ss: Vec<bool>) -> Interval {
        self.0.prob(&pv, &ss)
    }

    pub fn _bmeas_interval(
        &self,
        pv: HashMap<String, Interval>,
        ss: Vec<bool>,
    ) -> HashMap<String, Interval> {
        self.0.bmeas(&pv, &ss)
    }

    /// The dual structure function `phi^D(x) = !phi(!x)` (a boolean BDD; `minpath`/`mincut`
    /// live on the manager since they also need the ZDD forest).
    pub fn _dual(&self) -> PyBddNode {
        PyBddNode(self.0.dual())
    }

    pub fn _size(&self) -> (u64, u64, u64) {
        self.0.size()
    }

    pub fn _bdd_count(&self, ss: Vec<bool>) -> u64 {
        self.0.bdd_count(&ss)
    }

    pub fn _bdd_extract(&self, ss: Vec<bool>) -> PyBddPath {
        PyBddPath::new(&self, ss.clone())
    }
}

#[pyclass(unsendable)]
pub struct PyBddPath {
    bddnode: BddNode,
    bddpath: BddPath,
    domain: Vec<bool>,
}

#[pymethods]
impl PyBddPath {
    #[new]
    fn new(node: &PyBddNode, ss: Vec<bool>) -> Self {
        let bddpath = node.0.bdd_extract(&ss);
        PyBddPath {
            bddnode: node.0.clone(),
            bddpath,
            domain: ss.clone(),
        }
    }

    fn __len__(&self) -> usize {
        self.bddnode.bdd_count(&self.domain) as usize
    }

    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> Option<Vec<String>> {
        slf.bddpath.next()
    }
}
