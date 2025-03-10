# Desmos Line Parser
quick and dirty parser for desmos that takes lines written in desmos as input and returns code in a language of your choice

## example usages:
```
python desmos_to_code.py
python desmos_to_code.py example_instructions/python_instr.txt
python desmos_to_code.py example_instructions/clike_instr.txt
```

## currently supports
arithmetic: `a + b` `a - b` `a \cdot b` `\frac{a}{b}`
implicit multiplication: `a_{pple}b_{anana}`
exponentiation: `e^{x}` `a^{b}`
some binary operations: e.g. `max` `min` `log_{a}b` `\frac{d}{da}b`
some unary operations: e.g. `sin` `ln` `erf` `\sqrt{x}` but not `arcsin`
iterators: `\sum_{a=1}^{n}b` `\prod_{a=1}^{n}b` but not `\int_{a}^{b}ydx`
conditions: `\left\{a>b:x,y\right\}` `\left\{a>b:x,c>d:y,z\right\}`
functions definitions: `f\left(x\right)=x`
variable definitions: `f=x`
function applications: `y=f\left(x\right)+1` (note that `f\left(x\right)` is interpreted as application `f(x)`, but in desmos it could mean multiplication `f * x`)
greek letters
