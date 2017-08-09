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
    _, _, stmts, _ = unpack(args, 4)
    valid_stmts = tuple([s for s in stmts if s != '\n'])
    return valid_stmts


def emit_enum(args):
    _, name, _, first_opt, option_pairs, _ = unpack(args, 6)
    _, options = zip(*option_pairs)
    all_options = (first_opt,) + options
    return ast.EnumField(name, all_options)


def emit_generic_id(args):
    type_name, name = args
    return ast.IDField(name, type_name)


def emit_nullable(args):
    _, field, opt_array, _ = unpack(args, 4)
    result = ast.Nullable(field)

    if opt_array:
        return ast.Array(result, opt_array)

    return result


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


def custom_id_validator(field_type, value):
    print("Unable to validate type {}".format(field_type))


def validate_id_field(field, value):
    field_type = field.type

    try:
        validator = builtin_id_validators[field_type]
    except KeyError:
        validator = partial(custom_id_validator, field_type)

    validator(value)


def validate_enum_field(field, value):
    assert isinstance(value, py_ast.Str), "expected string"


def validate_default_field(field, value):
    if isinstance(field, ast.IDField):
        validate_id_field(field, value)
    else:
        assert isinstance(field, ast.EnumField)
        validate_enum_field(field, value)


def emit_default_array_field(args):
    body, newline = unpack(args, 2)
    field, subscript, opt_assign = unpack(body, 3)
    field_array = ast.Array(field, subscript)
    if opt_assign == '':
        return field_array

    _, _, list_, _ = unpack(opt_assign, 4)
    if subscript.length != len(list_.elts):
        raise SyntaxError("default list contains {} elements, but expected array of length {}"
                          .format(len(list_.elts), subscript.length))

    for element in list_.elts:
        validate_default_field(field, element)

    return ast.Default(field_array, list_)


def emit_default_field(args):
    field_type, assignment, _ = unpack(args, 3)
    if assignment == '':
        return field_type

    _, value = assignment
    validate_default_field(field_type, value)
    return ast.Default(field_type, value)


def emit_form_block(args):
    _, _, body = unpack(args, 3)
    return ast.FormBlock(body)


def emit_validate_block(args):
    _, _, body = unpack(args, 3)
    return ast.ValidateBlock(body)


def emit_if_stmt(args):
    _, test, _, body = unpack(args, 4)
    return py_ast.If(test, (body,), ()),


f = Grammar('EBNF')
f.file_input = ((f.type | lit('NEWLINE'))[...] & lit('ENDMARKER')) >> emit_file_input
f.type = (lit('Type') & lit('ID') & lit(':') & f.suite) >> emit_type
f.suite = (lit('NEWLINE') & lit('INDENT') & (f.body_stmt | lit('NEWLINE'))[1:] & lit('DEDENT')) >> emit_suite
f.body_stmt = f.stmt | f.block
f.stmt = f.declaration_stmt

# declaration stmts
f.declaration_stmt = f.default_stmt | f.optional_stmt | f.default_array_stmt
f.default_array_stmt = (f.typed_id & f.array_length & ~(lit('=') & lit('[') & p.test_list_comp & lit(']')) &
                        lit('NEWLINE')) >> emit_default_array_field
f.default_stmt = (f.typed_id & ~(lit('=') & p.test_list) & lit('NEWLINE')) >> emit_default_field
f.optional_stmt = (lit('*') & f.typed_id & ~f.array_length & lit('NEWLINE')) >> emit_nullable
f.array_length = (lit('[') & lit('NUMBER') & lit(']')) >> emit_subscript

# type declarations
f.enum_id = (lit('Enum') & lit('ID') & lit('(') & lit('LIT') & (lit(',') & lit('LIT'))[1:] & lit(')')) >> emit_enum
f.builtin_id = ((lit("Integer") | lit("Bool") | lit("String") | lit("Float")) & lit('ID')) >> emit_generic_id
f.generic_id = (lit('ID') & lit('ID')) >> emit_generic_id
f.typed_id = f.enum_id | f.builtin_id | f.generic_id

# block stmts
f.block = f.form_block | f.validate_block
f.form_block = (lit('form') & lit(':') & f.block_suite) >> emit_form_block
f.validate_block = (lit('validate') & lit(':') & f.block_suite) >> emit_validate_block
f.block_suite = p.suite | f.if_stmt_inline
f.if_stmt_inline = (lit('if') & p.test & lit(':') & p.simple_stmt) >> emit_if_stmt
f.ensure_parsers_defined()
