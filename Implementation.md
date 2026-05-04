# Complete Codegen and Emitter Implementation

This plan outlines the steps to implement the missing components in the Code Generator and Emitter to support all TyC language features, producing functional JVM Jasmin bytecode for Assignment 4.

## User Review Required
Please review the changes below, which cover the complete set of TODOs and missing functionalities for loops, short-circuiting logic, struct handling, and assignments.

## Open Questions
- TyC's postfix operations (`++`, `--`) require the original value to be the result of the expression, while updating the variable. I will emit JVM instructions such that for `x++`, it pushes `x`, duplicates it, pushes `1`, adds them, and stores it back in `x`, leaving the old `x` on the stack. For `++x`, it will push `x`, push `1`, add, duplicate, and store back. 
- Is there any specific directory for generated `.j` struct files? I assume they should be created in the exact same output directory as `TyC.j` (which is `src/runtime/`).

## Proposed Changes

### 1. `src/codegen/emitter.py`
Add necessary missing emitters for Struct fields, class definitions, string concatenation, and logic operations.

#### [MODIFY] [emitter.py](file:///e:/School/3rdYear/Semester%202/PPL/BTL/PPL4/src/codegen/emitter.py)
- **`emit_add_op`**: Extend to support string concatenation if the operands are `StringType` by calling `java/lang/String.concat`.
- **`emit_field`**: Add a new method to emit field declarations (`.field public [name] [type]`).
- **`emit_default_constructor`**: Add a new method to emit a parameterless constructor (`<init>()V`) for struct initializations, chaining to `java/lang/Object/<init>()V`.
- **`emit_and_short_circuit` / `emit_or_short_circuit`**: Optionally add or just handle it directly within `codegen.py` using labels and jumps.

### 2. `src/codegen/codegen.py`
Implement all the visitor methods that currently raise `RuntimeError` or `NotImplementedError`.

#### [MODIFY] [codegen.py](file:///e:/School/3rdYear/Semester%202/PPL/BTL/PPL4/src/codegen/codegen.py)
- **`visit_binary_op`**: 
  - Add `&&` and `||` with proper short-circuiting logic using jump labels. 
  - Add logic to branch to string concatenation when operands are strings.
- **`visit_assign_expr`**: 
  - Modify to handle `MemberAccess` left-hand side, utilizing `PUTFIELD`.
- **`visit_struct_decl`**: 
  - Instantiate a new `Emitter` with `{struct_name}.j`.
  - Emit `.class` and `.super` prolog.
  - Visit and emit all struct members as `.field`.
  - Emit the default constructor using the new `emitter.emit_default_constructor`.
  - Write output.
- **`visit_member_decl`**: 
  - Return the field definition code calling `emit_field`.
- **`visit_for_stmt`**: 
  - Use `frame.enter_loop()` to register `continue_label` and `break_label`. 
  - Visit the initialization, write the loop condition check and branch to `break_label` if false, visit body, visit update, branch to condition label. Call `frame.exit_loop()`.
- **`visit_switch_stmt`**: 
  - Register `break_label` via `frame.enter_loop()`. Evaluate expression, test each case's constant value sequentially (or via `lookupswitch`). Emit matching branches and the default branch. Call `frame.exit_loop()`.
- **`visit_case_stmt`** & **`visit_default_stmt`**: 
  - Handle block logic and label emission for each case.
- **`visit_break_stmt`**: 
  - Jump to `frame.get_break_label()`.
- **`visit_continue_stmt`**: 
  - Jump to `frame.get_continue_label()`.
- **`visit_prefix_op`**: 
  - Handle `++`, `--` (load, modify, dup, store), `+` (identity), `-` (negate), `!` (compare with zero).
- **`visit_postfix_op`**: 
  - Handle `++`, `--` (load, dup, modify, store).
- **`visit_member_access`**: 
  - Push object reference, then use `GETFIELD`.
- **`visit_struct_literal`**: 
  - `NEW` instance, `DUP`, `INVOKESPECIAL` for `<init>`, then for each expression, push value and use `PUTFIELD`.

## Verification Plan
Once all visitor functions and emitters are implemented, run:
```bash
python run.py test-codegen
```
This should execute the 100 codegen tests provided in the skeleton and confirm if the implementation is correct and valid JVM bytecode is produced.
