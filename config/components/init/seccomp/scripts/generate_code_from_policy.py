#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import sys
import argparse
import textwrap
import re
import os
import stat

supported_parse_item = ['labelName', 'priority', 'allowList', 'blockList', 'priorityWithArgs', \
                        'allowListWithArgs', 'headFiles', 'selfDefineSyscall', 'returnValue', \
                        'mode', 'privilegedProcessName', 'allowBlockList']

supported_architecture = ['arm', 'arm64', 'riscv64']

BPF_JGE = 'BPF_JUMP(BPF_JMP|BPF_JGE|BPF_K, {}, {}, {}),'
BPF_JGT = 'BPF_JUMP(BPF_JMP|BPF_JGT|BPF_K, {}, {}, {}),'
BPF_JEQ = 'BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, {}, {}, {}),'
BPF_JSET = 'BPF_JUMP(BPF_JMP|BPF_JSET|BPF_K, {}, {}, {}),'
BPF_JA = 'BPF_JUMP(BPF_JMP|BPF_JA, {}, 0, 0),'
BPF_LOAD = 'BPF_STMT(BPF_LD|BPF_W|BPF_ABS, {}),'
BPF_LOAD_MEM = 'BPF_STMT(BPF_LD|BPF_MEM, {}),'
BPF_ST = 'BPF_STMT(BPF_ST, {}),'
BPF_AND = 'BPF_STMT(BPF_ALU|BPF_AND|BPF_K, {}),'
BPF_RET_VALUE = 'BPF_STMT(BPF_RET|BPF_K, {}),'

operation = ['<', '<=', '!=', '==', '>', '>=', '&']

ret_str_to_bpf = {
    'KILL_PROCESS': 'SECCOMP_RET_KILL_PROCESS',
    'KILL_THREAD': 'SECCOMP_RET_KILL_THREAD',
    'TRAP': 'SECCOMP_RET_TRAP',
    'ERRNO': 'SECCOMP_RET_ERRNO',
    'USER_NOTIF': 'SECCOMP_RET_USER_NOTIF',
    'TRACE': 'SECCOMP_RET_TRACE',
    'LOG' : 'SECCOMP_RET_LOG',
    'ALLOW': 'SECCOMP_RET_ALLOW'
}

mode_str = {
    'DEFAULT': 0,
    'ONLY_CHECK_ARGS': 1
}

architecture_to_number = {
    'arm': 'AUDIT_ARCH_ARM',
    'arm64': 'AUDIT_ARCH_AARCH64',
    'riscv64': 'AUDIT_ARCH_RISCV64'
}


class ValidateError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


def print_info(info):
    print("[INFO] %s" % info)


def is_hex_digit(s):
    try:
        int(s, 16)
        return True

    except ValueError:
        return False


def str_convert_to_int(s):
    number = -1
    digit_flag = False

    if s.isdigit() :
        number = int(s)
        digit_flag = True

    elif is_hex_digit(s):
        number = int(s, 16)
        digit_flag = True

    return number, digit_flag


def is_function_name_exist(arch, function_name, func_name_nr_table):
    if function_name in func_name_nr_table:
        return True
    else:
        raise ValidateError('{} not exsit in {} function_name_nr_table Table'.format(function_name, arch))


def is_errno_in_valid_range(errno):
    if int(errno) > 0 and int(errno) <= 255 and errno.isdigit():
        return True
    else:
        raise ValidateError('{} not within the legal range of errno values.'.format(errno))


def is_return_errno(return_str):
    if return_str[0:len('ERRNO')] == 'ERRNO':
        errno_no = return_str[return_str.find('(') + 1 : return_str.find(')')]
        return_string = return_str[0:len('ERRNO')]
        return_string += ' | '
        if is_errno_in_valid_range(errno_no):
            return_string += errno_no
            return True, return_string
    return False, 'not_return_errno'


def function_name_to_nr(function_name_list, func_name_nr_table):
    return set(func_name_nr_table[function_name] for function_name \
    in function_name_list if function_name in func_name_nr_table)


def filter_syscalls_nr(name_to_nr):
    syscalls = {}
    for syscall_name, nr in name_to_nr.items():
        if not syscall_name.startswith("__NR_") and not syscall_name.startswith("__ARM_NR_"):
            continue

        if syscall_name.startswith("__NR_arm_"):
            syscall_name = syscall_name[len("__NR_arm_"):]
        elif syscall_name.startswith("__NR_riscv_"):
            syscall_name = syscall_name[len("__NR_riscv_"):]
        elif syscall_name.startswith("__NR_"):
            syscall_name = syscall_name[len("__NR_"):]
        elif syscall_name.startswith("__ARM_NR_"):
            syscall_name = syscall_name[len("__ARM_NR_"):]
        elif syscall_name.startswith("__RISCV_NR_"):
            syscall_name = syscall_name[len("__RISCV_NR_"):]
        syscalls[syscall_name] = nr

    return syscalls


