from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
import pexpect

from subprocess import check_output
import os.path
import sys
from pathlib2 import Path

import re
import signal
import logging
import time

__version__ = '0.1.1'

#version_pat = re.compile(r'version (\d+(\.\d+)+)')

# from .images import (
#     extract_image_filenames, display_data_for_image, image_setup_cmd
# )
#
# class IREPLWrapper(replwrap.REPLWrapper):
#     """A subclass of REPLWrapper that gives incremental output
#     specifically for bash_kernel.
#
#     The parameters are the same as for REPLWrapper, except for one
#     extra parameter:
#
#     :param line_output_callback: a callback method to receive each batch
#       of incremental output. It takes one string parameter.
#     """
#     def __init__(self, cmd_or_spawn, orig_prompt, prompt_change,
#                  extra_init_cmd=None, line_output_callback=None):
#         self.line_output_callback = line_output_callback
#         replwrap.REPLWrapper.__init__(self, cmd_or_spawn, orig_prompt,
#                                       prompt_change, extra_init_cmd=extra_init_cmd)
#
#     def _expect_prompt(self, timeout=-1):
#         if timeout == None:
#             # "None" means we are executing code from a Jupyter cell by way of the run_command
#             # in the do_execute() code below, so do incremental output.
#             while True:
#                 pos = self.child.expect_exact([self.prompt, self.continuation_prompt, u'\r\n'],
#                                               timeout=None)
#                 if pos == 2:
#                     # End of line received
#                     self.line_output_callback(self.child.before + '\n')
#                 else:
#                     if len(self.child.before) != 0:
#                         # prompt received, but partial line precedes it
#                         self.line_output_callback(self.child.before)
#                     break
#         else:
#             # Otherwise, use existing non-incremental code
#             pos = replwrap.REPLWrapper._expect_prompt(self, timeout=timeout)
#
#         # Prompt received, so return normally
#         return pos

class RaxKernel(Kernel):
    implementation = 'rax_kernel'
    implementation_version = __version__

    @property
    def language_version(self):
        return "1.3"
        # m = version_pat.search(self.banner)
        # return m.group(1)

    # _banner = None
    #
    # @property
    # def banner(self):
    #     if self._banner is None:
    #         self._banner = check_output(['bash', '--version']).decode('utf-8')
    #     return self._banner

    @property
    def banner(self):
        return "Hi, I'm Rax!"

    language_info = {'name': 'rax',
                     'mimetype': 'text/x-rax',
                     'file_extension': '.rax',
                     'pygments_lexer': 'rax'}

    rax_running = False

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        logger = logging.getLogger('rax_kernel')
        fh = logging.FileHandler('rax_kernel.log')
        fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        self.rax_running = False

    def _start_rax(self, dburl = None):
        self.logger.debug("Starting Rax kernel")
        # Signal handlers are inherited by forked processes, and we can't easily
        # reset it from the subprocess. Since kernelapp ignores SIGINT except in
        # message handlers, we need to temporarily reset the SIGINT handler here
        # so that bash and its children are interruptible.
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            # Note: the next few lines mirror functionality in the
            # bash() function of pexpect/replwrap.py.  Look at the
            # source code there for comments and context for
            # understanding the code here.
            if dburl:
                params = ['-s', '-u', dburl, '-D', 'IDE:=1']
            else:
                params = ['-s', '-B', '-D', 'IDE:=1']
            self.raxwrapper = pexpect.spawn("/Users/chosia/codersco/RaxCore/start_rax",
                                            params, echo=False,
#                                            encoding='utf-8',
                                            codec_errors='replace')
            fout = file('child.log', 'w')
            self.raxwrapper.logfile = fout

            self.raxwrapper.sendline('''%include __EXE_PATH__ "/rx_GraphicalEngine/SimpleCharts.rax";''')
            self.raxwrapper.sendline('''`print "Rax$ready";''')
            idx = self.raxwrapper.expect([pexpect.EOF, "Rax\$ready"])
            if idx == 0:
                #We're unable to start Rax
                out = self.raxwrapper.before
                self.logger.error("Unable to start Rax")
                self.logger.debug("Rax output: {0}".format(out))
                self.process_output(out)
            else:
                self.rax_running = True

        finally:
            signal.signal(signal.SIGINT, sig)

    def _stop_rax(self):
        self.raxwrapper.sendeof()
        self.rax_running = False

    def process_output(self, output):
        if not self.silent:
            # Send standard output
            stream_content = {'name': 'stdout', 'text': output}
            display_data_content = {
                'data': {
                    'text/markdown' : output
                },
                'metadata': {}
            }
            self.logger.debug('Sending display data: {0}'.format(display_data_content))
            self.send_response(self.iopub_socket, 'display_data', display_data_content)
            if os.path.isfile('RAX$PLOT.html'):
                plot_file = open('RAX$PLOT.html', 'r')
                file_content = plot_file.read()
                plot_file.close()
                display_data_content = {
                    'data': {
                        'text/html' : file_content
                    },
                    'metadata': {}
                }
                self.logger.debug('Sending display data: {0}'.format(display_data_content))
                self.send_response(self.iopub_socket, 'display_data', display_data_content)
            if os.path.isfile('RAX$PLOT.svg'):
                plot_file = open('RAX$PLOT.svg', 'r')
                file_content = plot_file.read()
                plot_file.close()
                display_data_content = {
                    'data': {
                        'text/svg' : file_content
                    },
                    'metadata': {}
                }
                self.logger.debug('Sending display data: {0}'.format(display_data_content))
                self.send_response(self.iopub_socket, 'display_data', display_data_content)
