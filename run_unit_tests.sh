#!/bin/bash
unset DB_HOST
unset DB_PORT
unset DB_NAME
unset DB_USER
unset DB_SCHEMA
unset DB_PASSWORD
unset JWT_SECRET
unset JWT_ALGORITHM
unset JWT_EXPIRATION_MINUTES
unset JWT_REFRESH_EXPIRATION_DAYS
unset TESTING

export PYTHONPATH=$PWD
export TESTING=true

echo '                                                                                                    '
echo '                                                                                                    '
echo '    /$$   /$$ /$$   /$$ /$$$$$$ /$$$$$$$$       /$$$$$$$$ /$$$$$$$$  /$$$$$$  /$$$$$$$$ /$$$$$$     '
echo '   | $$  | $$| $$$ | $$|_  $$_/|__  $$__/      |__  $$__/| $$_____/ /$$__  $$|__  $$__//$$__  $$    '
echo '   | $$  | $$| $$$$| $$  | $$     | $$            | $$   | $$      | $$  \__/   | $$  | $$  \__/    '
echo '   | $$  | $$| $$ $$ $$  | $$     | $$            | $$   | $$$$$   |  $$$$$$    | $$  |  $$$$$$     '
echo '   | $$  | $$| $$  $$$$  | $$     | $$            | $$   | $$__/    \____  $$   | $$   \____  $$    '
echo '   | $$  | $$| $$\  $$$  | $$     | $$            | $$   | $$       /$$  \ $$   | $$   /$$  \ $$    '
echo '   |  $$$$$$/| $$ \  $$ /$$$$$$   | $$            | $$   | $$$$$$$$|  $$$$$$/   | $$  |  $$$$$$/    '
echo '    \______/ |__/  \__/|______/   |__/            |__/   |________/ \______/    |__/   \______/     '
echo '                                                                                                    '
echo '                                                                                                    '
echo '                                                                                                    '                                                                                          
                                                                                             

poetry run pytest -m unit --tb=short 