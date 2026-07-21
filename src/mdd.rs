use crate::interval::Interval;
use crate::zmdd::PyZmddNode;
use pyo3::{exceptions::PyValueError, prelude::*};
use mss::prelude::*;
use std::collections::{HashMap, HashSet};

#[pyclass(unsendable)]
pub struct PyMddMgr(MssMgr<i32>);

#[pyclass(unsendable)]
#[derive(Clone, Debug)]
pub struct PyMddNode(MddNode<i32>);

#[pymethods]
impl PyMddMgr {
    #[new]
    pub fn new() -> Self {
        PyMddMgr(MssMgr::new())
    }

    /// Minimal path vectors of `node` as a genuine ZMDD family, or `None` if the structure
    /// function is not coherent.
    pub fn _minpath(&self, node: &PyMddNode) -> Option<PyZmddNode> {
        self.0.minpath(&node.0).map(PyZmddNode)
    }

    pub fn _size(&self) -> (usize, usize, usize, usize) {
        self.0.size()
    }

    pub fn _clear_cache(&mut self) {
        self.0.clear_cache()
    }

    pub fn _boolean(&self, val: bool) -> PyMddNode {
        PyMddNode(self.0.boolean(val))
    }

    pub fn _value(&self, val: i32) -> PyMddNode {
        PyMddNode(self.0.value(val))
    }

    pub fn _create_node(&self, hid: HeaderId, nodes: Vec<PyMddNode>) -> PyMddNode {
        PyMddNode(self.0.create_node(hid, &nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>()))
    }

    pub fn _defvar(&mut self, label: &str, range: usize) -> PyMddNode {
        PyMddNode(self.0.defvar(label, range))
    }

    pub fn _get_varorder(&self) -> Vec<(String, usize)> {
        self.0.get_varorder()
    }

    pub fn _rpn(&mut self, rpn: &str, vars: HashMap<String, usize>) -> PyResult<PyMddNode> {
        if let Ok(node) = self.0.rpn(rpn, &vars) {
            Ok(PyMddNode(node))
        } else {
            Err(PyValueError::new_err("Invalid expression"))
        }
    }

    pub fn _and(&mut self, nodes: Vec<PyMddNode>) -> PyMddNode {
        let xs = nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>();
        PyMddNode(self.0.and(&xs))
    }

    pub fn _or(&mut self, nodes: Vec<PyMddNode>) -> PyMddNode {
        let xs = nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>();
        PyMddNode(self.0.or(&xs))
    }

    pub fn _min(&mut self, nodes: Vec<PyMddNode>) -> PyMddNode {
        let xs = nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>();
        PyMddNode(self.0.min(&xs))
    }

    pub fn _max(&mut self, nodes: Vec<PyMddNode>) -> PyMddNode {
        let xs = nodes.iter().map(|x| x.0.clone()).collect::<Vec<_>>();
        PyMddNode(self.0.max(&xs))
    }
}

#[pymethods]
impl PyMddNode {
    pub fn _get_id(&self) -> (usize, usize) {
        self.0.get_id2()
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

    pub fn _get_children(&self) -> Option<Vec<PyMddNode>> {
        if let Some(x) = self.0.get_children() {
            let res = x.iter().map(|x| PyMddNode(x.clone())).collect::<Vec<_>>();
            Some(res)
        } else {
            None
        }
    }

    pub fn _is_boolean(&self) -> bool {
        self.0.is_boolean()
    }

    pub fn _dot(&self) -> String {
        self.0.dot()
    }

    pub fn _add(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.add(&other.0))
    }

    pub fn _sub(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.sub(&other.0))
    }

    pub fn _mul(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.mul(&other.0))
    }

    pub fn _div(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.div(&other.0))
    }

    pub fn _equiv(&self, other: &PyMddNode) -> bool {
        self.0.get_id() == other.0.get_id()
    }

    pub fn _eq(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.eq(&other.0))
    }

    pub fn _ne(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.ne(&other.0))
    }

    pub fn _lt(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.lt(&other.0))
    }

    pub fn _le(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.le(&other.0))
    }

    pub fn _gt(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.gt(&other.0))
    }

    pub fn _ge(&self, other: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.ge(&other.0))
    }

    pub fn _not(&mut self) -> PyMddNode {
        PyMddNode(self.0.not())
    }

    pub fn _ifelse(&self, then: &PyMddNode, els: &PyMddNode) -> PyMddNode {
        PyMddNode(self.0.ite(&then.0, &els.0))
    }

    pub fn _prob(&mut self, pv: HashMap<String, Vec<f64>>, ss: Vec<i32>) -> f64 {
        self.0.prob(&pv, &ss)
    }

    pub fn _prob_interval(&mut self, pv: HashMap<String, Vec<Interval>>, ss: Vec<i32>) -> Interval {
        self.0.prob(&pv, &ss)
    }

    pub fn _bmeas(&mut self, pv: HashMap<String, Vec<f64>>, ss: Vec<i32>) -> HashMap<String, Vec<f64>> {
        self.0.bmeas(&pv, &ss)
    }

    pub fn _bmeas_interval(
        &mut self,
        pv: HashMap<String, Vec<Interval>>,
        ss: Vec<i32>,
    ) -> HashMap<String, Vec<Interval>> {
        self.0.bmeas(&pv, &ss)
    }

    pub fn _mdd_count(&self, ss: Vec<i32>) -> u64 {
        let ss = ss.iter().map(|x| *x).collect::<HashSet<_>>();
        self.0.mdd_count(&ss)
    }

    pub fn _mdd_extract(&self, ss: Vec<i32>) -> PyMddPath {
        PyMddPath::new(&self, ss)
    }

    pub fn _size(&self) -> (u64, u64, u64) {
        self.0.size()
    }
}

#[pyclass(unsendable)]
pub struct PyMddPath {
    bddnode: MddNode<i32>,
    bddpath: MddPath<i32>,
    domain: HashSet<i32>,
}

#[pymethods]
impl PyMddPath {
    #[new]
    fn new(node: &PyMddNode, ss: Vec<i32>) -> Self {
        let ss = ss.iter().map(|x| *x).collect::<HashSet<_>>();
        let bddpath = node.0.mdd_extract(&ss);
        PyMddPath {
            bddnode: node.0.clone(),
            bddpath,
            domain: ss.clone(),
        }
    }

    fn __len__(&self) -> usize {
        self.bddnode.mdd_count(&self.domain) as usize
    }

    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> Option<HashMap<String, usize>> {
        slf.bddpath.next()
    }
}

