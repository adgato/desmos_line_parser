from pyparsing import (
    Forward, Word, nums, alphas, alphanums, Literal, Group, Opt,
    ZeroOrMore, OneOrMore, DelimitedList, SkipTo,
    ParserElement
)

ParserElement.enablePackrat()

lPar = Literal("\\left(")
rPar = Literal("\\right)")

def bop(op, left, right): return {'bop': op, 'l': left, 'r': right}
def uop(op, value): return {'uop': op, 'v': value}

def brace(t): return Literal("{") + t + Literal("}")

def paren(t): return lPar + t + rPar
def paren2(t1, t2): return lPar + t1 + Literal(",") + t2 + rPar
def paren3(t1, t2, t3): return lPar + t1 + Literal(",") + t2 + Literal(",") + t3 + rPar
def parenN(t): return lPar + Group(DelimitedList(t)) + rPar

def flatten(t): return ''.join(t).replace('_','').replace('{','').replace('}','')

def mul_bops(tokens):
    result = tokens[0]
    op = 0
    for term in tokens[1]:
        if term == '\\cdot': op = 1
        elif term == "\\times": op = 2
        else:
            result = bop('dot' if op == 1 else 'cross' if op == 2 else '*', result, term)
            op = 0
    return result

def add_bops(tokens):
    result = tokens[0]
    if len(tokens) > 1 and tokens[1]:
        operations = tokens[1]
        for i in range(0, len(operations), 2):
            op = operations[i]
            right = operations[i + 1]
            result = bop(op, result, right)
    return result

def trig_ops(tokens):
    result = flatten(tokens).replace('operatorname', '')
    
    has_arc = result.startswith('arc')
    has_inv = result.endswith('^-1')
    if has_arc: result = result[3:]
    if has_arc != has_inv: result += '_inv'
    
    return result.replace('^-1', '').replace('^2', '2')

greek = (
    Literal("\\alpha") | Literal("\\beta") | Literal("\\gamma") | Literal("\\delta") |
    Literal("\\epsilon") | Literal("\\varepsilon") | Literal("\\zeta") | Literal("\\eta") |
    Literal("\\theta") | Literal("\\vartheta") | Literal("\\iota") | Literal("\\kappa") |
    Literal("\\lambda") | Literal("\\mu") | Literal("\\nu") | Literal("\\xi") |
    Literal("\\pi") | Literal("\\varpi") | Literal("\\rho") | Literal("\\varrho") |
    Literal("\\sigma") | Literal("\\varsigma") | Literal("\\tau") | Literal("\\upsilon") |
    Literal("\\phi") | Literal("\\varphi") | Literal("\\chi") | Literal("\\psi") |
    Literal("\\omega") |
    
    Literal("\\Gamma") | Literal("\\Delta") | Literal("\\Theta") | Literal("\\Lambda") |
    Literal("\\Xi") | Literal("\\Pi") | Literal("\\Sigma") | Literal("\\Upsilon") |
    Literal("\\Phi") | Literal("\\Psi") | Literal("\\Omega")
)

# ident composed of greek letters, axes, subscripts
letter = Word(alphas, exact=1) | greek

ident = (letter + Literal("_") + brace(Word(alphanums))) | letter
ident.setParseAction(flatten)

# either mixed fraction or rational number
number = Word(nums)
mixed_frac = number + Literal("\\frac") + brace(number) + brace(number)
rational = Literal(".") + number | number + Literal(".") + Opt(number) | number
number = mixed_frac | rational

mixed_frac.setParseAction(lambda t: bop("+", t[0], bop("/", t[3], t[6])))
rational.setParseAction(flatten)

# infix operators
mul_op = Opt(Literal("\\cdot") | Literal("\\times"))
add_op = Literal("+") | Literal("-")
eq_op = Literal("=") | Literal(">") | Literal("<") | Literal("\\ge") | Literal("\\le")

# binary functions
bop_name1 = Literal("mod") | Literal("nCr") | Literal("distance")
bop_name2 = Literal("max") | Literal("min") | Literal("gcd")

