import dis as disassembler
import sys
import types


def unpack_bytecode(bytecode):
    extended_arg = 0
    for i in range(0, len(bytecode), 2):
        if bytecode[i] >= disassembler.HAVE_ARGUMENT:
            oparg = bytecode[i + 1] | extended_arg
            extended_arg = (
                oparg << 8) if bytecode[i] == disassembler.EXTENDED_ARG else 0
        else:
            oparg = None
        yield (i, bytecode[i], oparg)


def get_argument_value(offset, code_object, opcode, oparg):
    argument_value = None
    if opcode in disassembler.hasconst and code_object.co_consts:
        argument_value = code_object.co_consts[oparg]
        if isinstance(argument_value, str) or argument_value is None:
            argument_value = repr(argument_value)
    elif opcode in disassembler.hasname and code_object.co_names:
        argument_value = code_object.co_names[oparg]
    elif opcode in disassembler.hasjrel:
        argument_value = offset + 2 + oparg
        argument_value = "to " + repr(argument_value)
    elif opcode in disassembler.haslocal and code_object.co_varnames:
        argument_value = code_object.co_varnames[oparg]
    elif opcode in disassembler.hascompare:
        argument_value = disassembler.cmp_op[oparg]
    elif opcode in disassembler.hasfree and code_object.co_cellvars and code_object.co_freevars:
        argument_value = (
            code_object.co_cellvars +
            code_object.co_freevars)[oparg]
    return argument_value


def find_line_starts(code_object):
    byte_increments = code_object.co_lnotab[0::2]
    line_increments = code_object.co_lnotab[1::2]
    byte = 0
    line = code_object.co_firstlineno
    linestart_dictionary = {byte: line}
    for byte_increment, line_increment in zip(byte_increments,
                                              line_increments):
        byte += byte_increment
        if line_increment >= 0x80:
            line_increment -= 0x100
        line += line_increment
        linestart_dictionary[byte] = line
    return linestart_dictionary


def disassemble_to_list(code_object, unpacked_bytecode):
    code_list = []
    for offset, opcode, oparg in unpacked_bytecode:
        argument_value = get_argument_value(offset, code_object, opcode, oparg)
        if argument_value:
            if isinstance(argument_value, str):
                argument_value = argument_value.strip("\'")
            argument_value = None if argument_value == 'None' else argument_value
            code_list.append([disassembler.opname[opcode], argument_value])
        else:
            if oparg:
                code_list.append([disassembler.opname[opcode], oparg])
            else:
                code_list.append([disassembler.opname[opcode]])
    return code_list


def assemble_new_bytecode(
        code_list,
        constants,
        variable_names,
        names,
        cell_names):
    byte_list = []
    for i, instruction in enumerate(code_list):
        if len(instruction) == 2:
            offset = i * 2
            opname, argument_value = instruction
            opcode = disassembler.opname.index(opname)
            oparg = argument_value
            if opcode in disassembler.hasconst and constants:
                oparg = constants.index(argument_value)
            elif opcode in disassembler.hasname and names:
                oparg = names.index(argument_value)
            elif opcode in disassembler.hasjrel:
                argument_value = int(argument_value.split()[1])
                oparg = argument_value - offset - 2
            elif opcode in disassembler.haslocal and variable_names:
                oparg = variable_names.index(argument_value)
            elif opcode in disassembler.hascompare:
                oparg = disassembler.cmp_op.index(argument_value)
            elif opcode in disassembler.hasfree and cell_names:
                oparg = cell_names.index(argument_value)
        else:
            opname = instruction[0]
            opcode = disassembler.opname.index(opname)
            oparg = 0
        byte_list += [opcode, oparg]
    return(bytes(byte_list))


