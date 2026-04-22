"""
Static Semantic Checker for TyC Programming Language

This module implements a comprehensive static semantic checker using visitor pattern
for the TyC procedural programming language. It performs type checking,
scope management, type inference, and detects all semantic errors as
specified in the TyC language specification.
"""

from functools import reduce
from typing import (
    Dict,
    List,
    Set,
    Optional,
    Any,
    Tuple,
    NamedTuple,
    Union,
    TYPE_CHECKING,
)
from ..utils.visitor import ASTVisitor
from ..utils.nodes import (
    ASTNode,
    Program,
    StructDecl,
    MemberDecl,
    FuncDecl,
    Param,
    VarDecl,
    IfStmt,
    WhileStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
    ReturnStmt,
    BlockStmt,
    SwitchStmt,
    CaseStmt,
    DefaultStmt,
    Type,
    IntType,
    FloatType,
    StringType,
    VoidType,
    StructType,
    BinaryOp,
    PrefixOp,
    PostfixOp,
    AssignExpr,
    MemberAccess,
    FuncCall,
    Identifier,
    StructLiteral,
    IntLiteral,
    FloatLiteral,
    StringLiteral,
    ExprStmt,
    Expr,
    Stmt,
    Decl,
)

# Type aliases for better type hints
TyCType = Union[IntType, FloatType, StringType, VoidType, StructType]
from .static_error import (
    StaticError,
    Redeclared,
    UndeclaredIdentifier,
    UndeclaredFunction,
    UndeclaredStruct,
    TypeCannotBeInferred,
    TypeMismatchInStatement,
    TypeMismatchInExpression,
    MustInLoop,
)

class AutoType:
    """Internal placeholder for an `auto` variable that hasn't been inferred yet."""
    def __init__(self, name: str, node: ASTNode):
        self.name = name
        self.node = node