def parse_syscall_file(file_name):
    const_pattern = re.compile(
        r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]+)\s+(.+)\s*$')
    mark_pattern = re.compile(r'\b[A-Za-z_][A-Za-z0-9_]+\b')
    name_to_nr = {}
    with open(file_name) as f:
        for line in f:
            k = const_pattern.match(line)
            if k is None:
                continue
            try:
                name = k.group(1)
                nr = eval(mark_pattern.sub(lambda x: str(name_to_nr.get(x.group(0))),
                                        k.group(2)))

                name_to_nr[name] = nr
            except(KeyError, SyntaxError, NameError, TypeError):
                continue

    return filter_syscalls_nr(name_to_nr)


def gen_syscall_nr_table(file_name, func_name_nr_table):
    s = re.search(r"libsyscall_to_nr_([^/]+)", file_name)
    func_name_nr_table[str(s.group(1))] = parse_syscall_file(file_name)
    if str(s.group(1)) not in func_name_nr_table.keys():
        raise ValidateError("parse syscall file failed")
    return func_name_nr_table


class SeccompPolicyParam:
    def __init__(self, arch, function_name_nr_table, is_debug):
        self.arch = arch
        self.priority = set()
        self.allow_list = set()
        self.blocklist = set()
        self.priority_with_args = set()
        self.allow_list_with_args = set()
        self.head_files = set()
        self.self_define_syscall = set()
        self.final_allow_list = set()
        self.final_priority = set()
        self.final_priority_with_args = set()
        self.final_allow_list_with_args = set()
        self.return_value = ''
        self.mode = 'DEFAULT'
        self.is_debug = is_debug
        self.function_name_nr_table = function_name_nr_table
        self.value_function = {
            'priority': self.update_priority,
            'allowList': self.update_allow_list,
            'blockList': self.update_blocklist,
            'allowListWithArgs': self.update_allow_list_with_args,
            'priorityWithArgs': self.update_priority_with_args,
            'headFiles': self.update_head_files,
            'selfDefineSyscall': self.update_self_define_syscall,
            'returnValue': self.update_return_value,
            'mode': self.update_mode
        }

    def clear_list(self):
        self.priority.clear()
        self.allow_list.clear()
        self.allow_list_with_args.clear()
        self.priority_with_args.clear()
        if self.mode == 'ONLY_CHECK_ARGS':
            self.final_allow_list.clear()
            self.final_priority.clear()

    def update_list(self, function_name, to_update_list):
        if is_function_name_exist(self.arch, function_name, self.function_name_nr_table):
            to_update_list.add(function_name)
            return True
        return False

    def update_priority(self, function_name):
        return self.update_list(function_name, self.priority)

    def update_allow_list(self, function_name):
        return self.update_list(function_name, self.allow_list)

    def update_blocklist(self, function_name):
        return self.update_list(function_name, self.blocklist)

    def update_priority_with_args(self, function_name_with_args):
        function_name = function_name_with_args[:function_name_with_args.find(':')]
        function_name = function_name.strip()
        if is_function_name_exist(self.arch, function_name, self.function_name_nr_table):
            self.priority_with_args.add(function_name_with_args)
            return True
        return False

    def update_allow_list_with_args(self, function_name_with_args):
        function_name = function_name_with_args[:function_name_with_args.find(':')]
        function_name = function_name.strip()
        if is_function_name_exist(self.arch, function_name, self.function_name_nr_table):
            self.allow_list_with_args.add(function_name_with_args)
            return True
        return False

    def update_head_files(self, head_files):
        if len(head_files) > 2 and (head_files[0] == '\"' and head_files[-1] == '\"') or \
            (head_files[0] == '<' and head_files[-1] == '>'):
            self.head_files.add(head_files)
            return True

        raise ValidateError('{} is not legal by headFiles format'.format(head_files))

    def update_self_define_syscall(self, self_define_syscall):
        nr, digit_flag = str_convert_to_int(self_define_syscall)
        if digit_flag and nr not in self.function_name_nr_table.values():
            self.self_define_syscall.add(nr)
            return True

        raise ValidateError('{} is not a number or {} is already used by ohter \
            syscall'.format(self_define_syscall, self_define_syscall))

    def update_return_value(self, return_str):
        is_ret_errno, return_string = is_return_errno(return_str)
        if is_ret_errno == True:
            self.return_value = return_string
            return True
        if return_str in ret_str_to_bpf:
            if self.is_debug == 'false' and return_str == 'LOG':
                raise ValidateError("LOG return value is not allowed in user mode")
            self.return_value = return_str
            return True

        raise ValidateError('{} not in {}'.format(return_str, ret_str_to_bpf.keys()))

    def update_mode(self, mode):
        if mode in mode_str.keys():
            self.mode = mode
            return True
        raise ValidateError('{} not in [DEFAULT, ONLY_CHECK_ARGS]'.format(mode_str))

    def check_allow_list(self, allow_list):
        for item in allow_list:
            pos = item.find(':')
            syscall = item
            if pos != -1:
                syscall = item[:pos]
            if syscall in self.blocklist:
                raise ValidateError('{} of allow list  is in block list'.format(syscall))
        return True

    def check_all_allow_list(self):
        flag = self.check_allow_list(self.final_allow_list) \
               and self.check_allow_list(self.final_priority) \
               and self.check_allow_list(self.final_priority_with_args) \
               and self.check_allow_list(self.final_allow_list_with_args)
        block_nr_list = function_name_to_nr(self.blocklist, self.function_name_nr_table)
        for nr in self.self_define_syscall:
            if nr in block_nr_list:
                return False
        return flag

    def update_final_list(self):
        #remove duplicate function_name
        self.final_allow_list |= self.allow_list
        self.final_priority |= self.priority
        self.final_allow_list_with_args |= self.allow_list_with_args
        self.final_priority_with_args |= self.priority_with_args
        final_priority_function_name_list_with_args = set(item[:item.find(':')] 
                                                            for item in self.final_priority_with_args)
        final_function_name_list_with_args = set(item[:item.find(':')] 
                                                    for item in self.final_allow_list_with_args)
        self.final_allow_list = self.final_allow_list - self.final_priority - \
                                    final_priority_function_name_list_with_args - final_function_name_list_with_args
        self.final_priority = self.final_priority - final_priority_function_name_list_with_args - \
                                final_function_name_list_with_args
        self.clear_list()