def chronotco(target_function):
    code_object = target_function.__code__
    disassembled_bytecode = disassemble_to_list(
        code_object, unpack_bytecode(code_object.co_code))
    for i in range(0, len(disassembled_bytecode)):
        if disassembled_bytecode[i] == ['LOAD_GLOBAL', code_object.co_name]:
            tail_recursive = False
            for index, instruction in enumerate(disassembled_bytecode[i + 1:]):
                if (instruction[0] == "CALL_FUNCTION") and (
                        disassembled_bytecode[i + index + 2] == ["RETURN_VALUE"]):
                    argument_count = instruction[1]
                    new_bytecode = [['STORE_FAST', variable] for variable in list(
                        code_object.co_varnames)[argument_count::-1]]
                    new_bytecode += [['POP_TOP'], ['JUMP_ABSOLUTE', 0]]
                    disassembled_bytecode[i + index +
                                          1:i + index + 3] = new_bytecode
                    tail_recursive = True

                    for instruction in disassembled_bytecode:
                        opcode = disassembler.opname.index(instruction[0])
                        if opcode in disassembler.hasjrel:
                            jump_offset = int(instruction[1].split("to")[1])
                            if jump_offset > (i + index + 1) * 2:
                                instruction[1] = "to " + \
                                    str((len(new_bytecode) - 2) * 2 + jump_offset)
                        if opcode in disassembler.hasjabs:
                            if instruction[1] > (i + index + 1) * 2:
                                instruction[1] += (len(new_bytecode) - 2) * 2
                    break

                elif (instruction[0] == "CALL_FUNCTION_KW") and (disassembled_bytecode[i + index + 2] == ["RETURN_VALUE"]):
                    argument_count = instruction[1]
                    keyward_argument_tuple = disassembled_bytecode[i + index][1]
                    positional_argument_count = argument_count - \
                        len(keyward_argument_tuple)
                    new_bytecode = [["POP_TOP"]]
                    new_bytecode += [['STORE_FAST', var] for var in list(
                        keyward_argument_tuple)[len(keyward_argument_tuple)::-1]]
                    if positional_argument_count != 0:
                        new_bytecode += [['STORE_FAST', var] for var in list(code_object.co_varnames)[
                            positional_argument_count - 1::-1]]
                    new_bytecode += [['POP_TOP'], ['JUMP_ABSOLUTE', 0]]
                    disassembled_bytecode[i + index +
                                          1:i + index + 3] = new_bytecode
                    tail_recursive = True

                    for instruction in disassembled_bytecode:
                        opcode = disassembler.opname.index(instruction[0])
                        if opcode in disassembler.hasjrel:
                            jump_offset = int(instruction[1].split("to")[1])
                            if jump_offset > (i + index + 1) * 2:
                                instruction[1] = "to " + \
                                    str((len(new_bytecode) - 2) * 2 + jump_offset)
                        if opcode in disassembler.hasjabs:
                            if instruction[1] > (i + index + 1) * 2:
                                instruction[1] += (len(new_bytecode) - 2) * 2
                    break

            if not tail_recursive:
                raise Exception("The provided function is not tail-recursive!")

    new_co_code = assemble_new_bytecode(
        disassembled_bytecode,
        code_object.co_consts,
        code_object.co_varnames,
        code_object.co_names,
        code_object.co_cellvars +
        code_object.co_freevars)

    if sys.version_info >= (3, 8):
        new_code_object = types.CodeType(
            code_object.co_argcount,
            code_object.co_kwonlyargcount,
            code_object.co_posonlyargcount,
            code_object.co_nlocals,
            code_object.co_stacksize,
            code_object.co_flags,
            new_co_code,
            code_object.co_consts,
            code_object.co_names,
            code_object.co_varnames,
            code_object.co_filename,
            code_object.co_name,
            code_object.co_firstlineno,
            code_object.co_lnotab,
            cellvars=code_object.co_cellvars,
            freevars=code_object.co_freevars)
    else:
        new_code_object = types.CodeType(
            code_object.co_argcount,
            code_object.co_kwonlyargcount,
            code_object.co_nlocals,
            code_object.co_stacksize,
            code_object.co_flags,
            new_co_code,
            code_object.co_consts,
            code_object.co_names,
            code_object.co_varnames,
            code_object.co_filename,
            code_object.co_name,
            code_object.co_firstlineno,
            code_object.co_lnotab,
            cellvars=code_object.co_cellvars,
            freevars=code_object.co_freevars)

    target_function.__code__ = new_code_object

    return target_function
