DOUGBOT V2 WINDOWS COMPATIBILITY FIX

What this fixes:
1. Transformers 5.x / tokenizers 0.23.x were installed because the original requirements were too broad.
2. Qwen2.5-0.5B-Instruct in this bundle was trained/tested with Transformers 4.57.1 + tokenizers 0.22.1.
3. Windows launchers now switch to the Dougbot folder automatically, so relative paths are stable.
4. Includes the earlier model-path resolution fix.

Install:
- Extract this ZIP directly over your existing dougbot-v2 folder and allow file replacement.
- In the SAME PowerShell window you plan to use, run:
    .\repair_dependencies_windows.ps1
- Then re-enter the password (the old one only lived in the PowerShell process/session):
    .\auth_session_windows.ps1
- Test:
    .\delve_status_windows.ps1
- Run:
    .\delve_watch_windows.ps1

You do NOT need to re-download Qwen or retrain the LoRA.
