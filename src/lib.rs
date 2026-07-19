use pyo3::prelude::*;
use pyo3::types::PyModule;

pub mod bdd;
pub mod interval;
pub mod mdd;

#[pymodule]
pub fn relibmss(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<bdd::PyBddNode>()?;
    m.add_class::<bdd::PyBddMgr>()?;
    m.add_class::<mdd::PyMddNode>()?;
    m.add_class::<mdd::PyMddMgr>()?;
    m.add_class::<bdd::PyBddPath>()?;
    m.add_class::<bdd::PyZddPath>()?;
    m.add_class::<interval::Interval>()?;
    Ok(())
}
