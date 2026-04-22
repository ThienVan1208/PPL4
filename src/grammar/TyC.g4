grammar TyC;

/* =========================================================================
   PARSER RULES
   ========================================================================= */

program: decl* EOF ;

decl: structDecl 
    | funcDecl 
    ;

// --- Structs ---
structDecl: STRUCT ID LBRACE structMember* RBRACE SEMI ;

structMember: type ID SEMI ;

// --- Types ---
type: INT 
    | FLOAT 
    | STRING 
    | ID 
    ;

returnType: type 
          | VOID 
          ;

// --- Functions ---
funcDecl: returnType? ID LPAREN paramList? RPAREN blockStmt ;

paramList: paramDecl (COMMA paramDecl)* ;

paramDecl: type ID ;

// --- Statements ---
stmt: varDeclStmt
    | blockStmt
    | ifStmt
    | whileStmt
    | forStmt
    | switchStmt
    | breakStmt
    | continueStmt
    | returnStmt
    | exprStmt
    ;

varDeclStmt: AUTO ID (ASSIGN expr)? SEMI
           | type ID (ASSIGN expr)? SEMI
           ;

blockStmt: LBRACE stmt* RBRACE ;

ifStmt: IF LPAREN expr RPAREN stmt (ELSE stmt)? ;

whileStmt: WHILE LPAREN expr RPAREN stmt ;

forStmt: FOR LPAREN forInit? SEMI expr? SEMI forUpdate? RPAREN stmt ;


forInit: AUTO ID (ASSIGN expr)?
       | type ID (ASSIGN expr)?
       | ID ASSIGN expr
       | expr DOT ID ASSIGN expr
       ;

forUpdate: ID ASSIGN expr
         | expr DOT ID ASSIGN expr
         | ID (INC | DEC)
         | (INC | DEC) ID
         | expr DOT ID (INC | DEC)
         | (INC | DEC) expr DOT ID
         ;

switchStmt: SWITCH LPAREN expr RPAREN LBRACE caseBlock* (defaultBlock caseBlock*)? RBRACE ;

caseBlock: CASE expr COLON stmt* ;

defaultBlock: DEFAULT COLON stmt* ;

breakStmt: BREAK SEMI ;

continueStmt: CONTINUE SEMI ;

returnStmt: RETURN expr? SEMI ;

exprStmt: expr SEMI ;

// --- Expressions ---
expr: expr DOT ID                               # memberAccessExpr
    | expr (INC | DEC)                          # postfixExpr
    | ID LPAREN argList? RPAREN                 # functionCallExpr
    | (INC | DEC | NOT | MINUS | PLUS) expr     # prefixExpr
    | expr (MUL | DIV | MOD) expr               # multiplicativeExpr
    | expr (PLUS | MINUS) expr                  # additiveExpr
    | expr (LT | LE | GT | GE) expr             # relationalExpr
    | expr (EQ | NEQ) expr                      # equalityExpr
    | expr AND expr                             # logicalAndExpr
    | expr OR expr                              # logicalOrExpr
    | <assoc=right> expr ASSIGN expr            # assignmentExpr
    | primaryExpr                               # primary
    ;

argList: expr (COMMA expr)* ;

primaryExpr: ID
           | INT_LIT
           | FLOAT_LIT
           | STRING_LIT
           | LPAREN expr RPAREN
           | LBRACE argList? RBRACE 
           ;

/* =========================================================================
   LEXER RULES
   ========================================================================= */

// --- Keywords ---
AUTO: 'auto' ;
BREAK: 'break' ;
CASE: 'case' ;
CONTINUE: 'continue' ;
DEFAULT: 'default' ;
ELSE: 'else' ;
FLOAT: 'float' ;
FOR: 'for' ;
IF: 'if' ;
INT: 'int' ;
RETURN: 'return' ;
STRING: 'string' ;
STRUCT: 'struct' ;
SWITCH: 'switch' ;
VOID: 'void' ;
WHILE: 'while' ;

// --- Operators ---
PLUS: '+' ;
MINUS: '-' ;
MUL: '*' ;
DIV: '/' ;
MOD: '%' ;
EQ: '==' ;
NEQ: '!=' ;
LT: '<' ;
GT: '>' ;
LE: '<=' ;
GE: '>=' ;
OR: '||' ;
AND: '&&' ;
NOT: '!' ;
INC: '++' ;
DEC: '--' ;
ASSIGN: '=' ;
DOT: '.' ;

// --- Separators ---
LBRACE: '{' ;
RBRACE: '}' ;
LPAREN: '(' ;
RPAREN: ')' ;
SEMI: ';' ;
COMMA: ',' ;
COLON: ':' ;

// --- Literals ---
INT_LIT: [0-9]+ ;

FLOAT_LIT: [0-9]+ '.' [0-9]* EXP?
         | '.' [0-9]+ EXP?
         | [0-9]+ EXP
         ;

fragment EXP: [eE] [+-]? [0-9]+ ;

fragment ESC: '\\' [bfrnt"\\] ;

STRING_LIT: '"' ( ESC | ~['"\\\r\n] )* '"' { self.text = self.text[1:-1] } ;

ILLEGAL_ESCAPE: '"' ( ESC | ~['"\\\r\n] )* '\\' ~[bfrnt"\\\r\n] (~['"\r\n])* '"'? {
    s = self.text[1:]
    res = ""
    i = 0
    while i < len(s):
        if s[i] == '\\' and i+1 < len(s) and s[i+1] not in 'bfrnt"\\\\':
            res += s[i:i+2]
            break
        res += s[i]
        i += 1
    self.text = "Illegal Escape " + res
} ;

UNCLOSE_STRING: '"' ( ESC | ~['"\\\r\n] )* { self.text = "Unclosed String " + self.text } ;

// --- Identifiers ---
ID: [a-zA-Z_] [a-zA-Z0-9_]* ;

// --- Comments & Whitespace ---
BLOCK_COMMENT: '/*' .*? '*/' -> skip ;
LINE_COMMENT: '//' ~[\r\n]* -> skip ;
WS: [ \t\r\n\f]+ -> skip ;

ERROR_TOKEN: . { self.text = "Error Token " + self.text } ;