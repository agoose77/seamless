from derp.ast import AST


FunnelModule = AST.subclass("FunnelModule", "types")
FunnelType = AST.subclass("FunnelType", "name body")
Docstring = AST.subclass("Docstring", "string")

Field = AST.subclass("Field", "name type")
DefaultField = Field.subclass("DefaultField", "default")
OptionalField = Field.subclass("OptionalField")

ArrayType = AST.subclass("ArrayType", "etype length")
EnumType = AST.subclass("EnumType", "options")
GenericType = AST.subclass("GenericType", "id")

ArraySubscript = AST.subclass("ArraySubscript", "length")

Block = AST.subclass("Block", "body")
FormBlock = Block.subclass("FormBlock")
ValidateBlock = Block.subclass("ValidateBlock")