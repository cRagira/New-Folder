#!/usr/bin/env bash


python teleg.py & gunicorn bet.wsgi && fg
