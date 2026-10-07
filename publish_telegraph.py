#!/usr/bin/env python3
"""Kept for compatibility with the scheduled shift.

This entry point now publishes every article to ALL captcha-free destinations
(telegra.ph + rentry.co) via publish_all.py, so a single command keeps every
mirror in sync. State lives in /home/ubuntu/.megsy_publish_state.json.
"""
import os, runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "publish_all.py"),
               run_name="__main__")
