# Proposed changes to shared code (none applied)
None are needed for the Mac build to work (assemble_mac.py wraps assemble_app.py without editing it). Optional wording only, for later:
- `app/src/station/launcher.py`: messages say "black window" and "Edge"; on a Mac they appear in Terminal and the default browser. A Mac test will show whether this matters.
- If Mac testing shows stray `.DS_Store` files breaking a library check or a refresh file, `station/refresh.py` and `setup_mac.py` should skip names starting with `.`/`._` (they do not mention them today).
