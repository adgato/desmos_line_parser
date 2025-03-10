from pyparsing import (
    Forward, Word, nums, alphas, alphanums, Literal, Group, Opt,
    ZeroOrMore, OneOrMore, DelimitedList, SkipTo,
    ParserElement
)

ParserElement.enablePackrat()

def bop(op, left, right): return {'bop': op, 'l': left, 'r': right}

def uop(op, value): return {'uop': op, 'v': value}

def brace(t): return Literal("{") + t + Literal("}")
def paren(t): return Literal("\\left(") + t + Literal("\\right)")
def flatten(t): return ''.join(t).replace('_','').replace('{','').replace('}','')

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

letter = Word(alphas, exact=1) | greek
number = Word(nums)
number = Literal(".") + number | number + Literal(".") + number | number

ident = (letter + Literal("_") + brace(Word(alphanums))) | letter

number.setParseAction(flatten)
ident.setParseAction(flatten)

E = Forward()
A = Forward()
B = Forward()

eqop = Literal("=") | Literal(">") | Literal("<") | Literal("\\ge") | Literal("\\le")
bop_name1 = Literal("mod") | Literal("nCr")
bop_name2 = Literal("max") | Literal("min") | Literal("gcd")

trig_name = Literal("sin") | Literal("cos") | Literal("tan") | Literal("csc") | Literal("sec") | Literal("cot")
trig_name = trig_name | trig_name + Literal("h") # | Literal("arc") + trig_name # this is weird for arcsinh so not including for now
trig_name = trig_name + Literal("^{2}") | trig_name + Literal("^{-1}") | trig_name

uop_name1 = trig_name | Literal("exp") | Literal("ln") | Literal("log")
uop_name2 = Literal("floor") | Literal("ceil") | Literal("round") | Literal("abs") | Literal("erf")

frac = Literal("\\frac") + brace(E) + brace(E)
exp = Literal("e^") + brace(E)
pow = A + Literal("^") + brace(E)
wrap = paren(E)
idx = exp | pow
val = ident | number | frac

# body multiplication
body2 = idx | val
body1 = body2 | wrap

body_mul = body2 + Group(OneOrMore(Opt(Literal('\\cdot')) + body1))

def mul_bops(tokens):
    result = tokens[0]
    for term in tokens[1]:
        if term != '\\cdot':
            result = bop('*', result, term)
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

body_mul.setParseAction(mul_bops)

body = body_mul | body1

app = ident + paren(Group(DelimitedList(E)))
named_bop1 = Literal("\\operatorname") + brace(bop_name1) + paren(E + Literal(",") + E)
named_bop2 = Literal("\\") + bop_name2 + paren(E + Literal(",") + E)

cases = Forward()
comp = E + eqop + E
cases << (comp + Literal(":") + E + Literal(",") + (cases | E))

cond = Literal("\\left\\{") + cases + Literal("\\right\\}")
abs = Literal("\\left|") + E + Literal("\\right|")
sqrt2 = Literal("\\sqrt") + brace(E)
sqrt = Literal("\\sqrt") + Literal("[") + E + Literal("]") + brace(E)

dx = Literal("d") + ident
dx.setParseAction(lambda t: t[1])

named_uop1 = Literal("\\") + uop_name1 + body
named_uop2 = Literal("\\operatorname") + brace(uop_name2) + paren(E)
log = Literal("\\log_") + brace(E) + body
diff = Literal("\\frac{d}") + brace(dx) + body
sum = Literal("\\sum_") + brace(E + Literal("=") + E) + Literal("^") + brace(E) + B
prod = Literal("\\prod_") + brace(E + Literal("=") + E) + Literal("^") + brace(E) + B
#integral = Literal("\\int_") + brace(E) + Literal("^") + brace(E) + SkipTo(dx) + dx # this is pretty lazy... and won't always work...