# all the trig names you could ever want
trig_name = Literal("sin") | Literal("cos") | Literal("tan") | Literal("csc") | Literal("sec") | Literal("cot")
trig_name = trig_name + Literal("h") | trig_name
trig_name = Literal("arc") + trig_name | trig_name
trig_name = Literal("operatorname") + brace(trig_name) | trig_name
trig_name = trig_name + Literal("^{2}") | trig_name + Literal("^{-1}") | trig_name
trig_name.setParseAction(trig_ops)

# unary function
uop_name1 = trig_name | Literal("exp") | Literal("ln") | Literal("log")
uop_name2 = Literal("floor") | Literal("ceil") | Literal("round") | Literal("abs") | Literal("erf")

# begin expression parsing
E = Forward()
A = Forward()
AX = Forward()
B = Forward()

# these can be passed to functions like \sin without parenthasis
frac = Literal("\\frac") + brace(E) + brace(E)
exp = Literal("e^") + brace(E)
pow = AX + Literal("^") + brace(E)
val = ident | number | frac
idx = exp | pow

# argument to a unary function that doesn't need to be wrapped in parenthasis
wrap = paren(E)
uarg2 = idx | val
uarg1 = uarg2 | wrap
uarg_mul = uarg2 + Group(OneOrMore(mul_op + uarg1))
uarg = uarg_mul | uarg1
uarg_mul.setParseAction(mul_bops)

# conditional statements
cases = Forward()
comp = E + eq_op + E
cases << (comp + Literal(":") + E + Literal(",") + (cases | E))
cond = Literal("\\left\\{") + cases + Literal("\\right\\}")

# points
point2 = paren2(E, E)
point3 = paren3(E, E, E)
point = point2 | point3

# component of a point
axis = A + Literal(".") + Word("xyz", exact=1)

# function application
app = ident + parenN(E)

# binary
named_bop1 = Literal("\\operatorname") + brace(bop_name1) + paren2(E, E)
named_bop2 = Literal("\\") + bop_name2 + paren2(E, E)
sqrt = Literal("\\sqrt") + Literal("[") + E + Literal("]") + brace(E)
binary = named_bop1 | named_bop2 | sqrt

# unary
named_uop1 = Literal("\\") + uop_name1 + uarg
log = Literal("\\log_") + brace(E) + uarg
diff = Literal("\\frac{d}") + brace(Literal("d") + ident) + uarg
named_uop2 = Literal("\\operatorname") + brace(uop_name2) + paren(E)
length = Literal("\\left|") + E + Literal("\\right|")
sqrt2 = Literal("\\sqrt") + brace(E)
unary = named_uop1 | log | diff | named_uop2 | length | sqrt2

# iterators
sum = Literal("\\sum_") + brace(E + Literal("=") + E) + Literal("^") + brace(E) + B
prod = Literal("\\prod_") + brace(E + Literal("=") + E) + Literal("^") + brace(E) + B
iterators = sum | prod

# parse actions
wrap.setParseAction(lambda t: {'wrap': t[1]})
axis.setParseAction(lambda t: {'axis': t[2], 'point': t[0]})
point2.setParseAction(lambda t: {'p2x': t[1], 'p2y': t[3]})
point3.setParseAction(lambda t: {'p3x': t[1], 'p3y': t[3], 'p3z': t[5]})
app.setParseAction(lambda t: {'app': t[0], 'args': t[2].asList()})
sum.setParseAction(lambda t: {'iter': "sum", 'it': t[2], 'from': t[4], 'to': t[8], 'body': t[10]})
prod.setParseAction(lambda t: {'iter': "prod", 'it': t[2], 'from': t[4], 'to': t[8], 'body': t[10]})
cond.setParseAction(lambda t: t[1])
cases.setParseAction(lambda t: {'if': t[0], 'then': t[2], 'else' : t[4]})
comp.setParseAction(lambda t: {'cop': t[1], 'l': t[0], 'r': t[2]})
named_bop1.setParseAction(lambda t: bop(t[2], t[5], t[7]))
named_bop2.setParseAction(lambda t: bop(t[1], t[3], t[5]))
log.setParseAction(lambda t: bop("log", t[2], t[4]))
diff.setParseAction(lambda t: bop("diff", t[3], t[6]))
pow.setParseAction(lambda t: bop("pow", t[0], t[3]))
sqrt.setParseAction(lambda t: bop("sqrt", t[2], t[5]))
sqrt2.setParseAction(lambda t: bop("sqrt", "2", t[2]))
frac.setParseAction(lambda t: bop("/", t[2], t[5]))
named_uop1.setParseAction(lambda t: uop(t[1], t[2]))
named_uop2.setParseAction(lambda t: uop(t[2], t[5]))
exp.setParseAction(lambda t: uop("exp", t[2]))
length.setParseAction(lambda t: uop("length", t[1]))