class StaticChecker(ASTVisitor):
    # Region: Const var
    ER_STRUCT_STR = 'Struct'
    STRUCT_MEMBERS_STR = 'members'

    ER_VAR_STR = 'Variable'
    ER_MEMBER_STR = 'Member'
    
    ER_FUNC_STR = 'Function'
    FUNC_PARAM_STR = 'params'
    ER_PARAM_STR = 'Parameter'
    RET_TYPE_STR = 'ret_type'
    # End Region

    def __init__(self):
        super().__init__()
        """
        - The first str is the struct's name.
        - The second str represents for fields name.
        - The Any type is the type of a specific field.
        
        EX:
        struct: "User": 
            "members":
            {
                "name": "string",
                "age": "int",
                "is_active": "boolean"
            }
        """
        self.struct_table: Dict[str, Dict[str, Any]] = {}


        """
        - The fist str is function's name.
        - The second str represents for fields name.
        - The Any type is the type of a specific field.
        
        EX:
        func "add": {
            "params": [IntType(), FloatType()],
            "ret_type": IntType(),
            "is_auto": False
        }
        """
        self.func_table: Dict[str, Dict[str, Any]] = {
            "readInt": {self.FUNC_PARAM_STR: [], self.RET_TYPE_STR: IntType()},
            "readFloat": {self.FUNC_PARAM_STR: [], self.RET_TYPE_STR: FloatType()},
            "readString": {self.FUNC_PARAM_STR: [], self.RET_TYPE_STR: StringType()},
            "printInt": {self.FUNC_PARAM_STR: [IntType()], self.RET_TYPE_STR: VoidType()},
            "printFloat": {self.FUNC_PARAM_STR: [FloatType()], self.RET_TYPE_STR: VoidType()},
            "printString": {self.FUNC_PARAM_STR: [StringType()], self.RET_TYPE_STR: VoidType()},
        }


        """
        - A stack of scope.
        EX:
        - Input:
        void main(int param1) {
            int x = 10;
            if (x > 5) {
                float y = 3.14;
            }
        }
        - Scope:
        [
            {"param1": IntType(), "x": IntType()},  # Index 0: Function-level scope
            {"y": FloatType()}                      # Index 1: Inner 'if' block scope
        ]
        """
        self.scope_table: List[Dict[str, Any]] = [] 


        self.loop_depth = 0  # To track if it is inside a loop for break/continue statements
        self.switch_depth = 0  # To track if it is inside a switch for break statements
        self.cur_func_name = ''  # To track current function for return statement checking
        self.cur_func_params: Set[str] = set() # To track current function's parameters for protection


    def check_program(self, node: Program):
        return self.visit(node)


    # =========================================================================
    # Helper Methods
    # =========================================================================
    def check_condition_expr(self, expr: Expr, stmt_node: Optional[Stmt] = None):
        if not expr: return

        cond_type = self.visit(expr)
        if isinstance(cond_type, AutoType):
            self.resolve_auto_type(cond_type.name, IntType())
            cond_type = IntType()
        if not isinstance(cond_type, IntType):
            raise TypeMismatchInExpression(stmt_node)
        

    def check_unsolved_autos(self):
        for _, var_type in self.scope_table[-1].items():
            if isinstance(var_type, AutoType):
                raise TypeCannotBeInferred(var_type.node)    
            

    def is_same_type(self, type1, type2) -> bool:
        if type(type1) != type(type2):
            return False
        
        if isinstance(type1, StructType) and isinstance(type2, StructType):
            return type1.struct_name == type2.struct_name
        
        return True
            
    def resolve_auto_type(self, name: str, inferred_type: Any) -> bool:
        for scope in reversed(self.scope_table):
            if name in scope and isinstance(scope[name], AutoType):
                scope[name] = inferred_type
                return True
        return False
    

    # =========================================================================
    # Program and Top-level Declarations
    # =========================================================================

    def visit_program(self, node: "Program", o: Any = None):
        for decl in node.decls:
            self.visit(decl)


    def visit_struct_decl(self, node: "StructDecl", o: Any = None):
        # Check that struct name is exist
        if node.name in self.struct_table:
            raise Redeclared(self.ER_STRUCT_STR, node.name)
        
        # Check that field names and types are distinct in struct
        self.struct_table[node.name] = {self.STRUCT_MEMBERS_STR : {}}
        member_names = set()

        for member in node.members:
            # Check name
            if member.name in member_names:
                raise Redeclared(self.ER_MEMBER_STR, member.name)
            member_names.add(member.name)

            # Check struct type
            if isinstance(member.member_type, StructType):
                if member.member_type.struct_name not in self.struct_table:
                    raise UndeclaredStruct(member.member_type.struct_name)
            
            member_type = self.visit(member.member_type)
            self.struct_table[node.name][self.STRUCT_MEMBERS_STR][member.name] = member_type


    def visit_member_decl(self, node: "MemberDecl", o: Any = None):
        return self.visit(node.member_type)        


    def visit_func_decl(self, node: "FuncDecl", o: Any = None):
        # Check that func name is exist?
        if node.name in self.func_table:
            raise Redeclared(self.ER_FUNC_STR, node.name)
        
        self.cur_func_name = node.name

        # Get return type and init in func_table
        return_type = self.visit(node.return_type) if node.return_type else None
        self.func_table[self.cur_func_name] = {
            self.FUNC_PARAM_STR : [],
            self.RET_TYPE_STR : return_type
        }

        # Create new scope for func
        self.scope_table.append({})
        param_types = []
        
        # Check and add params to new scope
        cur_scope = self.scope_table[-1]
        for param in node.params:
            if param.name in cur_scope:
                raise Redeclared(self.ER_PARAM_STR, param.name)
            
            param_type = self.visit(param.param_type)
            # Check if param_type is struct and not declared 
            if isinstance(param_type, StructType) and param_type.struct_name not in self.struct_table:
                raise UndeclaredStruct(param_type.struct_name)
            
            cur_scope[param.name] = param_type
            param_types.append(param_type)

        self.func_table[self.cur_func_name][self.FUNC_PARAM_STR] = param_types
        self.cur_func_params = set(cur_scope.keys())

        # Visit the body (parameters are already in the top scope)
        self.visit(node.body)

        # Function arguments can not be auto type after checking body?
        # Actually spec says check during declaration if they have types, which they must.
        self.check_unsolved_autos()

        if self.func_table[self.cur_func_name][self.RET_TYPE_STR] is None:
            self.func_table[self.cur_func_name][self.RET_TYPE_STR] = VoidType()

        # Exit the func scope
        self.scope_table.pop()
        self.cur_func_params = set()
        self.cur_func_name = ''
        

    def visit_param(self, node: "Param", o: Any = None):
        return self.visit(node.param_type, o)
        

    # =========================================================================
    # Type System
    # =========================================================================
    def visit_int_type(self, node: "IntType", o: Any = None):
        return IntType()

    def visit_float_type(self, node: "FloatType", o: Any = None):
        return FloatType()

    def visit_string_type(self, node: "StringType", o: Any = None):
        return StringType()

    def visit_void_type(self, node: "VoidType", o: Any = None):
        return VoidType()

    def visit_struct_type(self, node: "StructType", o: Any = None):
        if node.struct_name not in self.struct_table:
            raise UndeclaredStruct(node.struct_name)
        return StructType(node.struct_name)


    # =========================================================================
    # Statements
    # =========================================================================
    def visit_block_stmt(self, node: "BlockStmt", o: Any = None):
        # Create new scope for block
        self.scope_table.append({})

        for stmt in node.statements:
            self.visit(stmt)

        self.check_unsolved_autos()

        # Exit the block scope
        self.scope_table.pop()
        

    def visit_var_decl(self, node: "VarDecl", o: Any = None):
        cur_scope = self.scope_table[-1]

        if node.name in cur_scope:
            raise Redeclared(self.ER_VAR_STR, node.name)
        
        # TyC Rule: local variable cannot reuse a parameter name in the same function
        if node.name in self.cur_func_params:
            raise Redeclared(self.ER_VAR_STR, node.name)
        
        var_type = self.visit(node.var_type) if node.var_type else None
        
        # var_type has initial value
        if node.init_value:
            # If there are Point(int x, int y) and Vector2(intx, int y) then define auto x = {1, 2}
            # => Type of x can not be inferred because it can be either Point or Vector2
            if var_type is None and isinstance(node.init_value, StructLiteral):
                raise TypeCannotBeInferred(node)
            
            # rhs_type will be proccessed in visit Expr
            rhs_type = self.visit(node.init_value, var_type)

            # var_type is Auto
            if var_type is None:
                # If rhs type is also Auto => Type of var can not be inferred
                if isinstance(rhs_type, AutoType):
                    raise TypeCannotBeInferred(node)
                
                # If rhs type is not Auto => var_type can be inferred from rhs_type
                var_type = rhs_type

            # var_type is not Auto
            else:
                # If rhs_type is Auto => rhs_type can be inferred from var_type
                if isinstance(rhs_type, AutoType):
                    if not self.resolve_auto_type(rhs_type.name, var_type):
                        raise TypeCannotBeInferred(node)

                # rhs_type is not Auto => Check if var_type and rhs_type are the same
                elif not self.is_same_type(var_type, rhs_type):
                    raise TypeMismatchInStatement(node)
        
        # var_type has no initial value
        else:
            if var_type is None:
                var_type = AutoType(node.name, node)

        cur_scope[node.name] = var_type

        
    def visit_if_stmt(self, node: "IfStmt", o: Any = None):
        self.check_condition_expr(node.condition, node)
        self.visit(node.then_stmt)
        if node.else_stmt:
            self.visit(node.else_stmt)

    def visit_while_stmt(self, node: "WhileStmt", o: Any = None):
        self.check_condition_expr(node.condition, node)
        self.loop_depth += 1
        self.visit(node.body)
        self.loop_depth -= 1
        

    def visit_for_stmt(self, node: "ForStmt", o: Any = None):
        self.scope_table.append({})
        if node.init:
            self.visit(node.init)
        if node.condition:
            self.check_condition_expr(node.condition, node)
        if node.update:
            self.visit(node.update)

        self.loop_depth += 1
        self.visit(node.body)
        self.loop_depth -= 1

        self.check_unsolved_autos()
        self.scope_table.pop()


    def visit_switch_stmt(self, node: "SwitchStmt", o: Any = None):
        self.check_condition_expr(node.expr, node)
        self.switch_depth += 1
        for case in node.cases:
            self.visit(case)
        if node.default_case:
            self.visit(node.default_case)
        self.switch_depth -= 1
        

    def visit_case_stmt(self, node: "CaseStmt", o: Any = None):
        self.check_condition_expr(node.expr, node)
        for stmt in node.statements:
            self.visit(stmt)
        

    def visit_default_stmt(self, node: "DefaultStmt", o: Any = None):
        for stmt in node.statements:
            self.visit(stmt)


    def visit_break_stmt(self, node: "BreakStmt", o: Any = None):
        if self.loop_depth == 0 and self.switch_depth == 0:
            raise MustInLoop(node)


    def visit_continue_stmt(self, node: "ContinueStmt", o: Any = None):
        if self.loop_depth == 0:
            raise MustInLoop(node)


    def visit_return_stmt(self, node: "ReturnStmt", o: Any = None):
        if self.cur_func_name == '':
            raise UndeclaredFunction(node)

        expected_return_type = self.func_table[self.cur_func_name][self.RET_TYPE_STR]
        # actual_return_type will be proccessed in visit Expr
        # If expected is None (auto return), we pass None as context
        actual_return_type = self.visit(node.expr, expected_return_type) if node.expr else VoidType()

        # Handle function return type inference
        if expected_return_type is None:
            # First return statement defines the function's return type
            self.func_table[self.cur_func_name][self.RET_TYPE_STR] = actual_return_type
            expected_return_type = actual_return_type

        if isinstance(expected_return_type, AutoType) and isinstance(actual_return_type, AutoType):
            raise TypeCannotBeInferred(node)
        
        if isinstance(expected_return_type, AutoType):
            if not self.resolve_auto_type(expected_return_type.name, actual_return_type):
                raise TypeCannotBeInferred(node)
            expected_return_type = actual_return_type

        if isinstance(actual_return_type, AutoType):
            if not self.resolve_auto_type(actual_return_type.name, expected_return_type):
                raise TypeCannotBeInferred(node)
            actual_return_type = expected_return_type

        if not self.is_same_type(expected_return_type, actual_return_type):
            raise TypeMismatchInStatement(node)


    def visit_expr_stmt(self, node: "ExprStmt", o: Any = None):
        expr_type = self.visit(node.expr, o)
        if isinstance(expr_type, AutoType):
            raise TypeCannotBeInferred(node)


    # Expressions
    def visit_binary_op(self, node: "BinaryOp", o: Any = None):
        left_type = self.visit(node.left, o)
        right_type = self.visit(node.right, o)

        if isinstance(left_type, AutoType) and isinstance(right_type, AutoType):
            raise TypeCannotBeInferred(node)
        
        if node.operator in ['+', '-', '*', '/', '==', '!=', '>', '<', '>=', '<=']:
            if isinstance(left_type, AutoType) or isinstance(right_type, AutoType):
                raise TypeCannotBeInferred(node)
            
            if isinstance(left_type, (IntType, FloatType)) and isinstance(right_type, (IntType, FloatType)):
                if node.operator in ['==', '!=', '>', '<', '>=', '<=']:
                    return IntType()
                else:
                    if isinstance(left_type, FloatType) or isinstance(right_type, FloatType):
                        return FloatType()
                    return IntType()
            else:
                raise TypeMismatchInExpression(node)
            
        elif node.operator == '%':
            if isinstance(left_type, AutoType):
                self.resolve_auto_type(left_type.name, IntType())
                left_type = IntType()
            if isinstance(right_type, AutoType):
                self.resolve_auto_type(right_type.name, IntType())
                right_type = IntType()
            
            if isinstance(left_type, IntType) and isinstance(right_type, IntType):
                return IntType()
            else:
                raise TypeMismatchInExpression(node)

        elif node.operator in ['&&', '||']:
            if isinstance(left_type, AutoType):
                self.resolve_auto_type(left_type.name, IntType())
                left_type = IntType()
            if isinstance(right_type, AutoType):
                self.resolve_auto_type(right_type.name, IntType())
                right_type = IntType()
            
            if isinstance(left_type, IntType) and isinstance(right_type, IntType):
                return IntType()
            else:
                raise TypeMismatchInExpression(node)
            
        

    def visit_prefix_op(self, node: "PrefixOp", o: Any = None):
        if node.operator in ['+', '-']:
            operand_type = self.visit(node.operand)
            if isinstance(operand_type, AutoType):
                # self.resolve_auto_type(operand_type.name, IntType())
                # operand_type = IntType()
                raise TypeCannotBeInferred(node)
            
            if not isinstance(operand_type, (IntType, FloatType)):
                raise TypeMismatchInExpression(node)
            return operand_type
        
        elif node.operator == '!':
            operand_type = self.visit(node.operand)
            if isinstance(operand_type, AutoType):
                self.resolve_auto_type(operand_type.name, IntType())
                operand_type = IntType()
            if not isinstance(operand_type, IntType):
                raise TypeMismatchInExpression(node)
            return operand_type

        elif node.operator in ['++', '--']:
            if not isinstance(node.operand, (Identifier, MemberAccess)):
                raise TypeMismatchInExpression(node)
            operand_type = self.visit(node.operand)
            if isinstance(operand_type, AutoType):
                self.resolve_auto_type(operand_type.name, IntType())
                operand_type = IntType()
            if not isinstance(operand_type, IntType):
                raise TypeMismatchInExpression(node)
            return operand_type
        

    def visit_postfix_op(self, node: "PostfixOp", o: Any = None):
        if not isinstance(node.operand, (Identifier, MemberAccess)):
            raise TypeMismatchInExpression(node)
        operand_type = self.visit(node.operand)
        if isinstance(operand_type, AutoType):
            self.resolve_auto_type(operand_type.name, IntType())
            operand_type = IntType()
        if not isinstance(operand_type, IntType):
            raise TypeMismatchInExpression(node)
        return operand_type


    def visit_assign_expr(self, node: "AssignExpr", o: Any = None):
        if not isinstance(node.lhs, (Identifier, MemberAccess)):
            raise TypeMismatchInExpression(node)
        
        left_type = self.visit(node.lhs, o)
        right_type = self.visit(node.rhs, left_type)

        if isinstance(left_type, AutoType) and isinstance(right_type, AutoType):
            raise TypeCannotBeInferred(node)

        if isinstance(left_type, AutoType):
            if not self.resolve_auto_type(left_type.name, right_type):
                raise TypeCannotBeInferred(node)
            
            left_type = right_type

        if isinstance(right_type, AutoType):
            if not self.resolve_auto_type(right_type.name, left_type):
                raise TypeCannotBeInferred(node)
            
            right_type = left_type

        if not self.is_same_type(left_type, right_type):
            raise TypeMismatchInExpression(node)
        
        return left_type
    

    def visit_member_access(self, node: "MemberAccess", o: Any = None):
        # Ex: p.x => obj is p, obj_type is type of p, member_name is x
        obj_type = self.visit(node.obj, o)

        if isinstance(obj_type, AutoType):
            # Can not infer type of obj if it is auto, because it can be any struct that has the member
            raise TypeCannotBeInferred(node)

        if not isinstance(obj_type, StructType):
            raise TypeMismatchInExpression(node)
        
        struct_info = self.struct_table[obj_type.struct_name]
        if node.member not in struct_info[self.STRUCT_MEMBERS_STR]:
            raise TypeMismatchInExpression(node)
        
        return struct_info[self.STRUCT_MEMBERS_STR][node.member]

    def visit_func_call(self, node: "FuncCall", o: Any = None):
        if node.name not in self.func_table:
            raise UndeclaredFunction(node.name)

        for func_name, func_info in self.func_table.items():
            if func_name == node.name:
                param_types = func_info[self.FUNC_PARAM_STR]
                if len(param_types) != len(node.args):
                    raise TypeMismatchInExpression(node)
                
                for arg, param_type in zip(node.args, param_types):
                    arg_type = self.visit(arg, param_type)
                    if isinstance(arg_type, AutoType):
                        if not self.resolve_auto_type(arg_type.name, param_type):
                            raise TypeCannotBeInferred(node)
                    elif not self.is_same_type(arg_type, param_type):
                        raise TypeMismatchInExpression(node)

                ret_type = func_info[self.RET_TYPE_STR]
                if ret_type is None:
                    raise TypeCannotBeInferred(node)
                return ret_type
        

    def visit_identifier(self, node: "Identifier", o: Any = None):
        for scope in reversed(self.scope_table):
            if node.name in scope:
                var_type = scope[node.name]
                return var_type
            
        raise UndeclaredIdentifier(node.name)
    
    
    # o is expected type of struct literal, used for type inference and checking
    # Should return o 
    def visit_struct_literal(self, node: "StructLiteral", o: Any = None):
        if isinstance(o, AutoType):
            raise TypeCannotBeInferred(node)
            
        if not isinstance(o, StructType):
            raise TypeMismatchInExpression(node)
        
        struct_type = self.struct_table[o.struct_name]
        if not struct_type:
            raise UndeclaredStruct(o.struct_name)
        
        struct_members = struct_type[self.STRUCT_MEMBERS_STR]
        if len(struct_members) != len(node.values):
            raise TypeMismatchInExpression(node)
        
        type_members = list(struct_members.values())
        for val, type_member in zip(node.values, type_members):
            val_type = self.visit(val, type_member)
            if isinstance(val_type, AutoType):
                if not self.resolve_auto_type(val_type.name, type_member):
                    raise TypeCannotBeInferred(node)
            elif not self.is_same_type(val_type, type_member):
                raise TypeMismatchInExpression(node)

        return o


        

    # =========================================================================
    # Literals
    # =========================================================================
    def visit_int_literal(self, node: "IntLiteral", o: Any = None):
        return IntType()


    def visit_float_literal(self, node: "FloatLiteral", o: Any = None):
        return FloatType()

    def visit_string_literal(self, node: "StringLiteral", o: Any = None):
        return StringType()