class GenBpfPolicy:
    def __init__(self):
        self.arch = ''
        self.syscall_nr_range = []
        self.bpf_policy = []
        self.syscall_nr_policy_list = []
        self.function_name_nr_table_dict = {}
        self.gen_mode = 0
        self.flag = True
        self.return_value = ''
        self.operate_func_table = {
            '<' : self.gen_bpf_lt,
            '<=': self.gen_bpf_le,
            '==': self.gen_bpf_eq,
            '!=': self.gen_bpf_ne,
            '>' : self.gen_bpf_gt,
            '>=': self.gen_bpf_ge,
            '&' : self.gen_bpf_set,
        }

    @staticmethod
    def gen_bpf_eq32(const_str, jt, jf):
        bpf_policy = []
        bpf_policy.append(BPF_JEQ.format(const_str + ' & 0xffffffff', jt, jf))
        return bpf_policy

    @staticmethod
    def gen_bpf_eq64(const_str, jt, jf):
        bpf_policy = []
        bpf_policy.append(BPF_JEQ.format('((unsigned long)' + const_str + ') >> 32', 0, jf + 2))
        bpf_policy.append(BPF_LOAD_MEM.format(0))
        bpf_policy.append(BPF_JEQ.format(const_str + ' & 0xffffffff', jt, jf))
        return bpf_policy

    @staticmethod
    def gen_bpf_gt32(const_str, jt, jf):
        bpf_policy = []
        bpf_policy.append(BPF_JGT.format(const_str + ' & 0xffffffff', jt, jf))
        return bpf_policy

    @staticmethod
    def gen_bpf_gt64(const_str, jt, jf):
        bpf_policy = []
        number, digit_flag = str_convert_to_int(const_str)

        hight = int(number / (2**32))
        low = number & 0xffffffff

        if digit_flag and hight == 0:
            bpf_policy.append(BPF_JGT.format('((unsigned long)' + const_str + ') >> 32', jt + 2, 0))
        else:
            bpf_policy.append(BPF_JGT.format('((unsigned long)' + const_str + ') >> 32', jt + 3, 0))
            bpf_policy.append(BPF_JEQ.format('((unsigned long)' + const_str + ') >> 32', 0, jf + 2))

        bpf_policy.append(BPF_LOAD_MEM.format(0))
        bpf_policy.append(BPF_JGT.format(const_str + ' & 0xffffffff', jt, jf))

        return bpf_policy

    @staticmethod
    def gen_bpf_ge32(const_str, jt, jf):
        bpf_policy = []
        bpf_policy.append(BPF_JGE.format(const_str + ' & 0xffffffff', jt, jf))
        return bpf_policy

    @staticmethod
    def gen_bpf_ge64(const_str, jt, jf):
        bpf_policy = []
        number, digit_flag = str_convert_to_int(const_str)

        hight = int(number / (2**32))
        low = number & 0xffffffff

        if digit_flag and hight == 0:
            bpf_policy.append(BPF_JGT.format('((unsigned long)' + const_str + ') >> 32', jt + 2, 0))
        else:
            bpf_policy.append(BPF_JGT.format('((unsigned long)' + const_str + ') >> 32', jt + 3, 0))
            bpf_policy.append(BPF_JEQ.format('((unsigned long)' + const_str + ') >> 32', 0, jf + 2))
        bpf_policy.append(BPF_LOAD_MEM.format(0))
        bpf_policy.append(BPF_JGE.format(const_str + ' & 0xffffffff', jt, jf))
        return bpf_policy

    @staticmethod
    def gen_bpf_set32(const_str, jt, jf):
        bpf_policy = []
        bpf_policy.append(BPF_JSET.format(const_str + ' & 0xffffffff', jt, jf))
        return bpf_policy

    @staticmethod
    def gen_bpf_set64(const_str, jt, jf):
        bpf_policy = []
        bpf_policy.append(BPF_JSET.format('((unsigned long)' + const_str + ') >> 32', jt + 2, 0))
        bpf_policy.append(BPF_LOAD_MEM.format(0))
        bpf_policy.append(BPF_JSET.format(const_str + ' & 0xffffffff', jt, jf))
        return bpf_policy

    @staticmethod
    def gen_bpf_valid_syscall_nr(syscall_nr, cur_size):
        bpf_policy = []
        bpf_policy.append(BPF_LOAD.format(0))
        bpf_policy.append(BPF_JEQ.format(syscall_nr, 0, cur_size))
        return bpf_policy

    @staticmethod
    def check_arg_str(arg_atom):
        arg_str = arg_atom[0:3]
        if arg_str != 'arg':
            raise ValidateError('format ERROR, {} is not equal to arg'.format(arg_atom))

        arg_id = int(arg_atom[3])
        if arg_id not in range(6):
            raise ValidateError('arg num out of the scope 0~5')

        return arg_id, True

    @staticmethod
    def check_operation_str(operation_atom):
        operation_str = operation_atom
        if operation_str not in operation:
            operation_str = operation_atom[0]
            if operation_str not in operation:
                raise ValidateError('operation not in [<, <=, !=, ==, >, >=, &]')
        return operation_str, True

    #gen bpf (argn & mask) == value
    @staticmethod
    def gen_mask_equal_bpf(arg_id, mask, value, cur_size):
        bpf_policy = []
        #high 4 bytes
        bpf_policy.append(BPF_LOAD.format(20 + arg_id * 8))
        bpf_policy.append(BPF_AND.format('((uint64_t)' + mask + ') >> 32'))
        bpf_policy.append(BPF_JEQ.format('((uint64_t)' + value + ') >> 32', 0, cur_size + 4))

        #low 4 bytes
        bpf_policy.append(BPF_LOAD.format(16 + arg_id * 8))
        bpf_policy.append(BPF_AND.format(mask))
        bpf_policy.append(BPF_JEQ.format(value, cur_size, cur_size + 1))

        return bpf_policy

    def update_arch(self, arch):
        self.arch = arch
        self.syscall_nr_range = []
        self.syscall_nr_policy_list = []

    def update_function_name_nr_table(self, func_name_nr_table):
        self.function_name_nr_table_dict = func_name_nr_table

    def clear_bpf_policy(self):
        self.bpf_policy.clear()

    def get_gen_flag(self):
        return self.flag

    def set_gen_flag(self, flag):
        if flag:
            self.flag = True
        else:
            self.flag = False

    def set_gen_mode(self, mode):
        self.gen_mode = mode_str.get(mode)

    def set_return_value(self, return_value):
        is_ret_errno, return_string = is_return_errno(return_value)
        if is_ret_errno == True:
            self.return_value = return_string
            return
        if return_value not in ret_str_to_bpf:
            self.set_gen_mode(False)
            return

        self.return_value = return_value

    def gen_bpf_eq(self, const_str, jt, jf):
        if self.arch == 'arm':
            return self.gen_bpf_eq32(const_str, jt, jf)
        elif self.arch == 'arm64' or self.arch == 'riscv64':
            return self.gen_bpf_eq64(const_str, jt, jf)
        return []

    def gen_bpf_ne(self, const_str, jt, jf):
        return self.gen_bpf_eq(const_str, jf, jt)

    def gen_bpf_gt(self, const_str, jt, jf):
        if self.arch == 'arm':
            return self.gen_bpf_gt32(const_str, jt, jf)
        elif self.arch == 'arm64' or self.arch == 'riscv64':
            return self.gen_bpf_gt64(const_str, jt, jf)
        return []

    def gen_bpf_le(self, const_str, jt, jf):
        return self.gen_bpf_gt(const_str, jf, jt)

    def gen_bpf_ge(self, const_str, jt, jf):
        if self.arch == 'arm':
            return self.gen_bpf_ge32(const_str, jt, jf)
        elif self.arch == 'arm64' or self.arch == 'riscv64':
            return self.gen_bpf_ge64(const_str, jt, jf)
        return []

    def gen_bpf_lt(self, const_str, jt, jf):
        return self.gen_bpf_ge(const_str, jf, jt)

    def gen_bpf_set(self, const_str, jt, jf):
        if self.arch == 'arm':
            return self.gen_bpf_set32(const_str, jt, jf)
        elif self.arch == 'arm64' or self.arch == 'riscv64':
            return self.gen_bpf_set64(const_str, jt, jf)
        return []

    def gen_range_list(self, syscall_nr_list):
        if len(syscall_nr_list) == 0:
            return
        self.syscall_nr_range.clear()

        syscall_nr_list_order = sorted(list(syscall_nr_list))
        range_temp = [syscall_nr_list_order[0], syscall_nr_list_order[0]]

        for i in range(len(syscall_nr_list_order) - 1):
            if syscall_nr_list_order[i + 1] != syscall_nr_list_order[i] + 1:
                range_temp[1] = syscall_nr_list_order[i]
                self.syscall_nr_range.append(range_temp)
                range_temp = [syscall_nr_list_order[i + 1], syscall_nr_list_order[i + 1]]

        range_temp[1] = syscall_nr_list_order[-1]
        self.syscall_nr_range.append(range_temp)

    def gen_policy_syscall_nr(self, min_index, max_index, cur_syscall_nr_range):
        middle_index = (int)((min_index + max_index + 1) / 2)

        if middle_index == min_index:
            self.syscall_nr_policy_list.append(cur_syscall_nr_range[middle_index][1] + 1)
            return
        else:
            self.syscall_nr_policy_list.append(cur_syscall_nr_range[middle_index][0])

        self.gen_policy_syscall_nr(min_index, middle_index - 1, cur_syscall_nr_range)
        self.gen_policy_syscall_nr(middle_index, max_index, cur_syscall_nr_range)

    def gen_policy_syscall_nr_list(self, cur_syscall_nr_range):
        if not cur_syscall_nr_range:
            return
        self.syscall_nr_policy_list.clear()
        self.syscall_nr_policy_list.append(cur_syscall_nr_range[0][0])
        self.gen_policy_syscall_nr(0, len(cur_syscall_nr_range) - 1, cur_syscall_nr_range)

    def calculate_step(self, index):
        for i in range(index + 1, len(self.syscall_nr_policy_list)):
            if self.syscall_nr_policy_list[index] < self.syscall_nr_policy_list[i]:
                step = i - index
                break
        return step - 1

    def nr_range_to_bpf_policy(self, cur_syscall_nr_range):
        self.gen_policy_syscall_nr_list(cur_syscall_nr_range)
        syscall_list_len = len(self.syscall_nr_policy_list)

        if syscall_list_len == 0:
            return

        self.bpf_policy.append(BPF_JGE.format(self.syscall_nr_policy_list[0], 0, syscall_list_len))

        range_max_list = [k[1] for k in cur_syscall_nr_range]

        for i in range(1, syscall_list_len):
            if self.syscall_nr_policy_list[i] - 1 in range_max_list:
                self.bpf_policy.append(BPF_JGE.format(self.syscall_nr_policy_list[i], \
                                        syscall_list_len - i, syscall_list_len - i - 1))
            else:
                step = self.calculate_step(i)
                self.bpf_policy.append(BPF_JGE.format(self.syscall_nr_policy_list[i], step, 0))

        if self.syscall_nr_policy_list:
            self.bpf_policy.append(BPF_RET_VALUE.format('SECCOMP_RET_ALLOW'))

    def count_alone_range(self):
        cnt = 0
        for item in self.syscall_nr_range:
            if item[0] == item[1]:
                cnt = cnt + 1
        return cnt

    def gen_transverse_bpf_policy(self):
        if not self.syscall_nr_range:
            return
        cnt = self.count_alone_range()
        total_instruction_num = cnt + (len(self.syscall_nr_range) - cnt) * 2
        i = 0
        for item in self.syscall_nr_range:
            if item[0] == item[1]:
                if i == total_instruction_num - 1:
                    self.bpf_policy.append(BPF_JEQ.format(item[0], total_instruction_num - i - 1, 1))
                else:
                    self.bpf_policy.append(BPF_JEQ.format(item[0], total_instruction_num - i - 1, 0))
                i += 1
            else:
                self.bpf_policy.append(BPF_JGE.format(item[0], 0, total_instruction_num - i))
                i += 1
                if i == total_instruction_num - 1:
                    self.bpf_policy.append(BPF_JGE.format(item[1] + 1, 1, total_instruction_num - i - 1))
                else:
                    self.bpf_policy.append(BPF_JGE.format(item[1] + 1, 0, total_instruction_num - i - 1))
                i += 1

        self.bpf_policy.append(BPF_RET_VALUE.format('SECCOMP_RET_ALLOW'))

    def gen_bpf_policy(self, syscall_nr_list):
        self.gen_range_list(syscall_nr_list)
        range_size = (int)((len(self.syscall_nr_range) - 1) / 127) + 1
        alone_range_cnt = self.count_alone_range()
        if alone_range_cnt == len(self.syscall_nr_range):
            #Scattered distribution
            self.gen_transverse_bpf_policy()
            return

        if range_size == 1:
            self.nr_range_to_bpf_policy(self.syscall_nr_range)
        else:
            for i in range(0, range_size):
                if i == 0:
                    self.nr_range_to_bpf_policy(self.syscall_nr_range[-127 * (i + 1):])
                elif i == range_size - 1:
                    self.nr_range_to_bpf_policy(self.syscall_nr_range[:-127 * i])
                else:
                    self.nr_range_to_bpf_policy(self.syscall_nr_range[-127 * (i + 1): -127 * i])

    def load_arg(self, arg_id):
        # little endian
        bpf_policy = []
        if self.arch == 'arm':
            bpf_policy.append(BPF_LOAD.format(16 + arg_id * 8))
        elif self.arch == 'arm64' or self.arch == 'riscv64':
            #low 4 bytes
            bpf_policy.append(BPF_LOAD.format(16 + arg_id * 8))
            bpf_policy.append(BPF_ST.format(0))
            #high 4 bytes
            bpf_policy.append(BPF_LOAD.format(20 + arg_id * 8))
            bpf_policy.append(BPF_ST.format(1))

        return bpf_policy

    def compile_atom(self, atom, cur_size):
        bpf_policy = []
        if len(atom) < 6:
            raise ValidateError('{} format ERROR '.format(atom))

        if atom[0] == '(':
            bpf_policy += self.compile_mask_equal_atom(atom, cur_size)
        else:
            bpf_policy += self.compile_single_operation_atom(atom, cur_size)

        return bpf_policy

    def compile_mask_equal_atom(self, atom, cur_size):
        bpf_policy = []
        left_brace_pos = atom.find('(')
        right_brace_pos = atom.rfind(')')
        inside_brace_content = atom[left_brace_pos + 1: right_brace_pos]
        outside_brace_content = atom[right_brace_pos + 1:]

        arg_res = self.check_arg_str(inside_brace_content[0:4])
        if not arg_res[1]:
            return bpf_policy

        operation_res_inside = self.check_operation_str(inside_brace_content[4:6])
        if operation_res_inside[0] != '&' or not operation_res_inside[1]:
            return bpf_policy

        mask = inside_brace_content[4 + len(operation_res_inside[0]):]

        operation_res_outside = self.check_operation_str(outside_brace_content[0:2])
        if operation_res_outside[0] != '==' or not operation_res_outside[1]:
            return bpf_policy

        value = outside_brace_content[len(operation_res_outside[0]):]

        return self.gen_mask_equal_bpf(arg_res[0], mask, value, cur_size)

    def compile_single_operation_atom(self, atom, cur_size):
        bpf_policy = []
        arg_res = self.check_arg_str(atom[0:4])
        if not arg_res[1]:
            return bpf_policy

        operation_res = self.check_operation_str(atom[4:6])
        if not operation_res[1]:
            return bpf_policy

        const_str = atom[4 + len(operation_res[0]):]

        if not const_str:
            return bpf_policy

        bpf_policy += self.load_arg(arg_res[0])
        bpf_policy += self.operate_func_table.get(operation_res[0])(const_str, 0, cur_size + 1)

        return bpf_policy

    def parse_args_with_condition(self, group):
        #the priority of && higher than ||
        atoms = group.split('&&')
        bpf_policy = []
        for atom in reversed(atoms):
            bpf_policy = self.compile_atom(atom, len(bpf_policy)) + bpf_policy
        return bpf_policy

    def parse_sub_group(self, group):
        bpf_policy = []
        group_info = group.split(';')
        operation_part = group_info[0]
        return_part = group_info[1]
        if not return_part.startswith('return'):
            raise ValidateError('allow list with args do not have return part')

        self.set_return_value(return_part[len('return'):])
        and_cond_groups = operation_part.split('||')
        for and_condition_group in and_cond_groups:
            bpf_policy += self.parse_args_with_condition(and_condition_group)
            bpf_policy.append(BPF_RET_VALUE.format(ret_str_to_bpf.get(self.return_value)))
        return bpf_policy

    def parse_else_part(self, else_part):
        return_value = else_part.split(';')[0][else_part.find('return') + len('return'):]
        self.set_return_value(return_value)

    def parse_args(self, function_name, line, skip):
        bpf_policy = []
        group_info = line.split('else')
        else_part = group_info[-1]
        group = group_info[0].split('elif')
        for sub_group in group:
            bpf_policy += self.parse_sub_group(sub_group)
        self.parse_else_part(else_part)
        if self.return_value[0:len('ERRNO')] == 'ERRNO':
            bpf_policy.append(BPF_RET_VALUE.format(self.return_value.replace('ERRNO', ret_str_to_bpf.get('ERRNO'))))
        else:
            bpf_policy.append(BPF_RET_VALUE.format(ret_str_to_bpf.get(self.return_value)))
        syscall_nr = self.function_name_nr_table_dict.get(self.arch).get(function_name)
        #load syscall nr
        bpf_policy = self.gen_bpf_valid_syscall_nr(syscall_nr, len(bpf_policy) - skip) + bpf_policy
        return bpf_policy

    def gen_bpf_policy_with_args(self, allow_list_with_args, mode, return_value):
        self.set_gen_mode(mode)
        skip = 0
        for line in allow_list_with_args:
            if self.gen_mode == 1 and line == list(allow_list_with_args)[-1]:
                skip = 2
            line = line.replace(' ', '')
            pos = line.find(':')
            function_name = line[:pos]

            left_line = line[pos + 1:]
            if not left_line.startswith('if'):
                continue

            self.bpf_policy += self.parse_args(function_name, left_line[2:], skip)

    def add_load_syscall_nr(self):
        self.bpf_policy.append(BPF_LOAD.format(0))

    def add_return_value(self, return_value):
        if return_value[0:len('ERRNO')] == 'ERRNO':
            self.bpf_policy.append(BPF_RET_VALUE.format(return_value.replace('ERRNO', ret_str_to_bpf.get('ERRNO'))))
        else:
            self.bpf_policy.append(BPF_RET_VALUE.format(ret_str_to_bpf.get(return_value)))

    def add_validate_arch(self, arches, skip_step):
        if not self.bpf_policy or not self.flag:
            return
        bpf_policy = []
        #load arch
        bpf_policy.append(BPF_LOAD.format(4))
        if len(arches) == 2:
            bpf_policy.append(BPF_JEQ.format(architecture_to_number.get(arches[0]), 3, 0))
            bpf_policy.append(BPF_JEQ.format(architecture_to_number.get(arches[1]), 0, 1))
            bpf_policy.append(BPF_JA.format(skip_step))
            bpf_policy.append(BPF_RET_VALUE.format('SECCOMP_RET_TRAP'))
        elif len(arches) == 1:
            bpf_policy.append(BPF_JEQ.format(architecture_to_number.get(arches[0]), 1, 0))
            bpf_policy.append(BPF_RET_VALUE.format('SECCOMP_RET_TRAP'))
        else:
            self.bpf_policy = []

        self.bpf_policy = bpf_policy + self.bpf_policy


