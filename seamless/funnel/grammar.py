from ast import literal_eval
from functools import partial

from derp import Grammar, lit, unpack
from grammars.python import p, ast as py_ast

from . import ast


def emit_file_input(args):
    type_defs, endmarker = args
    valid_stmts = tuple([type_def for type_def in type_defs if type_def != '\n'])
    return ast.FunnelModule(valid_stmts)


def emit_type(args):
    _, name, _, body = unpack(args, 4)
    return ast.FunnelType(name, body)


def emit_suite(args):
    _, _, docstring, stmts, _ = unpack(args, 5)
    valid_stmts = tuple([s for s in stmts if s != '\n'])
    if docstring != '':
        valid_stmts = (docstring,) + valid_stmts
    return valid_stmts


def emit_enum(args):
    _, name, _, first_opt, option_pairs, _ = unpack(args, 6)
    _, options = zip(*option_pairs)
    all_options = (first_opt,) + options
    return ast.Field(name, ast.EnumType(all_options))


def emit_generic(args):
    type_name, name = args
    return ast.Field(name, ast.GenericType(type_name))


def emit_optional(args):
    _, field, opt_subscript, _ = unpack(args, 4)

    if opt_subscript:
        array_type = ast.ArrayType(field.type, opt_subscript.length)
        field = ast.Field(field.name, array_type)

    return ast.OptionalField(field.name, field.type)


def emit_subscript(args):
    _, length_str, _ = unpack(args, 3)
    length = literal_eval(length_str)
    assert isinstance(length, int)
    return ast.ArraySubscript(length)


def validate_int(value):
    assert isinstance(value, py_ast.Num), "expected int"
    assert isinstance(value.n, int), "expected int"


def validate_float(value):
    assert isinstance(value, py_ast.Num), "expected float"
    assert isinstance(value.n, float), "expected float"


def validate_bool(value):
    assert isinstance(value, py_ast.NameConstant), "expected bool"
    assert value.value in {'True', 'False'}, "expected bool"


def validate_string(value):
    assert isinstance(value, py_ast.Str), "expected string"


builtin_id_validators = {"Integer": validate_int,
                         "Bool": validate_bool,
                         "Float": validate_float,
                         "String": validate_string}


def generic_id_validator(type_id, value):
    print("Unable to validate type {}".format(type_id))


def validate_generic_type(generic_type, value):
    field_type = generic_type.id

    try:
        validator = builtin_id_validators[field_type]
    except KeyError:
        validator = partial(generic_id_validator, field_type)

    validator(value)


def validate_enum_type(enum_type, value):
    assert isinstance(value, py_ast.Str), "expected string"


def validate_default_type(field_type, value):
    if isinstance(field_type, ast.GenericType):
        validate_generic_type(field_type, value)
    else:
        assert isinstance(field_type, ast.EnumType)
        validate_enum_type(field_type, value)


def emit_default(args):
    field, assignment, _ = unpack(args, 3)
    if assignment == '':
        return field

    _, value = assignment
    validate_default_type(field.type, value)
    return ast.DefaultField(field.name, field.type, value)


def emit_form_block(args):
    _, _, body = unpack(args, 3)
    return ast.FormBlock(body)


def emit_validate_block(args):
    _, _, body = unpack(args, 3)
    return ast.ValidateBlock(body)


def emit_if_stmt(args):
    _, test, _, body = unpack(args, 4)
    return py_ast.If(test, (body,), ()),


def emit_docstring(args):
    literals, _ = args
    if literals == '':
        return ''
    return ast.Docstring(''.join(literals))


def emit_default_array(args):
    body, newline = unpack(args, 2)
    field, subscript, opt_assign = unpack(body, 3)

    array_type = ast.ArrayType(field.type, subscript.length)
    if opt_assign == '':
        return ast.Field(field.name, array_type)

    _, _, list_, _ = unpack(opt_assign, 4)
    if subscript.length != len(list_.elts):
        raise SyntaxError("default list contains {} elements, but expected array of length {}"
                          .format(len(list_.elts), subscript.length))

    for element in list_.elts:
        validate_default_type(field.type, element)

    return ast.DefaultField(field.name, array_type, list_)


f = Grammar('EBNF')

# Python inherited parsers
f.py_test_list = p.test_list
f.py_simple_stmt = p.simple_stmt
f.py_suite = p.suite
f.py_func_def = p.func_def
f.py_test = p.test
f.py_test_list_comp = p.test_list_comp

# Funnel parsers
f.file_input = ((f.type | lit('NEWLINE'))[...] & lit('ENDMARKER')) >> emit_file_input
f.type = (lit('Type') & lit('ID') & lit(':') & f.suite) >> emit_type
f.suite = (lit('NEWLINE') & lit('INDENT') & ~f.docstring & (f.body_stmt | lit('NEWLINE'))[1:] & lit('DEDENT')) >> emit_suite
f.body_stmt = f.stmt | f.block
f.stmt = f.declaration_stmt
f.docstring = (lit('LIT')[1:] & lit('NEWLINE')) >> emit_docstring

# declaration stmts
f.declaration_stmt = f.default_stmt | f.optional_stmt | f.default_array_stmt
f.default_array_stmt = (f.typed_id & f.array_length & ~(lit('=') & lit('[') & f.py_test_list_comp & lit(']')) &
                        lit('NEWLINE')) >> emit_default_array
f.default_stmt = (f.typed_id & ~(lit('=') & f.py_test_list) & lit('NEWLINE')) >> emit_default
f.optional_stmt = (lit('*') & f.typed_id & ~f.array_length & lit('NEWLINE')) >> emit_optional
f.array_length = (lit('[') & lit('NUMBER') & lit(']')) >> emit_subscript

# type declarations
f.enum_id = (lit('Enum') & lit('ID') & lit('(') & lit('LIT') & (lit(',') & lit('LIT'))[1:] & lit(')')) >> emit_enum
f.generic_id = (lit('ID') & lit('ID')) >> emit_generic
f.typed_id = f.enum_id | f.generic_id

# block stmts
f.block = f.form_block | f.validate_block | f.py_func_def
f.form_block = (lit('form') & lit(':') & f.block_suite) >> emit_form_block
f.validate_block = (lit('validate') & lit(':') & f.block_suite) >> emit_validate_block
f.block_suite = f.py_suite | f.if_stmt_inline
f.if_stmt_inline = (lit('if') & f.py_test & lit(':') & f.py_simple_stmt) >> emit_if_stmt

f.validate()
