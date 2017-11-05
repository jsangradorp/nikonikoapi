#!/usr/bin/env bash
echo This script will destroy and create the nikoniko user and database.
echo This will ERASE ALL YOUR DATA.
echo Edit and run it if you are sure you want to do that.
exit
cat << EOF | psql postgres
drop database if exists nikoniko;
drop user if exists nikoniko;
create user nikoniko with login createdb password 'awesomepassword';
create database nikoniko with owner = nikoniko;
EOF

