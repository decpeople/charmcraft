#!/usr/bin/env python3
# Copyright 2020 Ubuntu
# See LICENSE file for licensing details.

import logging
import os
import re
import subprocess
import time
import aiofiles
import textwrap
#Kazteleport
from jinja2 import Template
from ops.charm import CharmBase, ActionEvent, InstallEvent, StartEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus

logger = logging.getLogger(__name__)


class RabbitMQ(CharmBase):
    _stored = StoredState()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.start, self._start)
        self.framework.observe(self.on.update_status, self._on_update_status)
        self.framework.observe(self.on.stop_the_service_action, self._on_stop_the_service_action)
        self.framework.observe(self.on.start_the_service_action, self._on_start_the_service_action)
        self.framework.observe(self.on.restart_the_service_action, self._on_restart_the_service_action)
        self.framework.observe(self.on.config_changed_action, self._on_config_changed_action)
        self.framework.observe(self.on.get_conf_action, self._on_get_conf_action)
        self._stored.set_default(config={"publishes": {}})


    def _on_update_status(self, _):
        try:
            subprocess.check_call(["service", "rabbitmq-server", "status"])
            self.model.unit.status = ActiveStatus("RabbitMQ is running")
            self.model.unit.set_workload_version('Last')
        except subprocess.CalledProcessError:
            self.model.unit.status = BlockedStatus("RabbitMQ is not running")
            self.model.unit.set_workload_version('Last')


    def _on_install(self, _):
        subprocess.check_output(["apt", "install", "-y", "rabbitmq-server"])


    def _start(self, event):
        try:
            subprocess.check_call(["service", "rabbitmq-server", "status"])
            self.model.unit.status = ActiveStatus("RabbitMQ is running")
            self.model.unit.set_workload_version('Last')
        except subprocess.CalledProcessError as e:
            logger.debug("Starting systemd unit failed with return code %d", e.returncode)
            self.model.unit.status = BlockedStatus("Failed to start/enable ssh service")
            return
        self.model.unit.status = ActiveStatus("RabbitMQ is running")
    

    def _on_stop_the_service_action(self, event):
        try:
            subprocess.run(["service", "rabbitmq-server", "stop"], capture_output=True, check=True)
            output = {"RabbitMQ":"CHANGED"}
            self.model.unit.status = BlockedStatus("RabbitMQ stoped")
            self.model.unit.set_workload_version('Last')
            event.set_results(output)
        except subprocess.CalledProcessError as e:
            logger.debug(e.returncode)
            return e.returncode


    def _on_start_the_service_action(self, event):
        try:
            subprocess.run(["service", "rabbitmq-server", "start"], capture_output=True, check=True)
            output = {"RabbitMQ":"CHANGED"}
            self.model.unit.status = ActiveStatus("RabbitMQ is running")
            self.model.unit.set_workload_version('Last')
            event.set_results(output)
        except subprocess.CalledProcessError as e:
            logger.debug(e.returncode)
            return e.returncode
    

    def _on_restart_the_service_action(self, event):
        try:
            subprocess.run(["service", "rabbitmq-server", "restart"], capture_output=True, check=True)
            output = {"RabbitMQ":"restart"}
            self.model.unit.status = ActiveStatus("RabbitMQ is running")
            self.model.unit.set_workload_version('Last')
            event.set_results(output)
        except subprocess.CalledProcessError as e:
            logger.debug(e.returncode)
            return e.returncode
        
    
    def _on_config_changed_action(self, event):
        try:
            string = textwrap.dedent(text=event.params['main_data'])
            with open('/etc/rabbitmq/rabbitmq-env.conf', 'w') as fout:
                fout.write(string)
                fout.close()
            with open("/etc/rabbitmq/rabbitmq-env.conf", "r") as f:
                data = f.read()
                f.close()
            event.set_results({"config-changed":data})
        except Exception as e:
            self.model.unit.status = BlockedStatus(f"Error during config change:{e}")


    def _on_get_conf_action(self, event):
        try:
            with open("/etc/rabbitmq/rabbitmq-env.conf", "r") as f:
                data = f.read()
                f.close()
            print(data)
            event.set_results({"config":data})
        except Exception as e:
            self.model.unit.status = BlockedStatus(f"Error during config change:{e}")
            self.model.unit.set_workload_version('Last')

 

if __name__ == "__main__":
    main(RabbitMQ)