class AllowBlockList:
    def __init__(self, filter_name, arch, function_name_nr_table):
        self.is_valid = False
        self.arch = arch
        self.filter_name = filter_name
        self.reduced_block_list = set()
        self.function_name_nr_table = function_name_nr_table
        self.value_function = {
            'privilegedProcessName': self.update_flag,
            'allowBlockList': self.update_reduced_block_list,
        }

    def update_flag(self, name):
        if self.filter_name == name:
            self.is_valid = True
        else:
            self.is_valid = False

    def update_reduced_block_list(self, function_name):
        if self.is_valid and is_function_name_exist(self.arch, function_name, self.function_name_nr_table):
            self.reduced_block_list.add(function_name)
            return True
        return False


class SeccompPolicyParser:
    def __init__(self):
        self.cur_parse_item = ''
        self.arches = set()
        self.bpf_generator = GenBpfPolicy()
        self.seccomp_policy_param = dict()
        self.reduced_block_list_parm = dict()
        self.key_process_flag = False
        self.is_debug = False

    def update_is_debug(self, is_debug):
        if is_debug == 'false':
            self.is_debug = False
        else:
            self.is_debug = True

    def update_arch(self, target_cpu):
        if target_cpu == "arm":
            self.arches.add(target_cpu)
        elif target_cpu == "arm64":
            self.arches.add("arm")
            self.arches.add(target_cpu)
        elif target_cpu == "riscv64":
            self.arches.add(target_cpu)

    def update_block_list(self):
        for arch in supported_architecture:
            self.seccomp_policy_param.get(arch).blocklist -= self.reduced_block_list_parm.get(arch).reduced_block_list

    def update_parse_item(self, line):
        item = line[1:]
        if item in supported_parse_item:
            self.cur_parse_item = item
            print_info('start deal with {}'.format(self.cur_parse_item))

    def check_allow_list(self):
        for arch in self.arches:
            if not self.seccomp_policy_param.get(arch).check_all_allow_list():
                self.bpf_generator.set_gen_flag(False)

    def clear_file_syscall_list(self):
        for arch in self.arches:
            self.seccomp_policy_param.get(arch).update_final_list()
        self.cur_parse_item = ''
        self.cur_arch = ''

    def parse_line(self, line):
        if not self.cur_parse_item :
            return
        line = line.replace(' ', '')
        pos = line.rfind(';')
        if pos < 0:
            for arch in self.arches:
                if self.key_process_flag:
                    self.reduced_block_list_parm.get(arch).value_function.get(self.cur_parse_item)(line)
                else:
                    self.seccomp_policy_param.get(arch).value_function.get(self.cur_parse_item)(line)
        else:
            arches = line[pos + 1:].split(',')
            if arches[0] == 'all':
                arches = supported_architecture
            for arch in arches:
                if self.key_process_flag:
                    self.reduced_block_list_parm.get(arch).value_function.get(self.cur_parse_item)(line[:pos])
                else:
                    self.seccomp_policy_param.get(arch).value_function.get(self.cur_parse_item)(line[:pos])

    def parse_open_file(self, fp):
        for line in fp:
            line = line.strip()
            if not line:
                continue
            if line[0] == '#':
                continue
            if line[0] == '@':
                self.update_parse_item(line)
                continue
            if line[0] != '@' and self.cur_parse_item == '':
                continue
            self.parse_line(line)
        self.clear_file_syscall_list()
        self.check_allow_list()

    def parse_file(self, file_path):
        with open(file_path) as fp:
            self.parse_open_file(fp)

    def gen_seccomp_policy_of_arch(self, arch):
        cur_policy_param = self.seccomp_policy_param.get(arch)

        if not cur_policy_param.return_value:
            raise ValidateError('return value not defined')

        #get final allow_list
        syscall_nr_allow_list = function_name_to_nr(cur_policy_param.final_allow_list, \
                                                    cur_policy_param.function_name_nr_table) \
                                                    | cur_policy_param.self_define_syscall
        syscall_nr_priority = function_name_to_nr(cur_policy_param.final_priority, \
                                                  cur_policy_param.function_name_nr_table)
        self.bpf_generator.update_arch(arch)

        #load syscall nr
        if syscall_nr_allow_list or syscall_nr_priority:
            self.bpf_generator.add_load_syscall_nr()
        self.bpf_generator.gen_bpf_policy(syscall_nr_priority)
        self.bpf_generator.gen_bpf_policy_with_args(sorted(list(cur_policy_param.final_priority_with_args)), \
            cur_policy_param.mode, cur_policy_param.return_value)
        self.bpf_generator.gen_bpf_policy(syscall_nr_allow_list)
        self.bpf_generator.gen_bpf_policy_with_args(sorted(list(cur_policy_param.final_allow_list_with_args)), \
            cur_policy_param.mode, cur_policy_param.return_value)

        self.bpf_generator.add_return_value(cur_policy_param.return_value)
        for line in self.bpf_generator.bpf_policy:
            if 'SECCOMP_RET_LOG' in line and self.is_debug == False:
                raise ValidateError("LOG return value is not allowed in user mode")

    def gen_seccomp_policy(self):
        arches = sorted(list(self.arches))
        if not arches:
            return
        self.gen_seccomp_policy_of_arch(arches[0])
        skip_step = len(self.bpf_generator.bpf_policy) + 1
        if len(arches) == 2:
            self.gen_seccomp_policy_of_arch(arches[1])

        self.bpf_generator.add_validate_arch(arches, skip_step)

    def gen_output_file(self, args):
        if not self.bpf_generator.bpf_policy:
            raise ValidateError("bpf_policy is empty!")

        header = textwrap.dedent('''\

            #include <linux/filter.h>
            #include <stddef.h>
            #include <linux/seccomp.h>
            #include <linux/audit.h>
            ''')
        extra_header = set()
        for arch in self.arches:
            extra_header |= self.seccomp_policy_param.get(arch).head_files
        extra_header_list = ['#include ' + i for i in sorted(list(extra_header))]
        filter_name = 'g_' + args.filter_name + 'SeccompFilter'

        array_name = textwrap.dedent('''

            const struct sock_filter {}[] = {{
            ''').format(filter_name)

        footer = textwrap.dedent('''\

            }};

            const size_t {} = sizeof({}) / sizeof(struct sock_filter);
            ''').format(filter_name + 'Size', filter_name)

        content = header + '\n'.join(extra_header_list) + array_name + \
            '    ' + '\n    '.join(self.bpf_generator.bpf_policy) + footer

        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        modes = stat.S_IWUSR | stat.S_IRUSR | stat.S_IWGRP | stat.S_IRGRP
        with os.fdopen(os.open(args.dst_file, flags, modes), 'w') as output_file:
            output_file.write(content)

    def gen_seccomp_policy_code(self, args):
        if args.target_cpu not in supported_architecture:
            raise ValidateError('target cpu not supported')
        function_name_nr_table_dict = {}
        for file_name in args.src_files:
            file_name_tmp = file_name.split('/')[-1]
            if not file_name_tmp.lower().startswith('libsyscall_to_nr_'):
                continue
            function_name_nr_table_dict = gen_syscall_nr_table(file_name, function_name_nr_table_dict)


        for arch in supported_architecture:
            self.seccomp_policy_param.update(
                {arch: SeccompPolicyParam(arch, function_name_nr_table_dict.get(arch), args.is_debug)})
            self.reduced_block_list_parm.update(
                {arch: AllowBlockList(args.filter_name, arch, function_name_nr_table_dict.get(arch))})

        self.bpf_generator.update_function_name_nr_table(function_name_nr_table_dict)

        self.update_arch(args.target_cpu)
        self.update_is_debug(args.is_debug)

        for file_name in args.blocklist_file:
            if file_name.lower().endswith('blocklist.seccomp.policy'):
                self.parse_file(file_name)

        for file_name in args.keyprocess_file:
            if file_name.lower().endswith('privileged_process.seccomp.policy'):
                self.key_process_flag = True
                self.parse_file(file_name)
                self.key_process_flag = False

        self.update_block_list()

        for file_name in args.src_files:
            if file_name.lower().endswith('.policy'):
                self.parse_file(file_name)

        if self.bpf_generator.get_gen_flag():
            self.gen_seccomp_policy()

        if self.bpf_generator.get_gen_flag():
            self.gen_output_file(args)


def main():
    parser = argparse.ArgumentParser(
      description='Generates a seccomp-bpf policy')
    parser.add_argument('--src-files', type=str, action='append',
                        help=('The input files\n'))

    parser.add_argument('--blocklist-file', type=str, action='append',
                        help=('input basic blocklist file(s)\n'))

    parser.add_argument('--keyprocess-file', type=str, action='append',
                        help=('input key process file(s)\n'))

    parser.add_argument('--dst-file',
                        help='The output path for the policy files')

    parser.add_argument('--filter-name', type=str,
                        help='Name of seccomp bpf array generated by this script')

    parser.add_argument('--target-cpu', type=str,
                        help=('please input target cpu arm or arm64\n'))

    parser.add_argument('--is-debug', type=str,
                        help=('please input is_debug true or false\n'))

    args = parser.parse_args()

    generator = SeccompPolicyParser()
    generator.gen_seccomp_policy_code(args)


if __name__ == '__main__':
    sys.exit(main())
