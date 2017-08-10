from derp.ast import AST


FunnelModule = AST.subclass("FunnelModule", "types")
FunnelType = AST.subclass("FunnelType", "name body")
FieldType = AST.subclass("FieldType", "name")
Docstring = AST.subclass("Docstring", "string")

EnumField = FieldType.subclass("EnumField", "options")
IDField = FieldType.subclass("IDField", "type")

Nullable = AST.subclass("Nullable", "field")
Array = AST.subclass("Array", "field subscript")
Default = AST.subclass("Default", "field value")
ArraySubscript = AST.subclass("ArraySubscript", "length")
Block = AST.subclass("Block", "body")
FormBlock = Block.subclass("FormBlock")
ValidateBlock = Block.subclass("ValidateBlock")