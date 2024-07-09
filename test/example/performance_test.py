#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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


import time
import os
import sys
import platform
import pty
import threading
import re
import traceback
import select
import subprocess
import queue
import shutil

from collections import defaultdict

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mylogger.py"))
from mylogger import get_logger, parse_json

Log = get_logger("performance")

log_info = Log.info
log_error = Log.error
script_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

config = parse_json()
if not config:
    log_error("config file: build_example.json not exist")
    raise FileNotFoundError("config file: build_example.json not exist")


class PerformanceAnalyse:

    self.html_tamplate = """
                          <!DOCTYPE html>
                          <html lang="en">
                          <head>
                          <style type="text/css" media="screen">
                              table {{
                                  border-collapse: collapse;
                                  width: 80%;
                                  max-width: 1200px;
                                  margin-bottom: 30px;
                                  margin-left: auto;
                                  margin-right: auto;
                                  table-layout: fixed;
                              }}
                              th, td {{
                                  padding: 10px;
                                  text-align: center;
                                  font-size: 12px;
                                  border: 1px solid #ddd;  
                                  word-wrap: break-word;
                              }}
                              th {{
                                  background-color: #f2f2f2;
                                  font-weight: bold;
                                  text-transform: capitalize;
                              }}
                              tr:nth-child(even) {{
                                  background-color: #f9f9f9;
                              }}
                              caption {{
                                  font-size: 24px;
                                  margin-bottom: 16px;
                                  color: #333;
                                  text-transform: uppercase;
                                  letter-spacing: 2px;
                                  font-family: Arial, sans-serif;
                                  text-align: center;
                                  text-transform: capitalize;
                              }}
                              .container {{
                                  width: 80%;
                                  margin: 0 auto;
                              }}
                           body  {{ font-family: Microsoft YaHei,Tahoma,arial,helvetica,sans-serif;padding: 20px;}}
                           h1 {{ text-align: center; }}
                          </style>
                          </head>
                          <body>
                          <div class="container">
                          <h1>{}</h1>
                          """

    try:
        TIMEOUT = int(config.get("performance").get("performance_exec_timeout"))
        select_timeout = float(config.get("performance").get("performance_select_timeout"))
        top_count = int(config.get("performance").get("performance_top_count"))
        overflow = float(config.get("performance").get("performance_overflow"))
        exclude = config.get("performance").get("exclude")
        log_info("TIMEOUT:{}".format(TIMEOUT))
        log_info("select_timeout:{}".format(select_timeout))
        log_info("top_count:{}".format(top_count))
        log_info("overflow:{} sec".format(overflow))
    except Exception as e:
        log_error("config file:build_example.json has error:{}".format(e))
        raise FileNotFoundError("config file:build_example.json has error:{}".format(e))

    def __init__(self, performance_cmd, output_path, report_titles, ptyflags=False):
        self.performance_cmd = script_path + performance_cmd
        self.output_path = script_path + output_path
        self.report_title = report_titles
        self.ptyflag = ptyflags
        self.out_queue = queue.Queue()
        self.system_info = list()
        self.ninjia_trace_list = list()
        self.gn_exec_li = list()
        self.gn_script_li = list()
        self.gn_end_li = list()
        self.ccache_li = list()
        self.c_targets_li = list()
        self.root_dir = None
        self.gn_dir = None
        self.gn_script_res = None
        self.gn_exec_res = None
        self.cost_time_res = list()
        self.gn_exec_flag = re.compile(r"File execute times")
        self.gn_script_flag = re.compile(r"Script execute times")
        self.gn_end_flag = re.compile(r"Done\. Made \d+ targets from \d+ files in (\d+)ms")
        self.root_dir_flag = re.compile(r"""loader args.*source_root_dir="([a-zA-Z\d/\\_]+)""""")
        self.gn_dir_flag = re.compile(r"""loader args.*gn_root_out_dir="([a-zA-Z\d/\\_]+)""""")
        self.ccache_start_flag = re.compile(r"ccache_dir =")
        self.ccache_end_flag = re.compile(r"c targets overlap rate statistics")
        self.c_targets_flag = re.compile(r"c overall build overlap rate")
        self.build_error = re.compile(r"=====build\s\serror=====")
        self.ohos_error = re.compile(r"OHOS ERROR")
        self.total_flag = re.compile(r"Cost time:.*(\d+:\d+:\d+)")
        self.total_cost_time = None
        self.error_message = list()
        self.during_time_dic = {
            "Preloader": {"start_pattern": re.compile(r"Set cache size"),
                          "end_pattern": re.compile(r"generated compile_standard_whitelist"),
                          "start_time": 0,
                          "end_time": 0
                          },
            "Loader": {"start_pattern": re.compile(r"Checking all build args"),
                       "end_pattern": re.compile(r"generate target syscap"),
                       "start_time": 0,
                       "end_time": 0
                       },
            "Ninjia": {"start_pattern": re.compile(r"Done\. Made \d+ targets from \d+ files in (\d+)ms"),
                       "end_pattern": re.compile(r"ccache_dir ="),
                       "start_time": 0,
                       "end_time": 0
                       }}
        self.table_html = ""
        self.base_html = self.html_tamplate.format(self.report_title)
        self.remove_out()

    def remove_out(self):
        """
        Description: remove out dir
        """
        out_dir = os.path.join(script_path, "out")
        try:
            if not os.path.exists(out_dir):
                return
            for tmp_dir in os.listdir(out_dir):
                if tmp_dir in self.exclude:
                    continue
                if os.path.isdir(os.path.join(out_dir, tmp_dir)):
                    shutil.rmtree(os.path.join(out_dir, tmp_dir))
                else:
                    os.remove(os.path.join(out_dir, tmp_dir))
        except Exception as e:
            log_error(e)

    def write_html(self, content):
        """
        Description: convert html str
        @parameter content: html str
        """
        if not os.path.exists(os.path.dirname(self.output_path)):
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as html_file:
            html_file.write(content)

    def generate_content(self, table_name, data_rows, switch=False):
        """
        Description: generate html content
        @parameter table_name: table name
        @parameter data_rows: two-dimensional array data
        @parameter switch: change overflow data color
        """
        table_title = table_name.capitalize()
        if not data_rows[1:]:
            log_error("【{}】 is None")
            return False
        tb_html = """
               <table style="width: 100%; max-width: 1200px;">
               <caption>{0}</caption>
               <colgroup>
                   <col style="width: {1}%"/>
               </colgroup>
               <thead>
               <tr class="text-center success" style="font-weight: bold;font-size: 14px;">
                  """.format(table_title, int(100 / len(data_rows[0])))

        self.table_html += tb_html

        for header in data_rows[0]:
            self.table_html += "<th>{}</th>".format(header.capitalize())
        self.table_html += "</tr></thead>"

        self.table_html += "<tbody>"
        if switch:
            for index, row in enumerate(data_rows[1:]):
                if float(row[-1]) > float(self.overflow):
                    self.table_html += "<tr style='background-color:  #ff7f50;'>"
                elif float(row[-1]) <= float(self.overflow) and index % 2 == 0:
                    self.table_html += "<tr style='background-color:  #f5f5f5;'>"
                else:
                    self.table_html += "<tr>"
                for data in row:
                    self.table_html += "<td>{}</td>".format(data)
                self.table_html += "</tr>"
        else:
            for index, row in enumerate(data_rows[1:]):
                if index % 2 == 0:
                    self.table_html += "<tr style='background-color: #f5f5f5;'>"
                else:
                    self.table_html += "<tr>"
                for data in row:
                    self.table_html += "<td>{}</td>".format(data)
                self.table_html += "</tr>"
        self.table_html += "</tbody>"

        self.table_html += "</table></div></body></html>"
        return True

    @staticmethod
    def generate_error_content(table_name, lines):
        """
        Description: generate error html content
        @parameter table_name: table name
        @parameter lines: error message
        """
        table_title = table_name.capitalize()
        lines = ['<br>' + text for text in lines]
        html_content = '<center><h1>{}</h1><div style="text-align:left;">{}<div></center>'.format(table_title,
                                                                                                  '\n'.join(lines))
        error_html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Ohos Error</title></head><body>{}</body></html>'.format(
            html_content)
        return error_html

    def read_ninjia_trace_file(self):
        """
        Description: read ninjia trace file
        """
        try:
            ninja_trace_path = os.path.join(self.root_dir, self.gn_dir, "sorted_action_duration.txt")
            with open(ninja_trace_path, 'r') as f:
                for line in f:
                    yield line.strip()
        except Exception as e:
            log_error("open ninjia trace file error is:{}".format(e))

    def process_ninja_trace(self):
        """
        Description: generate ninja trace table data
        """
        data = defaultdict(list)
        result_list = list()

        for line in self.read_ninjia_trace_file():
            line_list = line.split(":")
            name = line_list[0].strip()
            if name == "total time":
                continue
            duration = int(line_list[1].strip())
            data[name].append(duration)

        for key, value in data.items():
            result = [key, len(value), max(value)]
            result_list.append(result)
        sort_result = sorted(result_list, key=lambda x: x[2], reverse=True)
        for i in range(len(sort_result)):
            sort_result[i][2] = round(float(sort_result[i][2]) / 1000, 4)

        self.ninjia_trace_list = sort_result[:self.top_count]

        self.ninjia_trace_list.insert(0, ["Ninjia Trace File", "Call Count", "Ninjia Trace Cost Time(s)"])

    def process_gn_trace(self):
        """
        Description: generate gn trace table data
        """
        self.gn_exec_res = [[item[2], item[1], round(float(item[0]) / 1000, 4)] for item in self.gn_exec_li if
                            item and re.match(r"[\d.]+", item[0])][
                           :self.top_count]
        self.gn_script_res = [[item[2], item[1], round(float(item[0]) / 1000, 4)] for item in self.gn_script_li if
                              item and re.match(r"[\d.]+", item[0])][:self.top_count]

        self.gn_exec_res.insert(0, ["Gn Trace Exec File", "Call Count", "GN Trace Exec Cost Time(s)"])

        self.gn_script_res.insert(0, ["Gn Trace Script File", "Call Count", "GN Trace Script Cost Time(s)"])

    def process_ccache_ctargets(self):
        """
        Description: generate gn trace table data
        """
        ccache_res = []
        c_targets_res = []
        for tmp in self.ccache_li:
            if ":" in tmp and len(tmp.split(":")) == 2:
                ccache_res.append(tmp.split(":"))
        ccache_res.insert(0, ["ccache item", "data"])

        for item_ in self.c_targets_li:
            if len(item_.split()) == 6:
                c_targets_res.append(item_.split())
        c_targets_res.insert(0, ["subsystem", "files NO.", " percentage", "builds NO.", "percentage", "verlap rate"])
        return ccache_res, c_targets_res

    def process_system(self):
        """
        Description: generate system data
        """
        start_li = [
            ["System Information name", "System Value"],
            ['Python Version', sys.version],
            ['Cpu Count', os.cpu_count()],
            ["System Info", platform.platform()]
        ]

        self.system_info.extend(start_li)
        try:
            disk_info = os.statvfs('/')
            total_disk = round(float(disk_info.f_frsize * disk_info.f_blocks) / (1024 ** 3), 4)

            self.system_info.append(["Disk Size", "{} GB".format(total_disk)])
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            total_memory_line = [line for line in lines if line.startswith('MemTotal')]
            total_memory = round(float(total_memory_line[0].split()[1]) / (1024 ** 2), 4) if total_memory_line else " "

            self.system_info.append(["Total Memory", "{} GB".format(total_memory)])
        except Exception as e:
            log_error(e)

    def process_cost_time(self):
        """
        Description: generate summary table data
        """
        for i in self.during_time_dic.keys():
            cost_time = (self.during_time_dic.get(i).get("end_time") - self.during_time_dic.get(i).get(
                "start_time")) / 10 ** 9
            new_cost_time = round(float(cost_time), 4)
            self.cost_time_res.append([i, new_cost_time])
        gn_res = re.search(self.gn_end_flag, self.gn_end_li[0])
        if gn_res:
            gn_time = round(float(gn_res.group(1)) / 1000, 4)
            self.cost_time_res.append(['GN', gn_time])
        self.cost_time_res.append(["Total", self.total_cost_time])
        self.cost_time_res.insert(0, ["Compile Process Phase", "Cost Time(s)"])

    def producer(self, execute_cmd, out_queue, timeout=TIMEOUT):
        """
        Description: execute cmd and put cmd result data to queue
        @parameter execute_cmd: execute cmd
        @parameter out_queue: save out data
        @parameter timeout: execute cmd time out
        @return returncode: returncode
        """
        log_info("exec cmd is :{}".format(" ".join(execute_cmd)))
        log_info("ptyflag is :{}".format(self.ptyflag))

        if self.ptyflag:
            try:
                master, slave = pty.openpty()
                proc = subprocess.Popen(
                    execute_cmd,
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    encoding="utf-8",
                    universal_newlines=True,
                    errors='ignore',
                    cwd=script_path

                )
                start_time = time.time()
                incomplete_line = ""
                while True:
                    if timeout and time.time() - start_time > timeout:
                        raise Exception("exec cmd time out,select")
                    ready_to_read, _, _ = select.select([master, ], [], [], PerformanceAnalyse.select_timeout)
                    for stream in ready_to_read:
                        output_bytes = os.read(stream, 1024)
                        output = output_bytes.decode('utf-8')
                        lines = (incomplete_line + output).split("\n")
                        for line in lines[:-1]:
                            line = line.strip()
                            if line:
                                out_str = "{}".format(time.time_ns()) + "[timestamp]" + line
                                out_queue.put(out_str)
                        incomplete_line = lines[-1]
                    if proc.poll() is not None:
                        out_queue.put(None)
                        break
                returncode = proc.wait()
                return returncode
            except Exception as e:
                out_queue.put(None)
                log_error("Producer An error occurred:{}".format(e))
                err_str = traceback.format_exc()
                log_error(err_str)
                raise e
        else:
            try:
                start_time = time.time()
                proc = subprocess.Popen(
                    execute_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    universal_newlines=True,
                    errors='ignore',
                    cwd=script_path
                )

                while True:
                    if timeout and time.time() - start_time > timeout:
                        raise TimeoutError("exec cmd timeout")
                    ready_to_read, _, _ = select.select([proc.stdout, proc.stderr], [], [],
                                                        PerformanceAnalyse.select_timeout)
                    for stream in ready_to_read:
                        output = stream.readline().strip()
                        if output:
                            out_str = "{}".format(time.time_ns()) + "[timestamp]" + output
                            out_queue.put(out_str)
                    if proc.poll() is not None:
                        out_queue.put(None)
                        break
                returncode = proc.wait()
                return returncode
            except Exception as e:
                out_queue.put(None)
                log_error("Producer An error occurred:{}".format(e))
                err_str = traceback.format_exc()
                log_error(err_str)
                raise e

    def consumer(self, out_queue, timeout=TIMEOUT):
        """
        Description: get cmd result data from queue
        @parameter out_queue: save out data
        @parameter timeout: execute cmd time out
        """
        start_time = time.time()
        try:
            line_count = 0
            gn_exec_start, gn_script, gn_end, ccache_start, ccache_end, c_tagart_end = None, None, None, None, None, None
            while True:
                if timeout and time.time() - start_time > timeout:
                    raise TimeoutError("consumer timeout")

                output = out_queue.get()
                if output is None:
                    log_info(".....................exec end...........................")
                    break
                line_count += 1
                log_info(output.split("[timestamp]")[1])
                line_mes = " ".join(output.split("[timestamp]")[1].split()[2:])
                time_stamp = output.split("[timestamp]")[0]

                if re.search(self.root_dir_flag, output):
                    self.root_dir = re.search(self.root_dir_flag, output).group(1)

                if re.search(self.gn_dir_flag, output):
                    self.gn_dir = re.search(self.gn_dir_flag, output).group(1)

                for key, value in self.during_time_dic.items():
                    if re.search(value.get("start_pattern"), output):
                        self.during_time_dic.get(key)["start_time"] = int(time_stamp)
                    if re.search(value["end_pattern"], output):
                        self.during_time_dic.get(key)["end_time"] = int(time_stamp)

                if re.search(self.gn_exec_flag, output):
                    gn_exec_start = line_count
                elif re.search(self.gn_script_flag, output):
                    gn_script = line_count
                elif re.search(self.gn_end_flag, output):
                    gn_end = line_count
                    self.gn_end_li.append(line_mes)
                elif re.search(self.ccache_start_flag, output):
                    ccache_start = line_count
                elif re.search(self.ccache_end_flag, output):
                    ccache_end = line_count
                elif re.search(self.c_targets_flag, output):
                    c_tagart_end = line_count

                if gn_exec_start and line_count > gn_exec_start and not gn_script:
                    self.gn_exec_li.append(line_mes.split())
                elif gn_script and line_count > gn_script and not gn_end:
                    self.gn_script_li.append(line_mes.split())
                elif ccache_start and line_count > ccache_start and not ccache_end:
                    self.ccache_li.append(line_mes)
                elif ccache_end and line_count > ccache_end and not c_tagart_end:
                    self.c_targets_li.append(line_mes)

                if re.search(self.ohos_error, output) or re.search(self.build_error, output):
                    self.error_message.append(
                        re.sub(r"\x1b\[[0-9;]*m", "", output.split("[timestamp]")[1].strip()))

                if re.search(self.total_flag, output):
                    total_time_str = re.search(self.total_flag, output).group(1)
                    time_obj = time.strptime(total_time_str, "%H:%M:%S")
                    milliseconds = (time_obj.tm_hour * 3600 + time_obj.tm_min * 60 + time_obj.tm_sec)
                    self.total_cost_time = milliseconds

        except Exception as e:
            log_error("Consumer An error occurred:{}".format(e))
            err_str = traceback.format_exc()
            log_error(err_str)
            raise e

    def exec_command_pipe(self, execute_cmd):
        """
        Description: start producer and consumer
        @parameter execute_cmd: execute cmd
        """
        try:
            producer_thread = threading.Thread(target=self.producer, args=(execute_cmd, self.out_queue))
            consumer_thread = threading.Thread(target=self.consumer, args=(self.out_queue,))
            producer_thread.daemon = True
            consumer_thread.daemon = True
            producer_thread.start()
            consumer_thread.start()
            producer_thread.join()
            consumer_thread.join()
        except Exception as e:
            err_str = traceback.format_exc()
            log_error(err_str)
            raise Exception(e)

    def process(self):
        """
        Description: start performance test
        """
        try:
            cmds = self.performance_cmd.split(" ")
            self.exec_command_pipe(cmds)
            if self.error_message:
                err_html = self.generate_error_content("Ohos Error", self.error_message)
                self.write_html(err_html)
                return

            self.process_system()
            self.process_cost_time()
            self.process_gn_trace()
            self.process_ninja_trace()
            ccache_res, c_targets_res = self.process_ccache_ctargets()

            log_info(self.cost_time_res)
            log_info(self.gn_exec_res)
            log_info(self.gn_script_res)
            log_info(self.ninjia_trace_list)
            log_info(ccache_res)
            log_info(c_targets_res)
            self.generate_content("System Information", self.system_info)
            self.generate_content("Compile Process Summary", self.cost_time_res)
            self.generate_content("Gn Trace Exec File", self.gn_exec_res, switch=True)
            self.generate_content("Gn Trace Script File ", self.gn_script_res, switch=True)
            self.generate_content("Ninjia Trace File", self.ninjia_trace_list, switch=True)
            self.generate_content("Ccache Data Statistics", ccache_res)
            self.generate_content("C Targets Overlap Rate Statistics", c_targets_res)
            res_html = self.base_html + self.table_html
            self.write_html(res_html)
        except Exception as e:
            err_str = traceback.format_exc()
            log_error(err_str)
            err_html = self.generate_error_content("Performance system Error", err_str.split("\n"))
            self.write_html(err_html)


if __name__ == '__main__':
    performance_script_data = config.get("performance").get("performance_script_data")
    for item in performance_script_data:
        cmd = item.get("performance_cmd")
        path = item.get("output_path")
        report_title = item.get("report_title")
        ptyflag = True if item.get("ptyflag").lower() == "true" else False
        if all([cmd, path, report_title]):
            performance = PerformanceAnalyse(cmd, path, report_title, ptyflag)
            performance.process()

