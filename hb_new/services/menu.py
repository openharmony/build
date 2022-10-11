#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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

from __future__ import print_function
from __future__ import unicode_literals

import sys
import importlib

from prompt_toolkit.shortcuts import run_application
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.filters import IsDone
from prompt_toolkit.layout.controls import TokenListControl
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.token import Token

from exceptions.ohosException import OHOSException
from services.interface.menuInterface import MenuInterface
from helper.separator import Separator
from containers.arg import Arg, ModuleType
from resources.config import Config

from util.logUtil import LogUtil
from util.productUtil import ProductUtil


class Menu(MenuInterface):

    def select_compile_option(self) -> dict:
        config = Config()
        results = {}
        all_build_args = Arg.parse_all_args(ModuleType.BUILD)
        for arg in all_build_args.values():
            if isinstance(arg, Arg) and arg.argAttribute.get("optional"):
                if arg.argName != 'target_cpu':
                    choices = [
                        choice if isinstance(choice, Separator) else {
                            'name': choice,
                            'value': arg.argName
                        } for choice in arg.argAttribute.get("optional")
                    ]
                else:
                    if config.support_cpu != None and isinstance(config.support_cpu, list):
                        choices = []
                        for cpu in config.support_cpu:
                            choices.append({
                                'name': cpu,
                                'value': arg.argName,
                            })
                    elif config.target_cpu != None:
                        choices = [
                            {
                                'name': config.target_cpu,
                                'value': arg.argName,
                            }
                        ]
                    else:
                        choices = [
                            {
                                'name': all_build_args['target_cpu'].argValue,
                                'value': arg.argName,
                            }
                        ]

                result = self._list_promt(arg.argName, 'select {} value'.format(
                    arg.argName), choices)[arg.argName][0]
                results[arg.argName] = result
        return results

    def select_product(self) -> dict:
        product_path_dict = {}
        company_separator = None
        for product_info in ProductUtil.get_products():
            company = product_info['company']
            product = product_info['name']
            if company_separator is None or company_separator != company:
                company_separator = company
                product_key = Separator(company_separator)
                product_path_dict[product_key] = None

            product_path_dict['{}@{}'.format(product, company)] = product_info

        if not len(product_path_dict):
            raise OHOSException('no valid product found')

        choices = [
            product if isinstance(product, Separator) else {
                'name': product.split('@')[0],
                'value': product.split('@')[1]
            } for product in product_path_dict.keys()
        ]
        product = self._list_promt('product', 'Which product do you need?',
                                   choices).get('product')
        product_key = f'{product[0]}@{product[1]}'
        return product_path_dict[product_key]

    def _list_promt(self, name, message, choices, **kwargs):
        questions = self._get_questions('list', name, message, choices)

        return self._prompt(questions=questions, **kwargs)

    def _get_questions(self, promt_type, name, message, choices):
        questions = [{
            'type': promt_type,
            'qmark': 'OHOS',
            'name': name,
            'message': message,
            'choices': choices
        }]

        return questions

    def _prompt(self, questions, answers=None, **kwargs):
        if isinstance(questions, dict):
            questions = [questions]
        answers = answers or {}

        patch_stdout = kwargs.pop('patch_stdout', False)
        return_asyncio_coroutine = kwargs.pop(
            'return_asyncio_coroutine', False)
        true_color = kwargs.pop('true_color', False)
        refresh_interval = kwargs.pop('refresh_interval', 0)
        eventloop = kwargs.pop('eventloop', None)
        kbi_msg = kwargs.pop('keyboard_interrupt_msg', 'Cancelled by user')

        for question in questions:
            try:
                choices = question.get('choices')
                if choices is not None and callable(choices):
                    question['choices'] = choices(answers)

                _kwargs = {}
                _kwargs.update(kwargs)
                _kwargs.update(question)
                question_type = _kwargs.pop('type')
                name = _kwargs.pop('name')
                message = _kwargs.pop('message')
                when = _kwargs.pop('when', None)
                question_filter = _kwargs.pop('filter', None)

                if when:
                    # at least a little sanity check!
                    if callable(question['when']):
                        try:
                            if not question['when'](answers):
                                continue
                        except Exception as error:
                            raise ValueError(
                                'Problem in \'when\' check of %s question: %s' %
                                (name, error))
                    else:
                        raise ValueError('\'when\' needs to be function that '
                                         'accepts a dict argument')
                if question_filter:
                    # at least a little sanity check!
                    if not callable(question['filter']):
                        raise ValueError('\'filter\' needs to be function that '
                                         'accepts an argument')

                if callable(question.get('default')):
                    _kwargs['default'] = question['default'](answers)

                application = self._question(message, **_kwargs)

                answer = run_application(
                    application,
                    patch_stdout=patch_stdout,
                    return_asyncio_coroutine=return_asyncio_coroutine,
                    true_color=true_color,
                    refresh_interval=refresh_interval,
                    eventloop=eventloop)

                if answer is not None:
                    if question_filter:
                        try:
                            answer = question['filter'](answer)
                        except Exception as error:
                            raise ValueError('Problem processing \'filter\' of'
                                             '{} question: {}'.format(name, error))
                    answers[name] = answer
            except AttributeError as attr_error:
                LogUtil.hb_error(attr_error)
                raise ValueError('No question type \'%s\'' % question_type)
            except KeyboardInterrupt:
                LogUtil.hb_warning('')
                LogUtil.hb_warning(kbi_msg)
                LogUtil.hb_warning('')
                return {}
        return answers

    def _question(self, message, **kwargs):
        if 'choices' not in kwargs:
            raise OHOSException("You must choose one platform.")

        choices = kwargs.pop('choices', None)
        qmark = kwargs.pop('qmark', '?')
        style = kwargs.pop('style', _get_style('terminal'))

        inquirer_control = InquirerControl(choices)

        def get_prompt_tokens(cli):
            tokens = []

            tokens.append((Token.QuestionMark, qmark))
            tokens.append((Token.Question, ' %s ' % message))
            if inquirer_control.answered:
                tokens.append((Token.Answer, ' ' +
                               inquirer_control.get_selection()[0]))
            else:
                tokens.append((Token.Instruction, ' (Use arrow keys)'))
            return tokens

        # assemble layout
        layout = HSplit([
            Window(height=D.exact(1),
                   content=TokenListControl(get_prompt_tokens)),
            ConditionalContainer(
                Window(inquirer_control),
                filter=~IsDone()
            )
        ])

        # key bindings
        manager = KeyBindingManager.for_prompt()

        @manager.registry.add_binding(Keys.ControlQ, eager=True)
        @manager.registry.add_binding(Keys.ControlC, eager=True)
        def _(event):
            raise KeyboardInterrupt()

        @manager.registry.add_binding(Keys.Down, eager=True)
        def move_cursor_down(event):
            def _next():
                inquirer_control.selected_option_index = (
                    (inquirer_control.selected_option_index + 1) %
                    inquirer_control.choice_count)
            _next()
            while isinstance(inquirer_control.choices[
                inquirer_control.selected_option_index][0], Separator) \
                    or inquirer_control.choices[
                        inquirer_control.selected_option_index][2]:
                _next()

        @manager.registry.add_binding(Keys.Up, eager=True)
        def move_cursor_up(event):
            def _prev():
                inquirer_control.selected_option_index = (
                    (inquirer_control.selected_option_index - 1) %
                    inquirer_control.choice_count)
            _prev()
            while isinstance(inquirer_control.choices[
                inquirer_control.selected_option_index][0], Separator) \
                    or inquirer_control.choices[
                        inquirer_control.selected_option_index][2]:
                _prev()

        @manager.registry.add_binding(Keys.Enter, eager=True)
        def set_answer(event):
            inquirer_control.answered = True
            event.cli.set_return_value(inquirer_control.get_selection())

        return Application(
            layout=layout,
            key_bindings_registry=manager.registry,
            mouse_support=False,
            style=style
        )


