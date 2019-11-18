import datetime
import http.client
import io
import json
import mimetypes
import os
import random
import socket
import ssl

from base64 import b64encode
from typing import Union, Tuple, List, Dict


def make_boundary() -> str:
    """ Replacement for mimetools choose_boundary
    Desc:   Since mimetools is no longer available in Python 3 we implement a replacement function. This function
            implements the same functionality for backwards compatibility.
    Ref:    https://docs.python.org/2.7/library/mimetools.html?highlight=choose_boundary#mimetools.choose_boundary
    """
    rand = random.Random()
    rand.seed()
    try:
        hostipaddr = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        hostipaddr = '127.0.0.1'
    return '%s.%d.%d.%f.%d' % (hostipaddr,
                               os.getuid(),
                               os.getpid(),
                               datetime.datetime.utcnow().timestamp(),
                               rand.randint(0, 100))


class HCIBenchAPI(object):

    class MultiPartForm(object):
        """Accumulate the data to be used when posting a form."""

        CRLF = '\r\n'
        CRLF_B = b'\r\n'

        def __init__(self):
            self.form_fields: List = []
            self.files: List = []
            self.boundary: str = make_boundary()

        @property
        def boundary(self):
            return self.__boundary

        @boundary.setter
        def boundary(self, value):
            self.__boundary = value

        def get_content_type(self) -> str:
            """Returns the content type."""
            return 'multipart/form-data; boundary=%s' % self.boundary

        def add_field(self, name: str, value: str) -> None:
            """Add a simple field to the form data."""
            self.form_fields.append((name, value))

        def add_file(self, fieldname, filename, filehandle, mimetype=None) -> None:
            """Add a file to be uploaded."""
            body = filehandle.read()
            if mimetype is None:
                mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            self.files.append((fieldname, filename, mimetype, body))

        def get_binary(self):
            """Return a binary buffer containing the form data, including attached files."""
            buffer: bytes = self.__form_fields() + self.__get_files()
            buffer += b'' if buffer else self.CRLF_B
            buffer += ("--%s--%s" % (self.boundary, self.CRLF)).encode('utf-8')
            binary = io.BytesIO()
            binary.write(buffer)
            return binary

        def __form_fields(self) -> bytes:
            buffer: bytes = b''
            for name, value in self.form_fields:
                buffer += self.CRLF.join(['--' + self.boundary,
                                          'Content-Disposition: form-data; name="%s"' % name,
                                          '',
                                          value]).encode('utf-8') + self.CRLF_B
            return buffer

        def __get_files(self) -> bytes:
            buffer: bytes = b''
            for name, fname, content_type, body in self.files:
                buffer += self.CRLF.join(['--' + self.boundary,
                                          'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, fname),
                                          'Content-Type: %s' % content_type,
                                          '']).encode('utf-8') + self.CRLF_B
                buffer += body + self.CRLF_B
            return buffer

    VALIDATE_SUCCESS = "All the config has been validated, please go ahead to kick off testing"

    def __init__(self, ip: str, username: str, password: str, tool: str, port: int = 8443):

        self.url = "%s:%d" % (ip, port)
        self.credential: str = b64encode((username + ':' + password).encode('utf-8')).decode('ascii')
        self.api: str = '/VMtest/'
        self.tool: str = tool
        self.msg_queue: str = ''

        # noinspection PyProtectedMember
        self.context = ssl._create_unverified_context()

    def __connect(self, method: str, path: str, request_body=None, file=None, file_field=''):
        if request_body is None:
            request_body = {}

        form = self.MultiPartForm()
        if request_body != {}:
            for field, value in request_body.items():
                form.add_field(field, value)
        if file:
            form.add_file(file_field, file.name, file)

        try:
            form_buffer = form.get_binary().getvalue()
            body = form.get_binary().getvalue()
            ctype = form.get_content_type()
            headers = {'Content-Type': ctype,
                       'Authorization': 'Basic %s' % self.credential,
                       'Content-length': str(len(form_buffer))}
            conn = http.client.HTTPSConnection(self.url, context=self.context)
            conn.request(method, self.api + path, body, headers)
        except OSError:
            raise SystemExit(1)
        return conn.getresponse()

    @classmethod
    def __is_http_200(cls, data: dict) -> bool:
        """Checks to see whether an HTTP request was successful"""
        return data and isinstance(data, dict) and data['status'] == '200'

    @classmethod
    def get_param_filename(cls, test_parameters: dict):
        """Returns the filename for given test parameters"""
        return "%s-%svmdk-%sws-%s-%srdpct-%srandompct-%sthreads" % (test_parameters['tool'],
                                                                    test_parameters['diskNum'],
                                                                    test_parameters['workSet'],
                                                                    test_parameters['blockSize'],
                                                                    test_parameters['readPercent'],
                                                                    test_parameters['randomPercent'],
                                                                    test_parameters['threadNum'])

    def read_hcibench_config(self) -> Dict:
        """Load the hcibenchapi configuration, aka /opt/automation/conf/perf-conf.yaml"""
        return json.loads(self.__connect('POST', 'readconfigfile').read())

    def configure_hcibench(self, request_body) -> Tuple[str, Dict]:
        """Configure hcibenchapi test, aka /opt/automation/conf/perf-conf.yaml"""
        data = json.loads(self.__connect('POST', 'generatefile', request_body).read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    def get_param_files(self, tool_param: str = None) -> List:
        """Load parameter files of a given tool"""
        request_body = {"tool": tool_param} if tool_param else {"tool": self.tool}
        data = json.loads(self.__connect('POST', "getvdbenchparamFile", request_body).read())
        return data["data"]

    def generate_param_file(self, request_body) -> Tuple[str, dict]:
        """Configure workload parameter"""
        data = json.loads(self.__connect('POST', 'generateParam', request_body).read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    # Delete a workload parameter file by name
    def delete_param_file(self, filename: str, tool_param: str = None) -> Union[str, Tuple[str, dict]]:
        tool = tool_param if tool_param else tool_param
        data = json.loads(self.__connect('POST', "deleteFile?name=%s&tool=%s" % (filename, tool)).read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    # Upload a local vdbench zip to HCIBench /opt/output/vdbench-source
    def upload_vdbench_zip(self, vdbench_zip) -> Union[str, Tuple[str, dict]]:
        with open(vdbench_zip, 'rb') as file:
            data = json.loads(self.__connect('POST', 'uploadvdbench', {}, file, 'vdbenchfile').read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    # Upload a local workload parameter file to HCIBench /opt/automation/(vdbench/fio)-param-files
    def upload_param_file(self, param_file) -> Union[str, Tuple[str, dict]]:
        with open(param_file, 'rb') as file:
            data = json.loads(self.__connect('POST', 'uploadParamfile', {'tool': self.tool}, file, 'paramfile').read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    # Kick off prevalidation, return True if success
    def prevalidation(self) -> Tuple[bool, str]:
        data = json.loads(self.__connect('POST', 'validatefile').read())
        if data and self.VALIDATE_SUCCESS in data['data']:
            return True, data['data']
        else:
            return False, data['data']

    # Start HCIBench testing
    def start_testing(self) -> Tuple[str, dict]:
        data = json.loads(self.__connect('POST', 'runtest').read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    # Kill HCIBench testing
    def kill_testing(self) -> Tuple[str, dict]:
        data = json.loads(self.__connect('POST', 'killtest').read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    # Check whether HCIBench testing finished
    def is_test_finished(self) -> bool:
        return self.__is_http_200(json.loads(self.__connect('POST', 'istestfinish').read()))

    # Delete guest VMs
    def cleanup_vms(self) -> Tuple[str, Dict]:
        data = json.loads(self.__connect('POST', 'cleanupvms').read())
        if self.__is_http_200(data):
            return 'Success', data
        else:
            return 'Fail', data

    # Load HCIBench test status
    def read_test_status(self) -> str:
        data = json.loads(self.__connect('GET', 'readlog').read())
        if data and 'data' in data and data['data'] not in self.msg_queue:
            delta = data['data'].replace(self.msg_queue.replace('\n...\n', ''), '').replace('<br>', '\n')
            self.msg_queue += delta + '\n'
            return self.msg_queue

    @property
    def credential(self) -> str:
        return self.__credentials

    @credential.setter
    def credential(self, value: str):
        self.__credentials = value
