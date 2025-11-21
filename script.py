#!/usr/bin/env python3
"""
MQTT Client Logger Service
Connects to a Mosquitto broker, subscribes to iot/+/status topic,
and logs all received messages.
"""

import paho.mqtt.client as mqtt
import logging
import signal
import sys
import configparser
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Global variable for graceful shutdown
running = True

# Configuration defaults
CONFIG_FILE = 'config.ini'
DEFAULT_BROKER = 'localhost'
DEFAULT_PORT = 1883
DEFAULT_TOPIC = 'iot/+/status'
DEFAULT_LOG_DIR = '/var/log/mqtt-logger'
DEFAULT_LOG_FILE = 'mqtt-messages.log'
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_CLIENT_ID = 'mqtt-logger-service'


def load_config():
    """Load configuration from config.ini file"""
    config = configparser.ConfigParser()
    
    # Set defaults
    config['MQTT'] = {
        'broker': DEFAULT_BROKER,
        'port': str(DEFAULT_PORT),
        'topic': DEFAULT_TOPIC,
        'client_id': DEFAULT_CLIENT_ID,
        'username': '',
        'password': '',
        'keepalive': '60'
    }
    
    config['LOGGING'] = {
        'log_dir': DEFAULT_LOG_DIR,
        'log_file': DEFAULT_LOG_FILE,
        'log_level': DEFAULT_LOG_LEVEL,
        'max_bytes': '10485760',  # 10MB
        'backup_count': '5'
    }
    
    # Try to read config file
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    
    return config


def setup_logging(config):
    """Setup logging with rotation"""
    log_dir = config.get('LOGGING', 'log_dir')
    log_file = config.get('LOGGING', 'log_file')
    log_level = config.get('LOGGING', 'log_level')
    max_bytes = config.getint('LOGGING', 'max_bytes')
    backup_count = config.getint('LOGGING', 'backup_count')
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    log_path = os.path.join(log_dir, log_file)
    
    # Setup rotating file handler
    handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    
    # Setup console handler as well
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Setup formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(handler)
    logger.addHandler(console_handler)
    
    return logger


def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        logging.info(f"Connected to MQTT broker successfully")
        topic = userdata['topic']
        client.subscribe(topic)
        logging.info(f"Subscribed to topic: {topic}")
    else:
        logging.error(f"Connection failed with code {rc}")


def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    if rc != 0:
        logging.warning(f"Unexpected disconnection (code {rc}). Will attempt to reconnect.")
    else:
        logging.info("Disconnected from MQTT broker")


def on_message(client, userdata, msg):
    """Callback when a message is received"""
    try:
        payload = msg.payload.decode('utf-8')
        logging.info(f"Topic: {msg.topic} | QoS: {msg.qos} | Message: {payload}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


def on_subscribe(client, userdata, mid, granted_qos):
    """Callback when subscription is confirmed"""
    logging.info(f"Subscription confirmed with QoS: {granted_qos}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logging.info(f"Received signal {signum}. Shutting down gracefully...")
    running = False


def main():
    """Main function"""
    global running
    
    # Load configuration
    config = load_config()
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("Starting MQTT Logger Service")
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get MQTT configuration
    broker = config.get('MQTT', 'broker')
    port = config.getint('MQTT', 'port')
    topic = config.get('MQTT', 'topic')
    client_id = config.get('MQTT', 'client_id')
    username = config.get('MQTT', 'username')
    password = config.get('MQTT', 'password')
    keepalive = config.getint('MQTT', 'keepalive')
    
    # Create MQTT client
    client = mqtt.Client(client_id=client_id, userdata={'topic': topic})
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    
    # Set username and password if provided
    if username and password:
        client.username_pw_set(username, password)
        logger.info(f"Using authentication for user: {username}")
    
    # Connect to broker
    try:
        logger.info(f"Connecting to broker {broker}:{port}")
        client.connect(broker, port, keepalive)
    except Exception as e:
        logger.error(f"Failed to connect to broker: {e}")
        sys.exit(1)
    
    # Start network loop in background
    client.loop_start()
    
    # Keep running until signal received
    try:
        while running:
            signal.pause()
    except AttributeError:
        # signal.pause() not available on Windows
        import time
        while running:
            time.sleep(1)
    
    # Cleanup
    logger.info("Stopping MQTT client...")
    client.loop_stop()
    client.disconnect()
    logger.info("MQTT Logger Service stopped")


if __name__ == "__main__":
    main()
