#!/bin/bash
subnet="192.168.252.0/24"
nmap -p 1234 --open -oG - $subnet | awk '/Up$/{print $2}'