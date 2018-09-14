RBNF=\
r"""
import std.common.[Space Name DoubleQuotedStr]
ignore [Space comment]
[python] import reley.expr_based_ast.[*]
[python] import reley.helper.[*]
[python] import functools.[*]


comment := R'(--.*)|(((\{\-\|)+?[\w\W]+?(\-\})+))'
docstr  := R'(\|\|\|.*)'
num := R'0[Xx][\da-fA-F]+|\d+(?:\.\d+|)(?:E\-{0,1}\d+|)'
lam := R'\\'

to_const cast := 'type' 'fn' 'def' '->' 'import' 'module'
                 '[|' '|]'
                 '{|' '|}'
                 'return' 'if' 'else' 'let' 'or' 'and' 'not' 'xor' 'where' 'as'
                 '..' '::' 'in' '<-' 'then' 'infix' '=='

doc ::= items=docstr+ -> Doc(loc@items[0], '\n'.join(each.value[3:] for each in items))
identifier ::= mark=Name | '(' as mark ID=binOp ')' -> Operator(loc @ mark, ID.name if ID else mark.value)

def_lambda ::= mark=lam fn=lambda_trailer -> Lam(loc @ mark, None, fn.args, fn.body)

lambda_trailer ::= (mark='(' [args=arguments] ')' | args=(mark=arg){1 1}) ('->' body=expr_stmts |  body=lambda_trailer)
                   -> Lam(loc @ mark, None, args or (), body)

define     ::= [doc=doc] id=identifier fn=fun_trailer
               ->
                  if isinstance(fn, Lam):
                    return DefFun(loc @ id, id.name, fn.args, fn.body, doc)
                  else:
                    return DefVar(loc @ id, id.name, fn)

fun_trailer ::= '=' body=expr_stmts | ((mark='(' [args=arguments] ')' | args=(mark=arg){1 1}) fun=fun_trailer)
                ->  Lam(loc @ mark, None, args or (), fun) if fun else body

defty ::= mark='type' id=identifier '=' ty=ty  -> DefTy(loc @ mark, id.name, ty)

arguments ::= head=arg tail=(',' arg)* -> [head, *tail[1::2]]

arg   ::= name=Name [':' ty=ty] -> Arg(loc @ name, name.value, ty)

ty    ::= it=expr -> it


alias_pair ::= imp_name=Name ['as' name=Name] -> Alias(loc @ imp_name, imp_name.value, name.value if name else imp_name.value)

dot_lst ::= head=alias_pair tail=(',' alias_pair)* -> (head, *tail[1::2])

import_ ::= mark='import' names=(Name ('.' Name)*) ['as' name=Name] ['(' lst=dot_lst ')']
           -> imp_name = ''.join(map(lambda _: _.value, names))
              name = name.value if name else None
              if not lst and not name: name = imp_name
              Import(loc @ mark, imp_name, name, lst)

infix ::= mark='infix' precedence=num op=identifier -> Infix(loc @ mark, eval(precedence.value), op.name)

expr ::=| BIN=expr (binOp expr)+ as tail
        | JUST=factor
        ->  if BIN : return BinSeq(loc @ BIN, [BIN, *tail]) if tail else BIN
            return JUST

binOp   ::=
        | ('or' | '-' | 'and') as basic
        | '`' names=(~'`')+ '`'
        | ('*' | '^' | '%' | '&' | '@' | '$' | '+' | '/' | '|' | '>' | '<' | '==' | '~' | '.' | '?' | '!' | '::')+ as seq
        -> bin_op_rewrite(state.ctx.get)

factor ::= [neg='-'] call=call -> Call(loc @ neg, Symbol(loc@neg, "neg"), call) if neg else call

call ::= leader=atom tail=(atom{is_indented})*
         ->  reduce(lambda a, b: Call(loc @ a, a, b), tail, leader)

atom ::= | '{|' as mark expr_stmts '|}'
         | SYMBOL=identifier
         | IF='if' cond=expr 'then' iftrue=expr_stmts 'else' iffalse=expr_stmts
         | LET='let' stmts=stmts 'in' out=expr_stmts
         | RET='return' [expr=expr_stmts]
         | YIELD='yield' [expr=expr_stmts]
         | STRS=DoubleQuotedStr+
         | NUM=num
         | LITERAL=literal
         -> atom_rewrite(state.ctx.get)

tuple ::= '(' as mark [head=expr tail=(',' expr)*] ')'
          -> if tail: return Tuple(loc @ mark, (head, *tail[1::2]))
             if head:
                head.loc.update(*(loc @ mark))
                return head
             Void(loc@mark)
list  ::= '[' as mark  [head=expr tail=(',' expr)*] ']' -> HList(loc @ mark, (head, *tail[1::2]) if head else ())

set   ::= '{' as mark head=expr tail=(',' expr)* '}' -> HDict(loc @ mark, make_set(head, *tail[1::2]))

dict  ::= '{' as mark head=pair tail=(',' pair)* '}' -> HDict(loc @ mark, (head, *tail[1::2]))

pair  ::= key=expr ':' value=expr -> (key, value)

literal ::= it=(tuple | list | set | dict | def_lambda) -> it

suites     ::= '{|' as mark expr=expr_stmts '|}'
               -> expr.loc.update(*(loc @ mark))
                  expr

expr_stmt  ::= expr=expr [';'] -> expr

expr_stmts ::= (leader=expr_stmt [(expr_stmt{is_aligned})+] as tail | '{|' expr_stmt+ as no_indented '|}') ['where' stmts=stmts]
             -> suite = Suite(loc @ leader, no_indented or [leader, *tail])
                if stmts:
                  return Where(loc @ leader, suite, stmts)
                suite
stmt   ::=
       | it=import_[';']
       | it=define [';']
       | it=defty  [';']
       | it=infix  [';']
       -> it

stmts  ::= leader=stmt [(stmt{is_aligned})+] as tail | '{|' stmt+ as no_indented '|}'
           -> Definition(loc @ leader, no_indented or [leader, *tail])

module ::= [[doc=doc] 'module' [ exports=identifier+ ] 'where'] it=stmts -> Module(it, doc, exports)

"""
