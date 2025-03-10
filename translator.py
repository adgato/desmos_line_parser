from pyparsing import (
    string, Word, Literal, Group, Opt,
    ZeroOrMore, DelimitedList,
    ParserElement, CharsNotIn
)

def paren(t): return Literal("(") + t + Literal(")")
def hashed(t): return Literal("#") + t + Literal("#")

ParserElement.enablePackrat()

fn_name = Opt("\\") + Word(string.ascii_lowercase) | Word("*-+=<>/", exact=1) + Opt(Literal("."))
args = Word(string.ascii_uppercase)

fn_name.setParseAction(lambda t: ''.join(t).replace('\\',''))

# For marco, we want to capture everything except '#'
marco = CharsNotIn('#')
raw_macro = marco.copy()

include = Literal("#include") + fn_name + paren(Group(DelimitedList(args))) + marco
define = Literal("#define") + fn_name + paren(Group(DelimitedList(args))) + marco
replace = Literal("#replace") + hashed(raw_macro) + hashed(Opt(raw_macro))
ignore = Literal('#') + Opt(raw_macro)

include_arr = {}
define_arr = {}
replace_arr = {}

include.setParseAction(lambda t: include_arr.update({t[1] : {'args': t[3].asList(), 'macro': t[5]}}))
define.setParseAction(lambda t: define_arr.update({t[1] : {'args': t[3].asList(), 'macro': t[5]}}))
replace.setParseAction(lambda t: replace_arr.update({t[2]: '' if t[5] == '#' else t[5]}))

marco.setParseAction(lambda t: t[0].strip())

directive = include | define | replace | ignore
S = ZeroOrMore(directive)

def parse_instr(text: str) -> dict:
    """Parse the input text into a list of parsed expressions"""
    include_arr.clear()
    define_arr.clear()
    replace_arr.clear()
    S.parseString(text, parseAll=True)
    return { 
        "include": include_arr.copy(),
        "define": define_arr.copy(),
        "replace": replace_arr.copy(),
    }

if __name__ == "__main__":
    defn = open("translate_instr.txt", 'r').read()
    result = parse_instr(defn)
    print("\nINCLUDE")
    print('\n'.join([f"{{'{k}': {v}}}" for k, v in result['include'].items()]))
    print("\nDEFINE")
    print('\n'.join([f"{{'{k}': {v}}}" for k, v in result['define'].items()]))
    print("\nREPLACE")
    print('\n'.join([f"{{'{k}': {v}}}" for k, v in result['replace'].items()]))