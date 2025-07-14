#!/bin/bash
cd /tmp/kavia/workspace/code-generation/browser-tic-tac-toe-443703d3/backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

