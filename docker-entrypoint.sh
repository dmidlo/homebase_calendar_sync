#!/bin/sh

# Start cron
cd /app
crond -l 2 -f | tee -a /var/log/cron.log
