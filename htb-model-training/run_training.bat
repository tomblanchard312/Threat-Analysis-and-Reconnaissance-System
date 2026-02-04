@echo off
REM HTB Pentest Model v4 Training Script
REM Scheduled to run at midnight CST

echo ============================================================
echo HTB Pentest Model v4 - Unsloth Training
echo Started: %date% %time%
echo ============================================================

cd /d "f:\Repos\Pen-Testing-AI-Assistant\htb-model-training\configs"

REM Activate conda/venv if needed (uncomment and modify as needed)
REM call conda activate unsloth

REM Log start time
echo Training started at %date% %time% >> training_log.txt

REM Run training
python unsloth_config.py 2>&1 | tee training_output.log

REM Log completion
echo Training completed at %date% %time% >> training_log.txt

echo ============================================================
echo Training Complete!
echo Check training_output.log for details
echo ============================================================

pause
