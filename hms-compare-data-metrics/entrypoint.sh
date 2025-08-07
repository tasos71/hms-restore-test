#!/bin/bash

echo "🔍 Running pytest with Allure..."

pytest --alluredir=allure-results
PYTEST_EXIT_CODE=$?

if [ $PYTEST_EXIT_CODE -ne 0 ]; then
  echo "❌ Some tests failed (exit code $PYTEST_EXIT_CODE)"
else
  echo "✅ All tests passed"
fi

echo "📤 Sending Allure results to Allure Docker Service..."

# Required: set ALLURE_ENDPOINT and PROJECT_ID as env vars
#if [[ -z "$ALLURE_ENDPOINT" || -z "$PROJECT_ID" ]]; then
#  echo "❌ Environment variables ALLURE_ENDPOINT and PROJECT_ID must be set"
#  exit 1
#fi

/app/send_results.sh

echo "✅ Allure results sent."

if [ $PYTEST_EXIT_CODE -ne 0 ]; then
  echo "❌ Some tests failed (exit code $PYTEST_EXIT_CODE)"
else
  echo "✅ All tests passed"
fi

# Final exit: propagate test result to container exit
exit $PYTEST_EXIT_CODE