class InquirerControl(TokenListControl):
    def __init__(self, choices, **kwargs):
        self.selected_option_index = 0
        self.answered = False
        self.choices = choices
        self._init_choices(choices)
        super(InquirerControl, self).__init__(self._get_choice_tokens,
                                              **kwargs)

    def _init_choices(self, choices, default=None):
        # helper to convert from question format to internal format
        self.choices = []  # list (name, value, disabled)
        searching_first_choice = True
        for index, choice in enumerate(choices):
            if isinstance(choice, Separator):
                self.choices.append((choice, None, None))
            else:
                base_string = str if sys.version_info[0] >= 3 else None
                if isinstance(choice, base_string):
                    self.choices.append((choice, choice, None))
                else:
                    name = choice.get('name')
                    value = choice.get('value', name)
                    disabled = choice.get('disabled', None)
                    self.choices.append((name, value, disabled))
                if searching_first_choice:
                    self.selected_option_index = index
                    searching_first_choice = False

    @property
    def choice_count(self):
        return len(self.choices)

    def _get_choice_tokens(self, cli):
        tokens = []
        token = Token

        def append(index, choice):
            selected = (index == self.selected_option_index)

            @_if_mousedown
            def select_item(cli, mouse_event):
                # bind option with this index to mouse event
                self.selected_option_index = index
                self.answered = True

            tokens.append((token.Pointer if selected else token, ' \u276f '
                          if selected else '   '))
            if selected:
                tokens.append((Token.SetCursorPosition, ''))
            if choice[2]:  # disabled
                tokens.append((token.Selected if selected else token,
                               '- %s (%s)' % (choice[0], choice[2])))
            else:
                if isinstance(choice[0], Separator):
                    tokens.append((token.Separator,
                                  str(choice[0]),
                                  select_item))
                else:
                    try:
                        tokens.append((token.Selected if selected else token,
                                      str(choice[0]), select_item))
                    except Exception:
                        tokens.append((token.Selected if selected else
                                      token, choice[0], select_item))
            tokens.append((token, '\n'))

        # prepare the select choices
        for i, choice in enumerate(self.choices):
            append(i, choice)
        tokens.pop()  # Remove last newline.
        return tokens

    def get_selection(self):
        return self.choices[self.selected_option_index]


