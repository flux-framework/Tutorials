#!/bin/bash

flux mini submit -N1 sleep 30
flux mini submit -N1 sleep 30
flux mini submit -N1 sleep 30
flux mini submit -N1 sleep 30
flux queue drain