# anything binding tighter than multiplication
A << (unary | iterators | binary | cond | app | wrap | point | val)

# weakly constrained operations
AX << (axis | A)
idxAX = idx | AX
signA = add_op + A
signA.setParseAction(lambda t: uop(t[0] + ".", t[1]))

# anything binding tighter than addition
B << ((idxAX | signA) + Group(ZeroOrMore(mul_op + idxAX)))
B.setParseAction(mul_bops)

# any expression
E << (B + Group(ZeroOrMore(add_op + B)))
E.setParseAction(add_bops)

# anything
var_def = ident + Literal("=") + E
func_def = ident + parenN(ident) + Literal("=") + E
var_def.setParseAction(lambda t: {'set': t[0], 'body': t[2]})
func_def.setParseAction(lambda t: {'def': t[0], 'args': t[2].asList(), 'body': t[5]})
S = func_def | var_def | E

def parse_desmos(line: str) -> dict:
    return S.parseString(line.replace("\\ ",""))[0]

if __name__ == "__main__":
    test_definitions = [
        #r"V\left(x\right)=\frac{2}{c}\left(1-\exp\left(-\frac{\operatorname{mod}\left(x,T_{1}\right)}{T_{2}}\right)\right)-1",
        #r"H\left(x\right)=\left\{\operatorname{mod}\left(\frac{x}{T_{1}},2\right)>1:-V\left(x\right),V\left(x\right)\right\}",
        #r"f\left(x\right)=\frac{1}{3\left(Q+1\right)^{\frac{Q}{1.3}}}e^{-\frac{1}{2}x^{2}}\left(10x+\sin^{2}\left(4\left(x-a\right)\right)\right)",
        #r"f_{n2}\left(q,n,t\right)=\operatorname{ceil}\left(\frac{n}{q+1}\right)^{q}g\left(q,\operatorname{ceil}\left(\frac{n}{q+1}\right),t-\frac{q}{2\operatorname{ceil}\left(\frac{n}{q+1}\right)}\right)",
        #r"F_{ib}\left(n\right)=\frac{\sqrt{5}}{5}\left(\phi^{n}-\frac{\cos\left(\pi n\right)}{\phi^{n}}\right)",
        #r"f_{2}\left(t\right)=\frac{\left(-a-\sqrt{a^{2}-1}\right)}{-2\sqrt{a^{2}-1}}e^{\left(-a+\sqrt{a^{2}-1}\right)t}+\frac{\left(-a+\sqrt{a^{2}-1}\right)}{2\sqrt{a^{2}-1}}e^{\left(-a-\sqrt{a^{2}-1}\right)t}\ ",
        #r"p\left(x\right)=0.5\operatorname{erf}\left(-3.7\left(x-0.65\right)\right)+0.5",
        #r"m_{x}\left(P\right)=\left\{\left|P.x\right|-s_{0}>\max\left(\left|P.y\right|-s_{1},\left|P.z\right|-s_{2}\right):0,\left|P.y\right|-s_{1}>\left|P.z\right|-s_{2}:1,2\right\}",
        #r"t_{1}=-\frac{\left(p-u\right)\times\left(v-u\right)\cdot\left(d\times\left(v-u\right)\right)}{\left|d\times\left(v-u\right)\right|^{2}}"
        #r"G_{2}\left(P,t\right)=\left(m_{g}\left(t-0,P.x,s_{0}\right),m_{g}\left(t-1,P.y,s_{1}\right),m_{g}\left(t-2,P.z,s_{2}\right)\right)",
    
        #r"abcde+fgh\cdoti",
        #r"A\times B\cdot C",
        #r"\sin2x^{2}",
        #r"\operatorname{arcsinh}^{-1}x",
        r"A.x^{2}",
    ]
    
    for defn in test_definitions:
        print(f"Function: {defn}")
        print(f"Parsed: {parse_desmos(defn)}")
        print()