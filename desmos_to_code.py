from parser import parse_desmos
from translator import parse_instr
import sys

def bind_args(bind: list, frame: dict, arg: int = -1) -> str:
    
    if arg >= 0 and len(frame['args']) == len(bind) - 1:
        frame['args'].insert(arg, '##')
      
    macro: str = frame['macro']
    for i in range(len(bind)):
        macro = macro.replace(frame['args'][i], bind[i])
    return macro

# put hashes around all args, so that they don't conflict with non-args in macros
def wrap_arg_hash(frame: dict):
    bind = [f"#{i}#" for i in frame['args']]
    frame['macro'] = bind_args(bind, frame)
    frame['args'] = bind
    
def gen_code(tree: dict) -> str:
    global header
    if isinstance(tree, str):
        return tree
    
    if isinstance(tree, list):
        return ADIV.join(gen_code(i) for i in tree)
    
    name = next(iter(tree))
    defaults = instr_set[name]
    
    values = list(tree.values())

    bind = [gen_code(values[i]) for i in range(len(values))]
    
    bind_name = defaults['bind_name']
    arg = -1
    if isinstance(bind_name, int):
        arg = bind_name
        bind_name = bind[bind_name]
    
    if incl := include.get(bind_name):
        header = bind_args(bind, incl, arg) + "\n" + header

    return bind_args(bind, define.get(bind_name, defaults), arg)

def translate_desmos(line: str, trans_instrs: str) -> str:
    global define, include, header
    parse_tree = parse_desmos(line)
    remapping = parse_instr(trans_instrs)
    
    define = remapping['define']
    include = remapping['include']
    
    for i in define:
        wrap_arg_hash(define[i])
    for i in include:
        wrap_arg_hash(include[i])
    
    replace = remapping['replace']
    if trans_instrs == "":
        replace.update({'$$': ', '})
    header = ""
    
    translation = gen_code(parse_tree)
    translation = header + "\n" + translation
    
    for k, v in replace.items():
        translation = translation.replace(k, v)
    return translation
    
        
ADIV = "$$"

instr_set = {
    'set' : {
        'bind_name': "set",
        'args': ['NAME', 'BODY'], 
        'macro': "NAME = BODY" 
    },
    'def' : {
        'bind_name': "def",
        'args': ['NAME', 'ARGS', 'BODY'], 
        'macro': "NAME(ARGS) = BODY" 
    },
    'app' : {
        'bind_name': "app",
        'args': ['NAME', 'ARGS'], 
        'macro': "NAME(ARGS) = BODY" 
    },
    'wrap' : {
        'bind_name': "wrap",
        'args': ['X'],
        'macro': "(X)"
    },
    'p2x' : {
        'bind_name': "point2",
        'args': ['X', 'Y'],
        'macro': "(X, Y)"
    },
    'p3x' : {
        'bind_name': "point3",
        'args': ['X', 'Y', 'Z'],
        'macro': "(X, Y, Z)"
    },
    'axis' : {
        'bind_name': "axis",
        'args': ['AXIS', 'POINT'],
        'macro': "POINT.AXIS"
    },
    'if' : {
        'bind_name': "case",
        'args': ['IF', 'THEN', 'ELSE'],
        'macro': "(IF ? THEN : ELSE)"
    },
    'iter' : {
        'bind_name': 0,
        'args': ['FOLD', 'IT', 'FROM', 'TO', 'BODY'],
        'macro': "FOLD(BODY for IT=[FROM..TO])"
    },
    'cop' : {
        'bind_name': 0,
        'args': ['OP', 'L', 'R'],
        'macro': f"OP(L{ADIV}R)"
    },
    'bop' : {
        'bind_name': 0,
        'args': ['OP', 'L', 'R'],
        'macro': f"OP(L{ADIV}R)"
    },
    'uop' : {
        'bind_name': 0,
        'args': ['OP', 'V'],
        'macro': "OP(V)"
    },
}

# where bind_name is a string, it searches for that function name exactly.
# e.g. for 'if' we have `'bind_name': "case"`, so we look for `#define case(IF, THEN, ELSE)`
# the argument names specified in the instructions file do not matter.
# where bind_name is an index this specific argument may be optionally discarded by the function. 
# we look for that argument as the function name.
# e.g. for 'bop' we have `'bind_name': 0`, so functions with name 'NAME' will be searched for the instructions file.
# 'NAME' could be '*' in which case we may look for `#define *(NAME, L, R) L * R`, but, `#define *(L, R) L * R` would also be acceptable.
for i in instr_set:
    wrap_arg_hash(instr_set[i])

header = ""
define = {}
include = {}

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python script_name.py <optional-filename>")
        sys.exit(1)
    
    trans_instrs = open(sys.argv[1], 'r').read() if len(sys.argv) == 2 else ""

    while True:
        print(translate_desmos(input('\nPaste desmos line: '), trans_instrs))
