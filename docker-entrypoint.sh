#!/bin/sh

# Start cron
crond -l 2 -f | tee -a /var/log/cron.log
