#!/usr/bin/env bash


python bot.py & gunicorn bet.wsgi && kill $!
