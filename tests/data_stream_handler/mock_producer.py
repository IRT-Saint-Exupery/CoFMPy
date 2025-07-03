# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
#    of conditions and the following disclaimer in the documentation and/or other
#    materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
import time
import threading
import subprocess
from pathlib import Path

import pandas as pd
from confluent_kafka import Producer

def try_start_kafka_docker(yml_path: str, command="up", options=None):
    try:
        yml_path = Path(yml_path).resolve()  # ensures absolute path

        if options is None:
            command_line = ["docker-compose", "-f", str(yml_path), command]
        else:
            command_line = ["docker-compose", "-f", str(yml_path), command, options]

        result = subprocess.run(
            command_line,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Docker Compose Output:", result)
        return True

    except:
        print("❌ Unknown Docker Compose Error")
        return False


class MockProducerThreaded:
    def __init__(
            self,
            df,
            topic,
            uri="localhost:9092",
            prev_delay=5,
            max_retries=500,
            end_thread=True,
            create_delay=0.1,
            send_delay=0.1,
            retry_delay=0.1
        ):
        """
        Init: load configuration.
        """
        self.data = df
        self.topic = topic
        self.thread = None
        self.producer = None
        self._stop_event = threading.Event()
        self.conf = {"bootstrap.servers": uri, "retries": 1}

        self.prev_delay = prev_delay
        self.max_retries = max_retries
        self.end_thread = end_thread
        self.create_delay = create_delay
        self.send_delay = send_delay
        self.retry_delay = retry_delay

    def _create_producer(self, post_delay=0.5):
        self.producer = Producer(self.conf)
        print(f"✅ Producer created: {self.producer}")
        time.sleep(post_delay)

    def _delivery_report(self, err, msg):
        if err is not None:
            print(f"❌ Delivery failed: {err}")
        else:
            print(
                f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
            )

    def _send_df_data(self, send_delay=0.1):

        for _, row in self.data.iterrows():
            if self._stop_event.is_set():
                break

            message = str(row.to_dict())
            self.producer.produce(
                self.topic,
                value=message.encode("utf-8"),
                callback=self._delivery_report,
            )
            self.producer.poll(0)  # trigger delivery callbacks
            time.sleep(send_delay)

        self.producer.flush()

    def run(self):
        """Main thread routine.

        Args:
            prev_delay (float): delay previous to start routine.
        """
        time.sleep(self.prev_delay)

        tried = 0

        while tried < self.max_retries:

            tried += 1

            if self.producer == None:
                try:
                    self._create_producer()
                except:
                    time.sleep(self.create_delay)

            else:
                try:
                    self._send_df_data(self.send_delay)

                    if self.end_thread:
                        self.stop()
                        print("✅ Producer thread completed")

                    break

                except Exception as e:
                    print(f"❌ Error while sending: {e}")
                    time.sleep(self.retry_delay)

    def start(self):
        """
        Starts the producer in a background thread.
        """
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def stop(self):
        """
        Signals the thread to stop.
        """
        self._stop_event.set()

    def join(self):
        """
        Waits for the thread to finish.
        """
        if self.thread is not None:
            self.thread.join()