#           self.send_response(self.iopub_socket, 'stream', stream_content)


    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        self.logger.debug('Starting do_execute')
        self.silent = silent
        # Handle empty requests (frontend might use them to query the execution_count)
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False
        error       = False
        try:
            code = code.strip()
            if not code.endswith(';'):
                code = code + ';'
            # Test for special %dburl line
            m = re.match(r"^%dburl\s+\"([^\"]+)\";$", code)
            if m:
                self.logger.debug("Found %dburl line")
                dburl = m.group(1)
                self.process_output("Restarting Rax with dburl: {0}".format(dburl))
                if self.rax_running:
                    self._stop_rax()
                self._start_rax(dburl=str(dburl))
            else:
                self.logger.debug("Found Rax code")
                if not self.rax_running:
                    self._start_rax()
                self.raxwrapper.sendline(code)
                self.raxwrapper.sendline('`print "RAX$DONE";')
                i = self.raxwrapper.expect(['RAX\$DONE'], timeout=None)
                self.process_output(self.raxwrapper.before)
        except KeyboardInterrupt:
            self.raxwrapper.sendintr()
            interrupted = True
            self.process_output(self.raxwrapper.before)
        except EOF:
            self.process_output(self.raxwrapper.before + 'Restarting Rax')
            self._start_rax()

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}
        if error:
            return {'status': 'error', 'execution_count': self.execution_count}
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

    # def do_complete(self, code, cursor_pos):
    #     code = code[:cursor_pos]
    #     default = {'matches': [], 'cursor_start': 0,
    #                'cursor_end': cursor_pos, 'metadata': dict(),
    #                'status': 'ok'}
    #
    #     if not code or code[-1] == ' ':
    #         return default
    #
    #     tokens = code.replace(';', ' ').split()
    #     if not tokens:
    #         return default
    #
    #     matches = []
    #     token = tokens[-1]
    #     start = cursor_pos - len(token)
    #
    #     if token[0] == '$':
    #         # complete variables
    #         cmd = 'compgen -A arrayvar -A export -A variable %s' % token[1:] # strip leading $
    #         output = self.bashwrapper.run_command(cmd).rstrip()
    #         completions = set(output.split())
    #         # append matches including leading $
    #         matches.extend(['$'+c for c in completions])
    #     else:
    #         # complete functions and builtins
    #         cmd = 'compgen -cdfa %s' % token
    #         output = self.bashwrapper.run_command(cmd).rstrip()
    #         matches.extend(output.split())
    #
    #     if not matches:
    #         return default
    #     matches = [m for m in matches if m.startswith(token)]
    #
    #     return {'matches': sorted(matches), 'cursor_start': start,
    #             'cursor_end': cursor_pos, 'metadata': dict(),
    #             'status': 'ok'}
