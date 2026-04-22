"""
AST Generation module for TyC programming language.
This module contains the ASTGeneration class that converts parse trees
into Abstract Syntax Trees using the visitor pattern.
"""

from functools import reduce
from build.TyCVisitor import TyCVisitor
from build.TyCParser import TyCParser
from src.utils.nodes import *


class ASTGeneration(TyCVisitor):

  

    def visitProgram(self, ctx: TyCParser.ProgramContext):
        decls = [self.visit(decl) for decl in ctx.decl()]
        return Program(decls)

    def visitDecl(self, ctx: TyCParser.DeclContext):
        return self.visit(ctx.getChild(0))

    def visitStructDecl(self, ctx: TyCParser.StructDeclContext):
        name = ctx.ID().getText()
        members = [self.visit(m) for m in ctx.structMember()]
        return StructDecl(name, members)

    def visitStructMember(self, ctx: TyCParser.StructMemberContext):
        member_type = self.visit(ctx.type_())
        name = ctx.ID().getText()
        return MemberDecl(member_type, name)

    def visitFuncDecl(self, ctx: TyCParser.FuncDeclContext):
        return_type = self.visit(ctx.returnType()) if ctx.returnType() else None
        name = ctx.ID().getText()
        params = self.visit(ctx.paramList()) if ctx.paramList() else []
        body = self.visit(ctx.blockStmt())
        return FuncDecl(return_type, name, params, body)

    def visitParamList(self, ctx: TyCParser.ParamListContext):
        return [self.visit(p) for p in ctx.paramDecl()]

    def visitParamDecl(self, ctx: TyCParser.ParamDeclContext):
        return Param(self.visit(ctx.type_()), ctx.ID().getText())


    def visitType(self, ctx: TyCParser.TypeContext):
        if ctx.INT():
            return IntType()
        elif ctx.FLOAT():
            return FloatType()
        elif ctx.STRING():
            return StringType()
        elif ctx.ID():
            return StructType(ctx.ID().getText())

    def visitReturnType(self, ctx: TyCParser.ReturnTypeContext):
        if ctx.VOID():
            return VoidType()
        return self.visit(ctx.type_())



    def visitStmt(self, ctx: TyCParser.StmtContext):
        return self.visit(ctx.getChild(0))

    def visitVarDeclStmt(self, ctx: TyCParser.VarDeclStmtContext):
        name = ctx.ID().getText()
        var_type = self.visit(ctx.type_()) if ctx.type_() else None
        init_value = self.visit(ctx.expr()) if ctx.expr() else None
        return VarDecl(var_type, name, init_value)

    def visitBlockStmt(self, ctx: TyCParser.BlockStmtContext):
        return BlockStmt([self.visit(s) for s in ctx.stmt()])

    def visitIfStmt(self, ctx: TyCParser.IfStmtContext):
        condition = self.visit(ctx.expr())
        then_stmt = self.visit(ctx.stmt(0))
        else_stmt = self.visit(ctx.stmt(1)) if ctx.ELSE() else None
        return IfStmt(condition, then_stmt, else_stmt)

    def visitWhileStmt(self, ctx: TyCParser.WhileStmtContext):
        return WhileStmt(self.visit(ctx.expr()), self.visit(ctx.stmt()))

    def visitForStmt(self, ctx: TyCParser.ForStmtContext):
        init = self.visit(ctx.forInit()) if ctx.forInit() else None
        condition = self.visit(ctx.expr()) if ctx.expr() else None
        update = self.visit(ctx.forUpdate()) if ctx.forUpdate() else None
        body = self.visit(ctx.stmt())
        return ForStmt(init, condition, update, body)

    def visitForInit(self, ctx: TyCParser.ForInitContext):
        if ctx.AUTO():
            name = ctx.ID().getText()
            init_value = self.visit(ctx.expr(0)) if ctx.expr() else None
            return VarDecl(None, name, init_value)
            
        elif ctx.type_():
            name = ctx.ID().getText()
            var_type = self.visit(ctx.type_())
            init_value = self.visit(ctx.expr(0)) if ctx.expr() else None
            return VarDecl(var_type, name, init_value)
            
        elif ctx.DOT():
            lhs = MemberAccess(self.visit(ctx.expr(0)), ctx.ID().getText())
            rhs = self.visit(ctx.expr(1))
            return ExprStmt(AssignExpr(lhs, rhs))
            
        else:
            lhs = Identifier(ctx.ID().getText())
            rhs = self.visit(ctx.expr(0))
            return ExprStmt(AssignExpr(lhs, rhs))

    def visitForUpdate(self, ctx: TyCParser.ForUpdateContext):
        if ctx.ASSIGN():
            if ctx.DOT():
                lhs = MemberAccess(self.visit(ctx.expr(0)), ctx.ID().getText())
                rhs = self.visit(ctx.expr(1))
            else:
                lhs = Identifier(ctx.ID().getText())
                rhs = self.visit(ctx.expr(0))
            return AssignExpr(lhs, rhs)
            
        else:
            op = ctx.INC().getText() if ctx.INC() else ctx.DEC().getText()
            
            if ctx.DOT():
                operand = MemberAccess(self.visit(ctx.expr(0)), ctx.ID().getText())
            else:
                operand = Identifier(ctx.ID().getText())
                
            is_prefix = ctx.getChild(0).getText() in ['++', '--']
            
            if is_prefix:
                return PrefixOp(op, operand)
            else:
                return PostfixOp(op, operand)

    def visitSwitchStmt(self, ctx: TyCParser.SwitchStmtContext):
        expr = self.visit(ctx.expr())
        cases = [self.visit(c) for c in ctx.caseBlock()] if ctx.caseBlock() else []
        default_case = self.visit(ctx.defaultBlock()) if ctx.defaultBlock() else None
        return SwitchStmt(expr, cases, default_case)

    def visitCaseBlock(self, ctx: TyCParser.CaseBlockContext):
        statements = [self.visit(s) for s in ctx.stmt()]
        return CaseStmt(self.visit(ctx.expr()), statements)

    def visitDefaultBlock(self, ctx: TyCParser.DefaultBlockContext):
        statements = [self.visit(s) for s in ctx.stmt()]
        return DefaultStmt(statements)

    def visitBreakStmt(self, ctx: TyCParser.BreakStmtContext):
        return BreakStmt()

    def visitContinueStmt(self, ctx: TyCParser.ContinueStmtContext):
        return ContinueStmt()

    def visitReturnStmt(self, ctx: TyCParser.ReturnStmtContext):
        expr = self.visit(ctx.expr()) if ctx.expr() else None
        return ReturnStmt(expr)

    def visitExprStmt(self, ctx: TyCParser.ExprStmtContext):
        return ExprStmt(self.visit(ctx.expr()))


    def visitMemberAccessExpr(self, ctx: TyCParser.MemberAccessExprContext):
        return MemberAccess(self.visit(ctx.expr()), ctx.ID().getText())

    def visitPostfixExpr(self, ctx: TyCParser.PostfixExprContext):
        op = ctx.INC().getText() if ctx.INC() else ctx.DEC().getText()
        return PostfixOp(op, self.visit(ctx.expr()))

    def visitFunctionCallExpr(self, ctx: TyCParser.FunctionCallExprContext):
        name = ctx.ID().getText()
        args = self.visit(ctx.argList()) if ctx.argList() else []
        return FuncCall(name, args)

    def visitArgList(self, ctx: TyCParser.ArgListContext):
        return [self.visit(e) for e in ctx.expr()]

    def visitPrefixExpr(self, ctx: TyCParser.PrefixExprContext):
        op = ctx.getChild(0).getText()
        return PrefixOp(op, self.visit(ctx.expr()))

    def _visitBinaryOp(self, ctx):
        left = self.visit(ctx.expr(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.expr(1))
        return BinaryOp(left, op, right)

    def visitMultiplicativeExpr(self, ctx: TyCParser.MultiplicativeExprContext):
        return self._visitBinaryOp(ctx)

    def visitAdditiveExpr(self, ctx: TyCParser.AdditiveExprContext):
        return self._visitBinaryOp(ctx)

    def visitRelationalExpr(self, ctx: TyCParser.RelationalExprContext):
        return self._visitBinaryOp(ctx)

    def visitEqualityExpr(self, ctx: TyCParser.EqualityExprContext):
        return self._visitBinaryOp(ctx)

    def visitLogicalAndExpr(self, ctx: TyCParser.LogicalAndExprContext):
        return self._visitBinaryOp(ctx)

    def visitLogicalOrExpr(self, ctx: TyCParser.LogicalOrExprContext):
        return self._visitBinaryOp(ctx)

    def visitAssignmentExpr(self, ctx: TyCParser.AssignmentExprContext):
        lhs = self.visit(ctx.expr(0))
        rhs = self.visit(ctx.expr(1))
        return AssignExpr(lhs, rhs)

    def visitPrimary(self, ctx: TyCParser.PrimaryContext):
        return self.visit(ctx.primaryExpr())

    def visitPrimaryExpr(self, ctx: TyCParser.PrimaryExprContext):
        if ctx.ID():
            return Identifier(ctx.ID().getText())
        elif ctx.INT_LIT():
            return IntLiteral(int(ctx.INT_LIT().getText()))
        elif ctx.FLOAT_LIT():
            return FloatLiteral(float(ctx.FLOAT_LIT().getText()))
        elif ctx.STRING_LIT():
            return StringLiteral(ctx.STRING_LIT().getText())
        elif ctx.LPAREN():
            return self.visit(ctx.expr())
        elif ctx.LBRACE():
            args = self.visit(ctx.argList()) if ctx.argList() else []
            return StructLiteral(args)