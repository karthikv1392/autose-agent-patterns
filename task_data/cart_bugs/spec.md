Bug report: "Totals are off by a cent on some orders, tax comes back as a float, removing an item sometimes leaves duplicates behind, and two shopping carts seem to share their items!"

Fix the project so that every test in `test_suite.py` passes. Do not edit the tests. Money is always integer cents. Discounts and tax are rounded **half-up** to the nearest cent, and percentages must be between 0 and 100 inclusive (otherwise raise `ValueError`).