trig_name.setParseAction(lambda t: flatten(t).replace('^2','2').replace('^-1','_inv'))
app.setParseAction(lambda t: {'app': t[0], 'args': t[2].asList()})
wrap.setParseAction(lambda t: {'wrap': t[1]})
sum.setParseAction(lambda t: {'iter': "sum", 'it': t[2], 'from': t[4], 'to': t[8], 'body': t[10]})
prod.setParseAction(lambda t: {'iter': "prod", 'it': t[2], 'from': t[4], 'to': t[8], 'body': t[10]})
#integral.setParseAction(lambda t: {'iter': "integral", 'it': t[9], 'from': t[2], 'to': t[6], 'body': E.parseString(t[8])[0]})
cond.setParseAction(lambda t: t[1])
cases.setParseAction(lambda t: {'if': t[0], 'then': t[2], 'else' : t[4]})
comp.setParseAction(lambda t: {'cop': t[1], 'l': t[0], 'r': t[2]})
named_bop1.setParseAction(lambda t: bop(t[2], t[5], t[7]))
named_bop2.setParseAction(lambda t: bop(t[1], t[3], t[5]))
log.setParseAction(lambda t: bop("log", t[2], t[4]))
diff.setParseAction(lambda t: bop("diff", t[2], t[4]))
pow.setParseAction(lambda t: bop("pow", t[0], t[3]))
sqrt.setParseAction(lambda t: bop("sqrt", t[2], t[5]))
sqrt2.setParseAction(lambda t: bop("sqrt", "2", t[2]))
frac.setParseAction(lambda t: bop("/", t[2], t[5]))
named_uop1.setParseAction(lambda t: uop(t[1], t[2]))
named_uop2.setParseAction(lambda t: uop(t[2], t[5]))
exp.setParseAction(lambda t: uop("exp", t[2]))
abs.setParseAction(lambda t: uop("abs", t[1]))


A << (named_bop1 | named_bop2 | cond | abs | sqrt | sqrt2 | named_uop2 | app | wrap | val) # | integral

sign = (Literal("+") | Literal("-")) + B

atom2 = idx | named_uop1 | log | diff | sum | prod | A 
atom1 = atom2 | sign

B << (atom1 + Group(ZeroOrMore(Opt(Literal('\\cdot')) + atom2)))

E << (B + Group(ZeroOrMore((Literal("+") | Literal("-")) + B)))

sign.setParseAction(lambda t: uop(t[0] + ".", t[1]))
B.setParseAction(mul_bops)
E.setParseAction(add_bops)

var_def = ident + Literal("=") + E
func_def = ident + paren(Group(DelimitedList(ident))) + Literal("=") + E
var_def.setParseAction(lambda t: {'set': t[0], 'body': t[2]})
func_def.setParseAction(lambda t: {'def': t[0], 'args': t[2].asList(), 'body': t[5]})

S = func_def | var_def | E

def parse_desmos(line: str) -> dict:
    return S.parseString(line.replace("\\ ",""))[0]

if __name__ == "__main__":
    test_definitions = [

        r"V\left(x\right)=\frac{2}{c}\left(1-\exp\left(-\frac{\operatorname{mod}\left(x,T_{1}\right)}{T_{2}}\right)\right)-1",
        r"H\left(x\right)=\left\{\operatorname{mod}\left(\frac{x}{T_{1}},2\right)>1:-V\left(x\right),V\left(x\right)\right\}",
        r"f\left(x\right)=\frac{1}{3\left(Q+1\right)^{\frac{Q}{1.3}}}e^{-\frac{1}{2}x^{2}}\left(10x+\sin^{2}\left(4\left(x-a\right)\right)\right)",
        r"f_{n2}\left(q,n,t\right)=\operatorname{ceil}\left(\frac{n}{q+1}\right)^{q}g\left(q,\operatorname{ceil}\left(\frac{n}{q+1}\right),t-\frac{q}{2\operatorname{ceil}\left(\frac{n}{q+1}\right)}\right)",
        r"F_{ib}\left(n\right)=\frac{\sqrt{5}}{5}\left(\phi^{n}-\frac{\cos\left(\pi n\right)}{\phi^{n}}\right)",
        r"f_{2}\left(t\right)=\frac{\left(-a-\sqrt{a^{2}-1}\right)}{-2\sqrt{a^{2}-1}}e^{\left(-a+\sqrt{a^{2}-1}\right)t}+\frac{\left(-a+\sqrt{a^{2}-1}\right)}{2\sqrt{a^{2}-1}}e^{\left(-a-\sqrt{a^{2}-1}\right)t}\ ",
        r"p\left(x\right)=0.5\operatorname{erf}\left(-3.7\left(x-0.65\right)\right)+0.5",
        
        r"abcde+fgh\cdoti",
        r"\sin2x^{2}",
        r"\sin\left(2\right)x^{2}",
        r"\sin2\left(x^{2}\right)",
    ]
    
    for defn in test_definitions:
        print(f"Function: {defn}")
        print(f"Parsed: {parse_desmos(defn)}")
        print()