def _get_style(style_type):
    style = importlib.import_module('prompt_toolkit.styles')
    token = importlib.import_module('prompt_toolkit.token')
    if style_type == 'terminal':
        return style.style_from_dict({
            token.Token.Separator: '#75c951',
            token.Token.QuestionMark: '#5F819D',
            token.Token.Selected: '',  # default
            token.Token.Pointer: '#FF9D00 bold',  # AWS orange
            token.Token.Instruction: '',  # default
            token.Token.Answer: '#FF9D00 bold',  # AWS orange
            token.Token.Question: 'bold',
        })
    if style_type == 'answer':
        return style.style_from_dict({
            token.Token.Separator: '#75c951',
            token.Token.QuestionMark: '#E91E63 bold',
            token.Token.Selected: '#cc5454',  # default
            token.Token.Pointer: '#ed9164 bold',
            token.Token.Instruction: '',  # default
            token.Token.Answer: '#f44336 bold',
            token.Token.Question: '',
        })

    return None


def _if_mousedown(handler):
    def handle_if_mouse_down(cli, mouse_event):
        mouse_events = importlib.import_module('prompt_toolkit.mouse_events')
        if mouse_event.event_type == mouse_events.MouseEventTypes.MOUSE_DOWN:
            return handler(cli, mouse_event)
        else:
            return NotImplemented

    return handle_if_mouse_down
