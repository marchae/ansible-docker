from __future__ import (absolute_import, division, print_function)

import docker
import hashlib
import os
import requests
import socket

from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor

class DockerDriver(object):
    """ Provide snapshot feature through 'docker commit'. """

    def __init__(self, author='ansible'):
        self._author = author
        try:
            err = self._connect()
        except (requests.exceptions.ConnectionError, docker.errors.APIError), error:
            # deactivate the plugin on error
            self.disabled = True
            ansible.utils.warning('Failed to contact docker daemon: {}'.format(error))
            return

    def _connect(self):
        # use the same environment variable as other docker plugins
        docker_host = os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock')
        # default version is current stable docker release (10/07/2015)
        # if provided, DOCKER_VERSION should match docker server api version
        docker_server_version = os.getenv('DOCKER_VERSION', '1.19')
        self._client = docker.Client(base_url=docker_host,
                version=docker_server_version, timeout=120)
        return self._client.ping()

    def target_container(self, host):
        """ Retrieve data on the container you want to provision. """
        def _match_container(metadatas):
            return metadatas['Names'][0] == '/' + host
        matchs = filter(_match_container, self._client.containers())
        return matchs[0] if len(matchs) == 1 else None

    def snapshot(self, host, task):
        tag = hashlib.md5(repr(task)).hexdigest()
        container = self.target_container(host)
        if container is None:
            return
        try:
            feedback = self._client.commit(container=container['Id'],
                repository=host, tag=tag, author=self._author)
        except docker.errors.APIError, error:
            self.disabled = True
            ansible.utils.warning('Failed to commit container: {}'.format(error))


class CallbackModule(CallbackBase):
    """Emulate docker cache.
    Commit the current container for each task.
    This plugin makes use of the following environment variables:
    - DOCKER_HOST (optional): How to reach docker daemon.
    Default: unix://var/run/docker.sock
    - DOCKER_VERSION (optional): Docker daemon version.
    Default: 1.19
    - DOCKER_AUTHOR (optional): Used when committing image. Default: Ansible
    Requires:
    - docker-py >= v0.5.3
    Resources:
    - http://docker-py.readthedocs.org/en/latest/api/
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'docker'

    _current_task = None

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.controller = DockerDriver()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._current_task = task.get_name()

    def v2_runner_on_ok(self, result):
        if self._current_task is None:
            # No task performed yet, don't commit
            return
        if result.is_changed():
            try:
                self.controller.snapshot(result._host.name, self._current_task)
            except AttributeError:
                return
